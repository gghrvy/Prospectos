# ProspectOS — Design Spec

Date: 2026-08-12
Status: Approved (user requested minimal check-ins, build straight through)

## 1. Source of truth

The full functional/architectural spec was provided directly by the user in the
initiating request (business purpose, pipeline, tech stack, data models, scoring
rules, UI, testing requirements, CLI, definition of done). That spec is
authoritative and is not repeated here in full — this document captures only the
decisions the original spec left open, plus the build order.

## 2. Decisions made in this session

- **Supabase**: no live project exists yet. Build against `.env.example`
  placeholders; document exact setup so either developer can create the
  Supabase project and run `alembic upgrade head` themselves later. Do not
  assume a live DB connection during this build; local tests that need a DB
  use a local Postgres/SQLite test fixture, never the shared Supabase instance.
- **Frontend package manager**: npm (matches the spec's documented commands
  exactly).
- **Backend package manager**: pip + venv (per spec section 45, explicit
  commands given).
- **Build cadence**: build straight through phase by phase with minimal
  check-ins. After every 2 phases, pause and tell the user to run `/compact`
  before continuing (per standing user preference — Claude cannot invoke
  compact itself).

## 3. Architecture (restated briefly)

```
GitHub repo: prospect-os/
  frontend/  (Next.js, TS, Tailwind, shadcn/ui)  → localhost:3000
  backend/   (FastAPI, SQLAlchemy, Alembic)       → localhost:8000
                    ↓
              Supabase PostgreSQL (shared, remote, DB-only)
```

Both developers run frontend + backend + Playwright + (optional) Ollama
locally; only Postgres is shared/remote. No auth in v1. No deployment in v1.

## 4. Build order (phases)

Grouped in pairs; a `/compact` checkpoint follows each pair.

1. **Repo scaffold** — monorepo directories, `.gitignore`, `.env.example`,
   root README skeleton, `backend/` FastAPI app skeleton, `frontend/`
   Next.js app skeleton (no business logic yet).
2. **Database layer** — SQLAlchemy models (businesses, website_audits,
   outreach, lead_status_history, notes), Alembic setup + initial migration,
   DB session/config module.
   — *compact checkpoint 1* —
3. **Business discovery** — `BusinessDiscoveryProvider` abstraction,
   `OpenStreetMapProvider` (Overpass API), `CSVProvider`, `ManualProvider`,
   dedup strategy.
4. **Core API + CSV** — Pydantic schemas, FastAPI routers for businesses
   (CRUD/list/filter), CSV import/export endpoints, OSM search endpoint.
   — *compact checkpoint 2* —
5. **Website discovery + crawler** — website URL resolution, Playwright
   crawler (depth 2, max 10 pages, robots.txt respect, feature/content
   extraction).
6. **Analyzer + scoring engine** — technical/mobile/design/content/
   conversion/CX/AI-detection analyzers, configurable weighted scoring,
   quality categories, opportunity types, opportunity score with reasons,
   package recommendation.
   — *compact checkpoint 3* —
7. **Screenshots + AI + outreach** — Playwright screenshot capture,
   `AIProvider` abstraction (`OllamaProvider` + `TemplateProvider`),
   outreach generation (observation + improvement + benefit + CTA).
8. **Remaining API + CLI** — audit-run endpoint, outreach generate/regenerate
   endpoints, status-change + status-history endpoints, `python -m app`
   CLI commands (search/audit/audit-all/score-all/generate-outreach/export).
   — *compact checkpoint 4* —
9. **Frontend scaffold** — Tailwind + shadcn/ui setup, dark theme, layout/nav,
   `/dashboard`, `/prospects`, `/prospects/[id]`, `/audits`, `/settings` page
   shells, API client lib.
10. **Frontend wiring** — dashboard metrics/charts, prospect table with
    filters/sort, prospect detail page (scores, screenshots, outreach,
    status, notes), status change UI, CSV import/export UI.
    — *compact checkpoint 5* —
11. **Tests** — pytest fixtures (a deliberately bad website, a good website),
    unit/integration tests per spec section 43, run and fix until green.
12. **Verification + docs** — run backend + frontend locally, walk the
    critical pipeline end-to-end with sample data, finalize README with the
    10 deliverables the spec requires (setup, Supabase instructions, env
    vars, run commands, Ollama setup, example workflow, testing instructions,
    known limitations, V2 features).

## 5. Explicit non-goals (from original spec, restated for the plan)

No auth, no deployment, no mass email sending, no paid APIs, no CAPTCHA/
anti-bot bypass, no fabricated data (ratings/emails/websites), no SQLite as
primary DB, no separate repos, no Supabase Edge Functions for core logic.

## 6. Testing strategy

pytest for backend logic (dedup, scoring, discovery, outreach generation) run
against a disposable local test database — not the shared Supabase instance.
Playwright crawler tests run against local static HTML fixtures (the "bad
site" and "good site" fixtures required by spec section 43), not live
websites, to keep tests deterministic and offline-capable.
