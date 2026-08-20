# ProspectOS

Internal AI-powered business opportunity intelligence tool for a two-person
web development + AI automation business. Finds local businesses, audits
their websites, scores commercial opportunity, and drafts personalized
outreach for human review.

This is NOT a tool for selling ProspectOS itself — it is internal sales
tooling. See `docs/superpowers/specs/2026-08-12-prospectos-design.md` for
the full design.

## Architecture

Both developers run the app entirely locally except for one shared Supabase
Postgres database:

```
GitHub
  ├── frontend/   Next.js (localhost:3000)
  └── backend/    FastAPI (localhost:8000)
                    └── Supabase PostgreSQL (shared, remote)
```

## Quick start

```powershell
# One-time setup
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium   # crawler + screenshots need this
copy ..\.env.example .env      # fill in real values (or leave as-is for local SQLite)
.venv\Scripts\python -m alembic upgrade head           # creates the schema

cd ..\frontend
npm install

# Every time after that, from the repo root:
.\scripts\dev.ps1
```

`dev.ps1` runs the backend (http://localhost:8000, docs at `/docs`) and
frontend (http://localhost:3000) as hidden background processes — no popup
CMD/PowerShell windows, everything stays inside whatever terminal you ran
it from (including VS Code's integrated terminal). Logs go to
`.devlogs\backend.log` / `.devlogs\frontend.log`:

```powershell
Get-Content -Wait .devlogs\backend.log    # tail backend logs live
Get-Content -Wait .devlogs\frontend.log   # tail frontend logs live
```

Both process IDs are tracked in `.dev-pids.json`. To stop them both cleanly
(instead of hunting for stray processes by hand):

```powershell
.\scripts\dev-stop.ps1
```

It also kills anything else listening on 8000/3000 as a fallback, so it's
the right thing to run if a dev server ever gets stuck.

If `backend/.env` is absent or has no `DATABASE_URL`, the backend falls back
to a local disposable SQLite file (`backend/prospectos_dev.db`) — good for
solo development or a demo without touching the shared Supabase instance.
To point at the real shared database, fill in `DATABASE_URL` in
`backend/.env` with the Supabase connection string and re-run
`alembic upgrade head` once.

### Database migrations

The first time you connect to a fresh Supabase project (after filling in
`DATABASE_URL` in `backend/.env`), run:

```bash
cd backend
alembic upgrade head
```

This creates `businesses`, `website_audits`, `outreach`, `lead_status_history`,
and `notes`. Both developers point at the same Supabase project, so only one
of you needs to run this once per schema change — after someone adds a new
migration, everyone else just runs `alembic upgrade head` again.

### Optional: local AI outreach drafts (Ollama)

Outreach drafting works out of the box with a template engine — no AI
required. To get LLM-written drafts instead, install
[Ollama](https://ollama.com), pull a model, and set `OLLAMA_BASE_URL` /
`OLLAMA_MODEL` in `backend/.env`:

```bash
ollama pull llama3.1
```

If Ollama isn't running, the app automatically falls back to the template
provider — no configuration needed either way.

### CLI

The backend also has a script-friendly CLI for bulk workflows, e.g. batch
auditing everything that doesn't have a recent audit yet:

```bash
cd backend
.venv\Scripts\python -m app search --category plumber --city Houston --save
.venv\Scripts\python -m app audit-all
.venv\Scripts\python -m app generate-outreach <business_id> [--angle ANGLE]
.venv\Scripts\python -m app export prospects.csv
```

### Example workflow

1. Go to **Discover**, search a category + city (e.g. "plumber" in
   "Houston"), review the results, then "Save all as prospects".
2. Go to **Prospects**, open one of the new rows.
3. Click **Run audit** — this crawls the business's site (or records
   "no website" if none was found), scores the opportunity, and captures
   screenshots.
4. Review the quality/opportunity scores and reasons, then click
   **Generate outreach draft** to get a human-reviewable email.
5. Update the lead status as you follow up, and leave notes for your
   co-founder to see (shared DB, near-real-time).

## Testing

```bash
cd backend
.venv\Scripts\python -m pytest -q
```

All 62 backend tests run against disposable in-memory SQLite — they never
touch the shared Supabase instance. There is currently no automated frontend
test suite (`npm run build` is the frontend's correctness check).

## Known limitations (v1)

- No authentication — anyone with network access to a running instance can
  use it. Fine for two trusted developers on their own machines; not for
  wider or public deployment.
- Nothing is deployed — both frontend and backend must be running locally.
- Website analysis is heuristic (regex/substring signal detection on raw
  HTML), not a full accessibility/performance audit — treated as a
  best-effort opportunity signal, not a certified report.
- OpenStreetMap coverage varies by region/category; sparse results just mean
  fewer OSM tags for that query, not that no businesses exist.
- No pagination on the OSM search results page (relies on the `limit`
  parameter you set before searching).
- `playwright install chromium` also tries to download a separate "Chromium
  Headless Shell" binary, which has failed to download in some environments
  due to CDN timeouts. The crawler/screenshot code explicitly launches with
  `channel="chromium"` so it only needs the main Chromium binary — if the
  headless-shell download fails, that's safe to ignore as long as the main
  Chromium download succeeded.
- `npm audit` reports advisories in Next.js 14.2.x that are only fully
  resolved by a Next.js 16 major upgrade; acceptable for a local-only,
  non-deployed internal tool, but worth revisiting before this ever runs
  anywhere network-exposed.

## Possible V2 features

- Authentication (even simple shared-password gating) if this ever needs to
  run somewhere other than two developers' own machines.
- Kanban-style pipeline board for lead status instead of a flat table.
- Scheduled/recurring re-audits to catch when a prospect's website changes.
- Bulk outreach draft generation across a filtered list of prospects.
- Richer analytics on the dashboard (conversion funnel by status, win rate
  by category/city, opportunity-type breakdown charts).
- Direct email send integration (still human-reviewed/human-triggered per
  send — this app deliberately never automates sending).

## Responsible data collection

This tool only collects publicly available business information (OpenStreetMap,
manually entered data, or CSV import) and performs conservative, low-rate
website crawling that respects robots.txt. It does not bypass CAPTCHAs,
authentication, or anti-bot protections, and does not send bulk/automated
email. You are responsible for complying with applicable privacy and
anti-spam laws (e.g. CAN-SPAM, GDPR, CASL) when using data collected here.
