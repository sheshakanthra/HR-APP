# Sage

*The HR assistant that knows what it doesn't know.*

An internal HRMS for a ~200-person SaaS company whose defining feature is a
**genuinely agentic, RAG-grounded AI assistant** (tool-calling, self-scoped,
human-in-the-loop) — not a bolt-on chatbot.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind, React Router, TanStack Query, `lucide-react` |
| Backend | FastAPI (Python 3.11), Pydantic v2, SQLAlchemy 2.0, Alembic |
| DB | PostgreSQL 16 + **pgvector** (app tables *and* policy embeddings in one DB) |
| Auth | JWT (access + refresh), Argon2 password hashing |
| LLM | **Groq only** for generation (`llama-3.3-70b-versatile`) via the official SDK |
| Embeddings | **Local** via `fastembed` (`BAAI/bge-small-en-v1.5`, 384-dim) — *not* Groq |

## Quick start

```bash
cp .env.example .env
# Fill in JWT_SECRET_KEY (python -c "import secrets; print(secrets.token_urlsafe(64))")
# and a real GROQ_API_KEY from https://console.groq.com/keys
docker compose up --build
```

- API: http://localhost:8000  (health `/health`, docs `/docs`)
- Web: http://localhost:5173
- Postgres: `localhost:5432`

On boot the API waits for Postgres, runs `alembic upgrade head`, and (when
`SEED_ON_START=true`) seeds + indexes policies. **Missing/placeholder
`GROQ_API_KEY` fails fast** at startup with a clear message.

### Logins (after seed)

- All demo employees: their seeded email / **`Passw0rd!`**
- Super admin: `admin@sage.io` / `SEED_ADMIN_PASSWORD`

### Manual seed / index

```bash
docker compose run --rm api python -m app.seed
docker compose run --rm api python -m app.scripts.ingest_policies   # embed published policies
docker compose run --rm -e PEOPLEDESK_SEED_FORCE=true api python -m app.seed  # reset
```

### Tests

```bash
docker compose up -d postgres
docker compose run --rm api pytest          # 46 tests: RBAC, leave state machine, RAG, agent guardrails
```

## The AI agent

Employee-facing, self-scoped, grounded. A transparent hand-rolled Groq
tool-dispatch loop (`app/services/agent/`) — no agent framework. Six tools, each
a real Python function with Pydantic-validated args executed under the caller's
RBAC:

- `search_policy_docs` — pgvector RAG over published policy; returns chunks with
  source **title + version** (relevance-thresholded; empty ⇒ escalate, never guess).
- `get_leave_balance` / `get_my_leave_requests` — caller's own data only.
- `submit_leave_request` — creates a **PENDING** request routed to the manager;
  **never approves**.
- `get_employee_contact` — name/title/department/work email/manager only.
- `flag_for_human_review` / `escalate_to_hr` — opens an HR ticket.

**Guardrails (code + prompt):** self-scoped queries only; never exposes another
person's comp/performance/leave; never approves/denies leave; never makes
hiring/firing/promotion judgments; policy answers cited from retrieved chunks;
mandatory escalation for harassment, grievances, mental-health/crisis, comp
disputes, legal/compliance, termination, medical accommodation, ungrounded
questions, or any "talk to a person." Every conversation and tool call is
persisted (`agent_message` + `audit_log`).

## Security & compliance

- **RBAC** enforced by a FastAPI dependency (`app/api/deps.py`) on every route;
  the agent's tools re-check it server-side. Roles: `employee < manager <
  hr_admin < super_admin`.
- **PII:** Argon2 password hashing; Pydantic response models can't leak comp
  fields; no PII in URLs or logs; audit metadata is PII-minimized.
- **Audit log:** append-only (`audit_log`), hr_admin+-readable at
  `GET /admin/audit-log`. Every write and every agent tool call is recorded
  (auth login; leave submit/approve/reject/cancel; policy CRUD/publish; agent tools).
- **Transport/config:** CORS locked to `WEB_ORIGIN`; rate limits (slowapi) on
  `/auth/login` (10/min), `/auth/refresh` (30/min), `/agent/chat` (20/min);
  JWT expiry + refresh.
- **Secrets:** `.env` git-ignored; only `.env.example` (placeholders) committed;
  `GROQ_API_KEY` never hardcoded or logged.

## Integrations (mocked)

SSO, Slack, payroll, and calendar are **mocked** behind clean interfaces in
`app/integrations/` (each labeled MOCK in code) so the app runs fully locally
with no vendor accounts; swap in a real provider without touching call sites.

## Scope

**v1 (built):** Employee Directory + Org Chart · Leave/PTO · Policy KB · AI Agent.
**Phase 2 (scaffolded/next):** performance reviews · read-only aggregate HR analytics.
**Phase 3 (not built):** engagement surveys · onboarding workflows · document e-sign.

### Explicitly out of scope — legal/compliance risk (by design)

- **AI-driven hiring / resume screening / candidate ranking** — disparate-impact
  and regulatory risk (NYC Local Law 144, EU AI Act "high-risk"); human decisions only.
- **AI termination / performance-based firing recommendations** — the agent never produces these.
- **The agent approving/denying leave** — approvals are human-only.

These require legal review + human-in-the-loop; the app is built so a human always
holds these decisions.

## Architecture

```
React SPA ──JWT──> FastAPI
                     ├── auth (JWT, RBAC dependency, rate limits)
                     ├── modules: directory / leave / policy
                     ├── agent service ─► Groq SDK (generation + tool loop)
                     │      └── RAG: fastembed (local) ─► pgvector search
                     ├── integrations/ (MOCKED: sso, slack, payroll, calendar)
                     └── audit + rbac in a dependency layer
                   PostgreSQL (+ pgvector)  — one DB
```

## Repo layout

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
  tests/             pytest (RBAC, leave, directory, policy, agent)
web/                 React + Vite frontend
docker-compose.yml   postgres (+pgvector) · api · web
```

## Deployment note

Local dev uses Docker Compose. A later production option is a split deploy
(API on Render, web on Vercel, managed Postgres with pgvector) — not configured yet.
