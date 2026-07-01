"""Agent guardrail tests. Tools are exercised directly (deterministic RBAC), and
the dispatch loop is driven by a scripted fake LLM client (no Groq calls)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models.agent import AgentConversation, HRTicket
from app.models.enums import LeaveStatus, RBACRole
from app.models.user import User
from app.services.agent.service import run_chat
from app.services.agent.tools import (
    ContactArgs,
    SearchArgs,
    SubmitLeaveArgs,
    ToolContext,
    _get_employee_contact,
    _search_policy_docs,
    _submit_leave_request,
    dispatch,
)


def _emp_user() -> User:
    db = SessionLocal()
    try:
        return db.scalar(select(User).where(User.rbac_role == RBACRole.employee).limit(1))
    finally:
        db.close()


# ---- scripted fake LLM ----

@dataclass
class FakeCall:
    id: str
    name: str
    arguments: str

    @property
    def function(self):
        return self


class FakeResponse:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class ScriptedClient:
    """Yields a queue of responses, one per create() call."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create(self, messages, tools):
        self.calls += 1
        return self._responses.pop(0)


# ---- tool-level guardrails (deterministic) ----

def test_contact_never_leaks_sensitive_fields():
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.rbac_role == RBACRole.employee).limit(1))
        ctx = ToolContext(db=db, user=user)
        target = db.scalar(select(User).where(User.rbac_role == RBACRole.manager).limit(1))
        res = _get_employee_contact(ctx, ContactArgs(name_or_email=target.email))
        assert res["contacts"], "should find the colleague"
        allowed = {"name", "title", "department", "work_email", "manager"}
        for c in res["contacts"]:
            assert set(c.keys()) == allowed  # no salary / leave / address fields
    finally:
        db.close()


def test_agent_submit_creates_pending_never_approved():
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.rbac_role == RBACRole.employee).limit(1))
        ctx = ToolContext(db=db, user=user)
        start = date.today() + timedelta(days=60)
        while start.weekday() >= 5:
            start += timedelta(days=1)
        res = _submit_leave_request(
            ctx,
            SubmitLeaveArgs(leave_type="Annual", start_date=start, end_date=start, reason="trip"),
        )
        assert res["status"] == "pending"  # the agent NEVER approves
        assert "human" in res["note"].lower()
        # cleanup
        from app.models.leave import LeaveRequest
        req = db.get(LeaveRequest, res["request_id"])
        assert req.status == LeaveStatus.pending
        assert req.created_via_agent is True
        db.delete(req)
        db.commit()
    finally:
        db.close()


def test_search_ungrounded_returns_no_guess():
    db = SessionLocal()
    try:
        user = _emp_user()
        ctx = ToolContext(db=db, user=user)
        res = _search_policy_docs(ctx, SearchArgs(query="zzxqy nonsense unrelated gibberish token"))
        assert res["grounded"] is False
        assert res["results"] == []
    finally:
        db.close()


# ---- loop-level: escalation persists a ticket ----

def test_escalation_creates_ticket_via_loop():
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.rbac_role == RBACRole.employee).limit(1))
        conv = AgentConversation(user_id=user.id, title="t")
        db.add(conv)
        db.flush()

        tickets_before = db.scalar(
            select(HRTicket).where(HRTicket.raised_by_user_id == user.id).limit(1)
        )

        client = ScriptedClient(
            [
                FakeResponse(
                    content="",
                    tool_calls=[
                        FakeCall(
                            "call_1",
                            "escalate_to_hr",
                            json.dumps({"category": "harassment", "summary": "reported harassment"}),
                        )
                    ],
                ),
                FakeResponse(
                    content="I'm sorry you're dealing with this. A human HR representative will follow up with you.",
                    tool_calls=None,
                ),
            ]
        )
        reply = run_chat(
            db,
            user=user,
            conversation=conv,
            user_text="A colleague is harassing me",
            client=client,
        )
        assert "human" in reply.content.lower()
        ticket = db.scalar(
            select(HRTicket)
            .where(HRTicket.raised_by_user_id == user.id, HRTicket.category == "harassment")
            .order_by(HRTicket.id.desc())
        )
        assert ticket is not None
        assert client.calls == 2
        db.delete(ticket)
        db.commit()
    finally:
        db.close()


# ---- loop-level: policy answer cites sources ----

def test_policy_answer_collects_sources():
    db = SessionLocal()
    try:
        user = _emp_user()
        conv = AgentConversation(user_id=user.id, title="t2")
        db.add(conv)
        db.flush()
        client = ScriptedClient(
            [
                FakeResponse(
                    content="",
                    tool_calls=[
                        FakeCall("c1", "search_policy_docs", json.dumps({"query": "maternity leave"}))
                    ],
                ),
                FakeResponse(content="Maternity leave is 16 weeks. (Source: ...)", tool_calls=None),
            ]
        )
        reply = run_chat(
            db, user=user, conversation=conv, user_text="maternity leave?", client=client
        )
        assert reply.sources, "grounded answer must attach sources"
        assert any("Maternity" in s["doc_title"] or "Parental" in s["doc_title"] for s in reply.sources)
    finally:
        db.close()


# ---- API: conversations are self-scoped ----

def test_conversation_access_is_self_scoped(client, auth_headers):
    # create a conversation as employee directly
    db = SessionLocal()
    try:
        emp = db.scalar(select(User).where(User.rbac_role == RBACRole.employee).limit(1))
        conv = AgentConversation(user_id=emp.id, title="private")
        db.add(conv)
        db.commit()
        conv_id = conv.id
    finally:
        db.close()
    # a DIFFERENT user (hr_admin) must not read it
    r = client.get(f"/agent/conversations/{conv_id}", headers=auth_headers["hr_admin"])
    assert r.status_code == 404
