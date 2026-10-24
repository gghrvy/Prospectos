# CLAUDE.md: ProspectOS

Internal lead-generation tool for a two-person web dev + AI automation business.
Pipeline: discover local businesses -> find/crawl their website -> audit -> score the
opportunity (0-100) -> recommend a package -> draft outreach -> human approves -> send
via Gmail in rate-limited batches -> track the lead through a 12-stage pipeline.

Monorepo: `frontend/` (Next.js 14, TypeScript, Tailwind, shadcn/ui) and `backend/`
(Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 `Mapped[...]`, Alembic). One shared
Supabase Postgres; local dev falls back to SQLite (`backend/prospectos_dev.db`).

## Start of every session
1. Read `docs/PROJECT_CONTEXT.md` (state + constraints). For new features, read the
   spec in `docs/superpowers/specs/` and the plan in `docs/superpowers/plans/`.
2. Check the code before trusting the docs. Continue from the actual state.
3. Non-trivial work: write or update a spec, then a phased plan, get it approved, then
   build phase by phase. Do not start coding a feature that has no plan.

## Commands (Windows / PowerShell)
- Start both servers: `.\scripts\dev.ps1` (backend :8000, docs at /docs; frontend :3000)
- Stop both: `.\scripts\dev-stop.ps1`. Logs: `.devlogs\backend.log`, `.devlogs\frontend.log`
- Backend has no `--reload` on purpose (Windows venv bug). Restart after backend changes.
- Backend tests: `cd backend; .venv\Scripts\python -m pytest -q`
- Frontend typecheck: `cd frontend; npx tsc --noEmit`
- Frontend build (correctness check, there is no frontend test suite): `cd frontend; npm run build`
- ESLint is not configured. Do not run `npm run lint` (it prompts interactively).
- New migration: `cd backend; .venv\Scripts\python -m alembic revision --autogenerate -m "<what>"`,
  then `alembic upgrade head` against local SQLite first.
- CLI: `.venv\Scripts\python -m app search|audit|audit-all|generate-outreach|export`

## Hard rules
- **Never run git commands.** The owner does all git add/commit/push. (Enforced by a hook.)
- **Never fabricate business data.** No invented emails, ratings or websites. If no
  website is found, store exactly: `"Website not found from available sources."`
- **Nothing sends without human approval.** Outreach is drafted, a human approves it,
  and only approved drafts go out through batches. Respect `outreach_daily_send_limit`,
  `outreach_hourly_send_limit` and batch send windows. Never bypass approval or limits.
- **Demo mode is a security boundary.** `enforce_demo_mode` in `backend/app/main.py`
  is the final gate. Any new route must be checked against it; default is blocked.
- No Google Maps scraping and no paid discovery/AI APIs. Discovery goes through the
  `BusinessDiscoveryProvider` abstraction (OpenStreetMap first, Geoapify fallback, CSV, manual).
- Crawling stays conservative: robots.txt respected, max 10 pages, depth 2, no CAPTCHA
  or anti-bot bypass.
- Outreach copy never insults a business and only cites verified observations
  (Observation -> Improvement -> Benefit -> CTA).
- Tests never touch the shared Supabase database.
- Never edit `.env` files or a released Alembic migration. (Enforced by a hook.)
- Don't claim done without running it. Report what was verified and how.

## Conventions
- PKs are `String(36)` UUIDs and JSON columns use `sa.JSON`, so models run on SQLite
  and Postgres unchanged. No dialect-specific types.
- Audits are append-only (one row per run, never overwritten). Lead status changes are
  append-only in `lead_status_history`.
- Every score ships with human-readable `opportunity_reasons`. No unexplained numbers.
- External services sit behind a provider interface with a working fallback
  (AI: Ollama -> template engine; discovery: OSM -> Geoapify).
- Layout: routers in `app/api/`, models in `app/models/`, Pydantic in `app/schemas/`,
  logic in `app/services/<area>/`. Keep routers thin.
- API tests use the `client` fixture (in-memory SQLite via StaticPool); unit tests use
  `db_session`. Crawler tests use local HTML fixtures, never live sites.
- Inspect existing code before adding a pattern. Don't duplicate what exists. Smallest
  coherent change. No speculative rewrites, no invented requirements.

## Hooks and agents in this repo
- `PreToolUse` guard (`.claude/hooks/guard.py`): blocks git commands, `.env` edits and
  edits to existing migration files.
- `PostToolUse` check (`.claude/hooks/check.py`): syntax-checks edited Python files and
  marks which side of the stack changed.
- `Stop` gate (`.claude/hooks/stop_gate.py`): if backend changed, runs pytest; if
  frontend changed, runs `tsc --noEmit`. Failures block the turn from ending until fixed.
- Subagent `rules-reviewer` (`.claude/agents/rules-reviewer.md`): run it on the diff
  before reporting a feature as done.

## Working style
- Treat a multi-step request as one task. Keep going until it is finished or genuinely
  blocked. Don't stop after an intermediate step to announce the next one.
- Before finishing: reread the request, compare it with what was done, run the tests.
- When blocked, research first (code, docs, API references). If a decision is still
  needed, ask once with options and a recommendation.
- Suggest `/compact` after every two plan phases.
