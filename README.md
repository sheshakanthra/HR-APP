# PeopleDesk

An internal HRMS for a ~200-person SaaS company whose defining feature is a
**genuinely agentic, RAG-grounded AI assistant** (tool-calling, self-scoped,
human-in-the-loop) — not a bolt-on chatbot.

> Build status: **Milestone 1 complete** (scaffold + secrets + DB). Auth, modules,
> and the agent land in subsequent milestones (see [Build order](#build-order)).

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

- API: http://localhost:8000  (health: `/health`, docs: `/docs`)
- Web: http://localhost:5173
- Postgres: `localhost:5432`

The API container waits for Postgres, runs `alembic upgrade head`, optionally
seeds (`SEED_ON_START=true`), then serves. **Missing/placeholder `GROQ_API_KEY`
fails fast at startup** with a clear message.

### Seeding manually

```bash
docker compose run --rm api python -m app.seed
# reset + reseed:
docker compose run --rm -e PEOPLEDESK_SEED_FORCE=true api python -m app.seed
```

Seed produces ~200 employees across 10 departments with a manager hierarchy,
3 leave types + balances, user logins, and 8 sample policy docs.

- All demo employees share the password **`Passw0rd!`**.
- Super admin: `admin@peopledesk.io` / value of `SEED_ADMIN_PASSWORD`.

## Secrets hygiene

- `.env` is git-ignored; only `.env.example` (placeholders) is committed.
- `GROQ_API_KEY` is never hardcoded or logged; startup fails fast if unset.
- Groq serves **generation only** — there is no Groq embeddings endpoint; embeddings run locally.

## Scope

**v1 (building):** Employee Directory + Org Chart · Leave/PTO · Policy KB · AI Agent.
**Phase 2 (stubs):** Performance reviews · read-only HR analytics.
**Phase 3 (not built):** engagement surveys · onboarding workflows · document e-sign.

### Explicitly out of scope — legal/compliance risk (by design)

- **AI-driven hiring / resume screening / candidate ranking** — disparate-impact
  and regulatory risk (NYC Local Law 144, EU AI Act "high-risk"). Human decisions only.
- **AI termination / performance-based firing recommendations** — the agent never produces these.
- **The agent approving/denying any leave** — approvals are human-only.

These require legal review + human-in-the-loop; the app is built so a human always
holds these decisions.

## Architecture

```
React SPA ──JWT──> FastAPI
                     ├── auth (JWT, RBAC dependency)
                     ├── modules: directory / leave / policy
                     ├── agent service ─► Groq SDK (generation + tool-calling loop)
                     │      └── RAG: fastembed (local) ─► pgvector similarity search
                     ├── integrations/ (MOCKED: sso, slack, payroll, calendar)
                     └── audit + rbac in a dependency layer
                   PostgreSQL (+ pgvector)  — one DB
```

External integrations (SSO, Slack, payroll, calendar) are **mocked** behind a clean
interface in `api/app/integrations/` so the app runs fully locally with no vendor
accounts. Each mock is labeled in code; swap in a real provider without touching call sites.

## Repo layout

```
api/                 FastAPI backend
  app/
    models/          SQLAlchemy 2.0 models (+ pgvector)
    integrations/    mocked external providers
    core/            security (Argon2, JWT)
    scripts/         container helpers (wait_for_db)
    config.py        env-driven settings, fail-fast secret validation
    seed.py          demo data generator
  alembic/           migrations
web/                 React + Vite frontend (shell in M1; pages land in M3)
docker-compose.yml   postgres (+pgvector) · api · web
```

## Build order

1. ✅ Scaffold + secrets + DB (models, Alembic, seed, Docker Compose)
2. Auth + RBAC (JWT login/refresh, role-gated routes + tests)
3. Directory + Leave (endpoints + React pages, approval state machine)
4. Policy KB + RAG ingestion (publish → chunk → embed → pgvector)
5. AI Agent (Groq tool loop, 6 tools, guardrails, escalation, UI panel)
6. Audit + hardening + tests + full README

## Deployment note

Local dev uses Docker Compose. A later production option is a split deploy
(API on Render, web on Vercel, managed Postgres with pgvector) — not configured yet.
