# ProspectOS — Project Context

Paste this whole file into a new Claude conversation to give it full context on this project.

## What it is (the concept)

**ProspectOS** is an internal sales-prospecting tool for a two-person web
development + AI automation business (not a product being sold to anyone —
it's tooling the two founders use themselves).

The problem it solves: instead of manually hunting for local businesses that
need a new website / better website / AI automation (chatbots, booking,
FAQ automation, etc.), ProspectOS automates the *research* half of cold
outreach:

1. **Find local businesses** (plumbers, dentists, restaurants, etc.) via
   OpenStreetMap search, CSV import, or manual entry — no Google Maps
   scraping, no paid data APIs.
2. **Find each business's website** (or determine it doesn't have one —
   "no website" is itself the #1 opportunity signal).
3. **Crawl the website** conservatively (Playwright, max 10 pages, depth 2,
   respects robots.txt, no CAPTCHA/anti-bot bypass).
4. **Audit it**: technical health, mobile-friendliness, design quality,
   content, conversion elements (contact form, booking, live chat, AI
   chatbot presence), customer-experience signals.
5. **Score the opportunity**: a 0-100 "how much could we help this business"
   score with configurable weights, landing them in a quality category
   (EXCELLENT → CRITICAL) and a list of specific opportunity types (e.g.
   `NO_WEBSITE`, `AI_CHATBOT`, `BOOKING_AUTOMATION`, `MOBILE_IMPROVEMENT`).
6. **Recommend a service package** (STANDARD / FULL / CUSTOM) based on the
   findings.
7. **Draft personalized outreach** (never insults the business, only cites
   verified observations, Observation → Improvement → Benefit → CTA
   structure) using a local Ollama LLM if available, or a template engine
   if not — no paid AI APIs, and outreach is drafted for **human review**,
   never auto-sent. No mass emailing, ever.
8. **Track the lead** through a pipeline (dashboard, prospect table with
   filters/sorting, prospect detail page, 12-stage lead status with history,
   notes) as the humans manually contact and follow up with the business.

It's explicitly an **internal MVP**, not a SaaS product: no auth (v1), no
cloud deployment, no mass email sending, minimal visual polish — just a
working local tool two people can both run against one shared database.

## Tech stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS,
  shadcn/ui, npm. Dark-themed internal dashboard.
- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0
  (declarative, `Mapped[...]` style), Alembic migrations.
- **Database**: **Supabase Postgres** — used purely as hosted Postgres (DB
  only, no Supabase Auth/Storage/Edge functions). One shared project both
  developers point their local backends at, so they see each other's data
  live. Not yet provisioned — app is currently scaffolded against
  `.env.example` placeholders.
- **Crawling**: Playwright (headless browser) + httpx + BeautifulSoup4.
- **AI**: Ollama (local LLM, optional) for outreach copy generation, with a
  template-based fallback provider so the app fully works with zero AI
  installed. No paid AI APIs (no OpenAI/Anthropic API keys used at runtime).
- **Business discovery**: OpenStreetMap/Overpass API, CSV import, manual
  entry — via a `BusinessDiscoveryProvider` abstraction (no Google Maps
  scraping, no paid APIs).
- **Testing**: pytest + Playwright, run against disposable local SQLite
  (never against the shared Supabase instance).
- **Infra**: **Nothing is deployed.** No Vercel/Railway/Render/VPS. Each
  developer runs `frontend` (localhost:3000) and `backend` (localhost:8000)
  on their own machine; only the Postgres database is shared/remote.

## Architecture

```
GitHub monorepo (c:\Codes\ProspectAi)
  ├── frontend/   Next.js — localhost:3000
  └── backend/    FastAPI — localhost:8000
                    └── Supabase PostgreSQL (shared, remote — DB only)
```

Both developers clone the repo, each run their own `frontend` + `backend`
locally, both connect to the same Supabase Postgres, so changes either
person makes (new leads, status updates, notes) are visible to the other
in near-real-time via the shared DB — no auth needed for v1 since it's just
the two of them.

## Data model (5 tables, via SQLAlchemy + Alembic)

- **`businesses`** — name, category, address/city/state/country, lat/lng,
  phone, email, website, source (openstreetmap/csv/manual), source_url,
  google_maps_url, rating, review_count, website_status
  (exists/not_found/unreachable), timestamps.
- **`website_audits`** — one row per audit run (never overwritten, so
  history is preserved for the two-person shared DB): url, http_status,
  https_enabled, title/meta, page_count, crawl_depth, a dozen boolean
  feature flags (`has_contact_form`, `has_booking`, `has_ai_chatbot`,
  `has_whatsapp`, etc.), broken_link_count, per-dimension scores (mobile,
  design, technical, content, conversion, customer_experience), rollup
  scores (website_quality_score, ai_opportunity_score,
  redesign_opportunity_score, overall_opportunity_score), quality_category,
  opportunity_types (JSON list), opportunity_reasons (JSON list, always
  human-readable justifications), screenshot paths.
- **`outreach`** — one row per generated draft (business_id, angle, subject,
  body, generated_by: "ollama"|"template").
- **`lead_status_history`** — append-only status changes (12-value enum:
  NEW → AUDITED → QUALIFIED → CONTACTED → FOLLOW_UP → REPLIED → DEMO_SENT →
  CALL_BOOKED → PROPOSAL → WON/LOST/NOT_INTERESTED) with note + changed_by.
- **`notes`** — free-text notes per business.

All PKs are string UUIDs (`String(36)`), JSON columns use `sa.JSON` — chosen
so the exact same models run against both SQLite (fast disposable test DB)
and Postgres (shared Supabase) without any dialect-specific types.

## Hard constraints (do not violate)

- No fabricated business data — ever. If a website can't be found, the
  literal string is `"Website not found from available sources."`
- No Google Maps scraping, no paid discovery/AI APIs.
- No CAPTCHA bypass, no anti-bot stealth techniques, no auth bypass, no
  robots.txt violations, max 10 pages / depth 2 per crawl.
- No mass/automated email sending — outreach is always drafted for a human
  to review and send manually.
- No authentication in v1 (but the schema is structured so it could be
  added later).
- No cloud deployment at this stage — local-only for both developers.
- Never insult a business in outreach copy; only cite verified, observed
  facts.
- Tests never touch the shared Supabase database.

## Current build status (as of last session)

**Done — the whole pipeline works end-to-end, backend + frontend:**
- Repo scaffold, `.env.example`, `README.md`, `scripts/dev.ps1` (one-command
  launcher that opens backend + frontend each in their own window) ✅
- Backend: FastAPI app, all 5 models/enums/schemas, full CRUD + CSV
  import/export + OSM search API on `/api/businesses` ✅
- Business discovery: OpenStreetMap provider (Nominatim + Overpass), CSV
  provider, Manual provider, phone/website/name+city dedup ✅
- Conservative Playwright crawler (max 10 pages, depth 2, robots.txt
  respected, `channel="chromium"` launch to avoid a headless-shell binary
  download issue hit in this environment) + heuristic HTML analyzer + 0-100
  opportunity scoring engine (12 `OpportunityType`s, human-readable
  `opportunity_reasons` always attached) + package recommendation +
  desktop/mobile screenshot capture (served at `/screenshots/...`) ✅
- AI outreach: dual-provider abstraction (Ollama if available, template
  engine always available as fallback), Observation→Improvement→Benefit→CTA
  drafts, never auto-sent ✅
- CLI (`python -m app search/audit/audit-all/generate-outreach/export`) ✅
- Backend tests: **62/62 passing** against disposable in-memory SQLite,
  including the required "bad site scores higher opportunity than good
  site" scenario ✅
- Frontend: Next.js dashboard (summary stats + top opportunities), Prospects
  table (filter/sort/search/pagination, manual add, CSV import/export),
  Prospect detail page (contact info, status history + change, audit scores
  + opportunity reasons + screenshots, outreach draft generation + history,
  notes), Discover page (OSM search + preview + save) — all wired to the
  live API, `npm run build` passes clean ✅
- Verified live end-to-end: created a business via the API, ran a real
  Playwright audit against a live URL, generated an outreach draft, added a
  note, changed lead status, and confirmed the detail endpoint aggregates
  all of it correctly ✅

**Not done yet:**
- Real Supabase Postgres has never been provisioned/connected to — everything
  above has been verified against local SQLite only (by design, so tests and
  demo prep never touch the shared DB prematurely). Alembic migrations are
  verified clean on SQLite; running them once against the real Supabase URL
  is the one step left before both developers can share data live.
- No automated frontend test suite (relies on `npm run build` + manual
  verification).
- Ollama outreach generation has not been exercised live in this
  environment (the template fallback has been, extensively) — install
  Ollama and pull a model to try it.

All 6 planned phase-pairs are functionally complete:
- ✅ Phase 1-2: scaffold + DB layer
- ✅ Phase 3-4: Business discovery + Core API + CSV import/export
- ✅ Phase 5-6: Website crawler + analyzer/scoring engine
- ✅ Phase 7-8: Screenshots + AI/outreach generation + remaining API + CLI
- ✅ Phase 9-10: Frontend build-out + wiring to backend
- ~ Phase 11-12: backend test fixtures done; frontend has no automated
  tests yet; final docs (this file + `README.md`) updated; Supabase
  provisioning still pending

## Where the full detail lives

- `docs/superpowers/specs/2026-08-12-prospectos-design.md` — design
  decisions (Supabase scaffold-only, npm choice, 12-phase build order,
  non-goals, testing strategy).
- `docs/superpowers/plans/2026-08-12-phase1-scaffold-database.md` — the
  exact implementation plan (with full code) for everything built so far.
- The original user spec (49 sections) that drove all of this is not saved
  as a separate file yet, but is fully reflected in the design doc above.

## Standing process rules for this project

- User runs all `git add`/`commit`/`push` themselves — Claude never runs
  git commands.
- Build straight through phases with minimal check-ins; suggest `/compact`
  after every 2 phases (Claude can't run `/compact` itself).
- Don't overengineer. Don't build auth. Don't deploy. Don't build mass
  email. Get the core pipeline actually working end-to-end before
  declaring anything done.
