"""Agent tools. Each is a real Python function with validated args, executed
under the caller's RBAC scope. RBAC is re-checked here server-side even if the
LLM "asks" for something out of scope. Determinism (leave math, submission) is
delegated to the leave service, never the LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from pydantic import BaseModel, ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.audit import record
from app.models.agent import HRTicket
from app.models.employee import Employee
from app.models.enums import LeaveStatus, TicketCategory
from app.models.leave import LeaveRequest, LeaveType
from app.models.user import User
from app.services import leave as leave_svc
from app.services import policy_rag


@dataclass
class ToolContext:
    db: Session
    user: User

    @property
    def employee(self) -> Employee | None:
        return self.user.employee


class ToolError(Exception):
    """Recoverable tool failure surfaced back to the model as a tool result."""


# ---- arg models ----

class SearchArgs(BaseModel):
    query: str


class LeaveRequestsArgs(BaseModel):
    status: str | None = None


class SubmitLeaveArgs(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: str = ""


class ContactArgs(BaseModel):
    name_or_email: str


class FlagArgs(BaseModel):
    reason: str


class EscalateArgs(BaseModel):
    category: str
    summary: str


# ---- tool implementations ----

def _search_policy_docs(ctx: ToolContext, a: SearchArgs) -> dict:
    results = policy_rag.search_policy_docs(ctx.db, a.query)
    if not results:
        return {
            "grounded": False,
            "results": [],
            "note": "No relevant published policy found. Offer to escalate to a human; do not guess.",
        }
    return {
        "grounded": True,
        "results": [
            {
                "doc_title": r["doc_title"],
                "doc_version": r["doc_version"],
                "text": r["chunk_text"],
            }
            for r in results
        ],
    }


def _get_leave_balance(ctx: ToolContext, _a: BaseModel) -> dict:
    emp = _require_employee(ctx)
    return {"balances": leave_svc.compute_balances(ctx.db, emp.id)}


def _get_my_leave_requests(ctx: ToolContext, a: LeaveRequestsArgs) -> dict:
    emp = _require_employee(ctx)
    stmt = select(LeaveRequest).where(LeaveRequest.employee_id == emp.id).order_by(
        LeaveRequest.created_at.desc()
    )
    if a.status:
        try:
            stmt = stmt.where(LeaveRequest.status == LeaveStatus(a.status.lower()))
        except ValueError:
            raise ToolError(f"Unknown status '{a.status}'")
    rows = ctx.db.scalars(stmt).all()
    return {
        "requests": [
            {
                "id": r.id,
                "type_id": r.leave_type_id,
                "start_date": r.start_date.isoformat(),
                "end_date": r.end_date.isoformat(),
                "days": float(r.days),
                "status": r.status.value,
            }
            for r in rows
        ]
    }


def _submit_leave_request(ctx: ToolContext, a: SubmitLeaveArgs) -> dict:
    emp = _require_employee(ctx)
    lt = ctx.db.scalar(
        select(LeaveType).where(
            or_(
                LeaveType.name.ilike(a.leave_type),
                LeaveType.code.ilike(a.leave_type),
                LeaveType.name.ilike(f"%{a.leave_type}%"),
            )
        )
    )
    if lt is None:
        types = [t.name for t in ctx.db.scalars(select(LeaveType))]
        raise ToolError(f"Unknown leave type '{a.leave_type}'. Available: {', '.join(types)}")
    try:
        req = leave_svc.submit_request(
            ctx.db,
            employee=emp,
            actor_user_id=ctx.user.id,
            leave_type_id=lt.id,
            start_date=a.start_date,
            end_date=a.end_date,
            reason=a.reason,
            via_agent=True,  # NEVER auto-approves; status is PENDING
        )
    except leave_svc.LeaveValidationError as exc:
        raise ToolError(str(exc))

    approver = ctx.db.get(Employee, req.approver_id) if req.approver_id else None
    return {
        "status": req.status.value,  # always "pending"
        "request_id": req.id,
        "leave_type": lt.name,
        "days": float(req.days),
        "start_date": req.start_date.isoformat(),
        "end_date": req.end_date.isoformat(),
        "approver": approver.full_name if approver else "HR (no direct manager)",
        "note": "Submitted for HUMAN approval. The agent cannot approve leave.",
    }


def _get_employee_contact(ctx: ToolContext, a: ContactArgs) -> dict:
    q = a.name_or_email.strip()
    like = f"%{q}%"
    rows = ctx.db.scalars(
        select(Employee)
        .where(
            or_(
                Employee.work_email.ilike(like),
                Employee.first_name.ilike(like),
                Employee.last_name.ilike(like),
                (Employee.first_name + " " + Employee.last_name).ilike(like),
            )
        )
        .limit(5)
    ).all()
    # Only ever expose contact-level fields. Never comp, home address, PII, or
    # another person's leave.
    contacts = []
    for e in rows:
        mgr = ctx.db.get(Employee, e.manager_id) if e.manager_id else None
        contacts.append(
            {
                "name": e.full_name,
                "title": e.title,
                "department": e.department.name if e.department else None,
                "work_email": e.work_email,
                "manager": mgr.full_name if mgr else None,
            }
        )
    return {"contacts": contacts}


def _flag_for_human_review(ctx: ToolContext, a: FlagArgs) -> dict:
    ticket = _make_ticket(ctx, TicketCategory.general.value, a.reason)
    return {
        "ticket_id": ticket.id,
        "note": "Flagged for a human HR representative, who will follow up.",
    }


def _escalate_to_hr(ctx: ToolContext, a: EscalateArgs) -> dict:
    try:
        category = TicketCategory(a.category.lower()).value
    except ValueError:
        category = TicketCategory.general.value
    ticket = _make_ticket(ctx, category, a.summary)
    return {
        "ticket_id": ticket.id,
        "category": category,
        "note": "Escalated to a human HR representative. They will follow up with you directly.",
    }


def _make_ticket(ctx: ToolContext, category: str, summary: str) -> HRTicket:
    ticket = HRTicket(raised_by_user_id=ctx.user.id, category=category, summary=summary)
    ctx.db.add(ticket)
    ctx.db.flush()
    return ticket


def _require_employee(ctx: ToolContext) -> Employee:
    if ctx.employee is None:
        raise ToolError("Your account is not linked to an employee profile.")
    return ctx.employee


# ---- registry ----

@dataclass
class Tool:
    name: str
    description: str
    args_model: type[BaseModel]
    fn: Callable[[ToolContext, Any], dict]
    parameters: dict
    # Which arg fields are safe to persist in the audit log (no free-text PII).
    audit_fields: tuple[str, ...] = ()


class _NoArgs(BaseModel):
    pass


TOOLS: dict[str, Tool] = {
    "search_policy_docs": Tool(
        "search_policy_docs",
        "Search published HR policy documents. Returns text chunks with source title and version. Use for ANY policy or entitlement question.",
        SearchArgs,
        _search_policy_docs,
        {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        audit_fields=("query",),
    ),
    "get_leave_balance": Tool(
        "get_leave_balance",
        "Get the CURRENT USER's own leave balances. Takes no arguments.",
        _NoArgs,
        _get_leave_balance,
        {"type": "object", "properties": {}},
    ),
    "get_my_leave_requests": Tool(
        "get_my_leave_requests",
        "Get the current user's own leave requests. Optional status filter (pending/approved/rejected/cancelled).",
        LeaveRequestsArgs,
        _get_my_leave_requests,
        {"type": "object", "properties": {"status": {"type": "string"}}},
        audit_fields=("status",),
    ),
    "submit_leave_request": Tool(
        "submit_leave_request",
        "Submit a leave request for the current user. Creates a PENDING request routed to their manager. NEVER approves it.",
        SubmitLeaveArgs,
        _submit_leave_request,
        {
            "type": "object",
            "properties": {
                "leave_type": {"type": "string", "description": "e.g. Annual, Sick, Casual"},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                "reason": {"type": "string"},
            },
            "required": ["leave_type", "start_date", "end_date"],
        },
        audit_fields=("leave_type", "start_date", "end_date"),
    ),
    "get_employee_contact": Tool(
        "get_employee_contact",
        "Look up a colleague's work contact info: name, title, department, work email, manager. Never returns compensation, home address, or leave data.",
        ContactArgs,
        _get_employee_contact,
        {
            "type": "object",
            "properties": {"name_or_email": {"type": "string"}},
            "required": ["name_or_email"],
        },
    ),
    "flag_for_human_review": Tool(
        "flag_for_human_review",
        "Flag the conversation for a human HR representative to review.",
        FlagArgs,
        _flag_for_human_review,
        {"type": "object", "properties": {"reason": {"type": "string"}}, "required": ["reason"]},
    ),
    "escalate_to_hr": Tool(
        "escalate_to_hr",
        "Escalate a sensitive matter to a human HR rep. Categories: harassment, grievance, mental_health, compensation, legal, termination, medical_accommodation, ungrounded, general.",
        EscalateArgs,
        _escalate_to_hr,
        {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "summary": {"type": "string"},
            },
            "required": ["category", "summary"],
        },
        audit_fields=("category",),
    ),
}


def groq_tool_schemas() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {"name": t.name, "description": t.description, "parameters": t.parameters},
        }
        for t in TOOLS.values()
    ]


def dispatch(ctx: ToolContext, name: str, raw_args: dict) -> tuple[dict, dict]:
    """Execute a tool. Returns (result, audit_metadata).

    Validates args (Pydantic), runs under RBAC, and records an audit entry with
    a PII-minimized argument set.
    """
    tool = TOOLS.get(name)
    if tool is None:
        return {"error": f"Unknown tool '{name}'"}, {"tool": name, "status": "unknown_tool"}

    try:
        args = tool.args_model(**(raw_args or {}))
    except ValidationError as exc:
        result = {"error": "invalid arguments", "detail": exc.errors()}
        _audit(ctx, tool, {}, "invalid_args")
        return result, {"tool": name, "status": "invalid_args"}

    safe_args = {f: getattr(args, f, None) for f in tool.audit_fields}
    try:
        result = tool.fn(ctx, args)
        status = "ok"
    except ToolError as exc:
        result = {"error": str(exc)}
        status = "tool_error"
    _audit(ctx, tool, safe_args, status)
    return result, {"tool": name, "args": _jsonable(safe_args), "status": status}


def _audit(ctx: ToolContext, tool: Tool, safe_args: dict, status: str) -> None:
    record(
        ctx.db,
        actor_user_id=ctx.user.id,
        action=f"agent.tool.{tool.name}",
        entity_type="agent_tool",
        metadata={"args": _jsonable(safe_args), "status": status},
        commit=False,
    )


def _jsonable(d: dict) -> dict:
    return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in d.items()}
