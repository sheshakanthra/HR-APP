<div align="center">

# Sage

**Grounded HR intelligence for the modern workplace.**

*Every answer traced to a source. Every decision left to a human.*

![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/frontend-React%2018-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/postgres-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-Groq-F55036?style=for-the-badge)

![RAG-Grounded](https://img.shields.io/badge/RAG--grounded-no%20guessing-critical?style=for-the-badge)
![RBAC](https://img.shields.io/badge/RBAC-enforced-informational?style=for-the-badge)
![Human-in-the-loop](https://img.shields.io/badge/approvals-human--only-important?style=for-the-badge)
![License](https://img.shields.io/badge/license-Internal%20Use-lightgrey?style=for-the-badge)

</div>

---

Most HR chatbots retrieve an FAQ and hope for the best. **Sage retrieves a
versioned, permissioned source** — so every answer the agent gives is traceable,
and every answer it can't ground gets escalated to a person instead of guessed at.

```
Employee query → Agent selects tool → pgvector retrieval → RBAC-scoped response → Audit log
```

Sage is a full HRMS — directory, org chart, leave/PTO, policy knowledge base —
built around one core idea: an **agentic AI assistant** that is self-scoped,
tool-calling, and human-in-the-loop by design, not a chatbot bolted on top of
static documents.

---

## Overview

Traditional HR tools either lock employees out of self-service or bolt on a
chatbot that hallucinates policy answers. Sage takes a different approach:

- Every AI response is **grounded in retrieved, versioned policy documents** —
  no answer is generated without a verifiable source, and the agent escalates
  rather than guesses when it lacks grounding.
- The agent operates under the **same role-based access control as the rest of
  the platform**, so it can never see or return more than the requesting
  employee is authorized to access.
- High-stakes decisions — leave approvals, hiring, performance, and
  termination — remain **strictly human-owned**, by design and by code.
- Every conversation, tool invocation, and system write is captured in an
  **append-only audit log** for full traceability and compliance review.

The result is an internal tool that employees can trust, and that HR and
security teams can safely put in front of an entire company.

---

## Core Features

| Module | Description |
|---|---|
| **AI Agent** | Conversational assistant with six governed tools, RAG-grounded policy answers, and mandatory escalation paths for sensitive topics. |
| **Employee Directory & Org Chart** | Searchable company directory with role-appropriate contact and reporting-line visibility. |
| **Leave / PTO Management** | Full leave request lifecycle with a defined approval state machine; the agent can submit requests but never approves them. |
| **Policy Knowledge Base** | Versioned, publishable policy documents that are chunked and embedded for retrieval by the AI agent. |
| **Audit & Compliance** | Append-only logging of every write and every agent action, reviewable by HR admins. |

---

## Technology Stack

**Frontend**
- React 18 + TypeScript, built with Vite
- Tailwind CSS for styling
- React Router for navigation
- TanStack Query for server state management
- `lucide-react` icon set

**Backend**
- FastAPI (Python 3.11)
- Pydantic v2 for request/response validation
- SQLAlchemy 2.0 ORM with Alembic migrations

**Data & Retrieval**
- PostgreSQL 16 with the **pgvector** extension — application data and policy
  embeddings live in a single database
- `fastembed` (`BAAI/bge-small-en-v1.5`, 384-dim) for **local** embedding
  generation, decoupled from the LLM provider

**AI / LLM**
- Groq (`llama-3.3-70b-versatile`) for generation, via the official SDK
- A transparent, hand-rolled tool-dispatch loop — no third-party agent
  framework — for full control over guardrails and auditability

**Authentication & Security**
- JWT-based authentication (access + refresh tokens)
- Argon2 password hashing
- Role-based access control enforced at the API layer

**Infrastructure**
- Docker Compose for local orchestration (Postgres, API, web)
- Planned production path: API on Render, web on Vercel, managed
  Postgres with pgvector

---

## Getting Started

```bash
cp .env.example .env
# Set JWT_SECRET_KEY:
#   python -c "import secrets; print(secrets.token_urlsafe(64))"
# Set a valid GROQ_API_KEY from https://console.groq.com/keys
docker compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8000 (health `/health`, docs `/docs`) |
| Web | http://localhost:5173 |
| Postgres | `localhost:5432` |

On startup, the API waits for Postgres, applies migrations
(`alembic upgrade head`), and — when `SEED_ON_START=true` — seeds demo data
and indexes policy documents. A missing or placeholder `GROQ_API_KEY` causes
the API to **fail fast** with a clear error rather than start in a broken
state.

### Demo Credentials

| Account | Login |
|---|---|
| Any seeded employee | Their seeded email / `Passw0rd!` |
| Super admin | `admin@sage.io` / `SEED_ADMIN_PASSWORD` |

### Manual Seed & Indexing

```bash
docker compose run --rm api python -m app.seed
docker compose run --rm api python -m app.scripts.ingest_policies   # embed published policies
docker compose run --rm -e PEOPLEDESK_SEED_FORCE=true api python -m app.seed  # reset
```

### Running Tests

```bash
docker compose up -d postgres
docker compose run --rm api pytest
```

46 tests covering RBAC enforcement, the leave state machine, RAG retrieval,
and agent guardrails.

---

## The AI Agent

The agent is employee-facing, self-scoped to the requesting user, and answers
only from grounded sources. It runs on a hand-rolled Groq tool-dispatch loop
(`app/services/agent/`), giving full visibility and control over every tool
call rather than delegating orchestration to an external framework.

**Available tools**

| Tool | Purpose |
|---|---|
| `search_policy_docs` | pgvector RAG search over published policy; returns chunks with source title and version. Relevance-thresholded — an empty result triggers escalation, never a guess. |
| `get_leave_balance` | Returns the caller's own leave balance. |
| `get_my_leave_requests` | Returns the caller's own leave request history. |
| `submit_leave_request` | Creates a `PENDING` request routed to the employee's manager. Never auto-approves. |
| `get_employee_contact` | Returns name, title, department, work email, and manager — no sensitive fields. |
| `flag_for_human_review` / `escalate_to_hr` | Opens an HR ticket for issues requiring human judgment. |

**Guardrails (enforced in both code and prompt)**

- Queries are strictly self-scoped; the agent cannot access or disclose another
  employee's compensation, performance, or leave data.
- The agent never approves or denies leave, and never renders hiring, firing,
  or promotion judgments.
- Policy answers must be traceable to retrieved source chunks.
- Escalation is mandatory for harassment, grievances, mental health or crisis
  situations, compensation disputes, legal or compliance matters, termination,
  medical accommodation requests, ungrounded questions, or any explicit
  request to speak with a person.
- Every conversation turn and tool call is persisted to `agent_message` and
  `audit_log` for full auditability.

---

## Security & Compliance

- **Access control** — RBAC is enforced by a FastAPI dependency
  (`app/api/deps.py`) on every route, and re-checked server-side inside each
  agent tool. Role hierarchy: `employee < manager < hr_admin < super_admin`.
- **PII protection** — Argon2 password hashing; response models are
  structured to prevent leaking compensation fields; no PII appears in URLs
  or logs; audit metadata is minimized by design.
- **Audit logging** — An append-only `audit_log`, readable by `hr_admin` and
  above at `GET /admin/audit-log`. Every write and every agent tool
  invocation is recorded, including authentication events, leave lifecycle
  actions, policy CRUD/publish events, and agent tool calls.
- **Transport & rate limiting** — CORS is locked to `WEB_ORIGIN`; rate limits
  (via `slowapi`) are applied to `/auth/login` (10/min), `/auth/refresh`
  (30/min), and `/agent/chat` (20/min); JWTs use short expiry with refresh.
- **Secrets management** — `.env` is git-ignored; only `.env.example`
  (placeholder values) is committed; `GROQ_API_KEY` is never hardcoded or
  logged.

---

## Integrations (Mocked)

SSO, Slack, payroll, and calendar integrations are mocked behind clean
interfaces in `app/integrations/` (each explicitly labeled `MOCK` in code).
This allows the full application to run locally without any vendor accounts,
while keeping the interfaces swappable for real providers without touching
call sites elsewhere in the codebase.

---

## Project Scope

**v1 — Built**
Employee Directory & Org Chart · Leave/PTO Management · Policy Knowledge Base
· AI Agent

**Phase 2 — Scaffolded / Next**
Performance reviews · Read-only aggregate HR analytics

**Phase 3 — Not Yet Built**
Engagement surveys · Onboarding workflows · Document e-signature

### Explicitly Out of Scope (by design)

These capabilities are intentionally excluded due to legal and compliance
risk, and require human judgment in every case:

- **AI-driven hiring, resume screening, or candidate ranking** — disparate-impact
  and regulatory exposure (e.g., NYC Local Law 144, EU AI Act "high-risk"
  classification); hiring decisions remain human-only.
- **AI-generated termination or performance-based firing recommendations** —
  the agent is architecturally incapable of producing these.
- **AI approval or denial of leave requests** — approvals are always a human
  action.

---

## Architecture

```
React SPA ──JWT──> FastAPI
                     ├── auth (JWT, RBAC dependency, rate limiting)
                     ├── modules: directory / leave / policy
                     ├── agent service ─► Groq SDK (generation + tool loop)
                     │      └── RAG: fastembed (local) ─► pgvector search
                     ├── integrations/ (MOCKED: sso, slack, payroll, calendar)
                     └── audit + RBAC in a shared dependency layer
                   PostgreSQL (+ pgvector) — single database
```

## Repository Layout

```
api/                 FastAPI backend
  app/
    api/routes/      auth, admin, directory, leave, policy, agent
    api/deps.py      auth + RBAC dependency layer
    core/            security (Argon2/JWT), audit, rate limiting
    models/          SQLAlchemy 2.0 models (+ pgvector)
    services/        leave state machine, policy RAG, agent (tools + loop)
    integrations/    mocked external providers
    seed.py          demo data generator
  alembic/           migrations
  tests/             pytest suite (RBAC, leave, directory, policy, agent)
web/                 React + Vite frontend
docker-compose.yml   postgres (+pgvector) · api · web
```

## Deployment Notes

Local development runs entirely on Docker Compose. A production deployment
path — API on Render, web on Vercel, and a managed Postgres instance with
pgvector — is planned but not yet configured.
