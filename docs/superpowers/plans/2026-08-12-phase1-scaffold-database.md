# ProspectOS Phase 1-2: Repo Scaffold + Database Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the prospect-os monorepo skeleton (frontend + backend, no business logic yet) and the full SQLAlchemy/Alembic database layer for the five core tables, testable locally without a live Supabase connection.

**Architecture:** Monorepo with `frontend/` (Next.js 14 App Router + TS + Tailwind + shadcn/ui) and `backend/` (FastAPI + SQLAlchemy 2.0 + Alembic) as sibling directories. Backend uses sync SQLAlchemy with a Postgres-compatible schema that also runs on SQLite for fast local tests (portable column types: `String(36)` UUIDs, `sa.Enum`, `sa.JSON`). Supabase Postgres is the only shared piece; it is not touched by tests.

**Tech Stack:** Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, npm · Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, pydantic-settings, psycopg2-binary, pytest.

## Global Constraints

- Directory layout must exactly match: `frontend/`, `backend/app/{api,models,schemas,services/{discovery,crawler,analyzer,scoring,outreach,ai},database}`, `backend/tests/`, `scripts/`, `data/samples/`, root `README.md`, `.gitignore`, `.env.example`.
- Never commit secrets; all credentials via env vars; `.env.example` has placeholders only.
- Do NOT use SQLite as the primary/production database — it is permitted only as the disposable local test database, never referenced in app runtime config beyond tests.
- No auth in v1. Frontend never receives service-role Supabase credentials.
- Backend run command: `uvicorn app.main:app --reload` on port 8000. Frontend: `npm run dev` on port 3000.
- Business/WebsiteAudit/Outreach/LeadStatusHistory/Note models must match field lists from spec sections 8-9 and 33 exactly (field names verbatim).
- Do not fabricate data anywhere; optional fields stay NULL.
- Git: the user runs all git commands themselves. Do not run `git add`/`commit`/`push`. Skip any step below that says to commit — leave files staged for the user instead (or simply finish the task without committing).

---

## File Structure

```
prospect-os/                         (repo root = c:\Codes\ProspectAi)
  .gitignore
  .env.example
  README.md
  scripts/
  data/samples/
  backend/
    requirements.txt
    alembic.ini
    alembic/
      env.py
      script.py.mako
      versions/
    app/
      __init__.py
      main.py
      database/
        __init__.py
        config.py         # Settings (pydantic-settings)
        base.py            # declarative Base
        session.py          # engine, SessionLocal, get_db
      models/
        __init__.py
        enums.py
        business.py
        website_audit.py
        outreach.py
        lead_status_history.py
        note.py
      api/
        __init__.py
      schemas/
        __init__.py
      services/
        __init__.py
        discovery/__init__.py
        crawler/__init__.py
        analyzer/__init__.py
        scoring/__init__.py
        outreach/__init__.py
        ai/__init__.py
    tests/
      __init__.py
      conftest.py
      test_health.py
      test_models.py
  frontend/
    package.json
    tsconfig.json
    next.config.mjs
    postcss.config.mjs
    tailwind.config.ts
    components.json           (shadcn)
    app/
      layout.tsx
      page.tsx
      globals.css
    lib/
      utils.ts
```

---

### Task 1: Monorepo scaffold, gitignore, env example, README skeleton

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `scripts/.gitkeep`
- Create: `data/samples/.gitkeep`

**Interfaces:**
- Produces: env var names later tasks depend on — `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `NEXT_PUBLIC_API_BASE_URL`, `CORS_ORIGINS`.

- [ ] **Step 1: Create `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/
.pytest_cache/

# Node
node_modules/
.next/
out/
npm-debug.log*

# Env
.env
.env.local
*.env
!.env.example

# OS
.DS_Store
Thumbs.db

# Screenshots / generated artifacts
backend/data/screenshots/
*.png
!frontend/public/**/*.png

# Alembic sqlite test db
*.db
*.sqlite3
```

- [ ] **Step 2: Create `.env.example`**

```env
# ---- Shared Supabase Postgres (backend only, never sent to frontend) ----
DATABASE_URL=postgresql+psycopg2://postgres:password@db.your-project.supabase.co:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# ---- Backend ----
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development

# ---- Optional local AI ----
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# ---- Frontend ----
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

- [ ] **Step 3: Create `scripts/.gitkeep` and `data/samples/.gitkeep`** (empty files, so empty dirs are tracked)

- [ ] **Step 4: Create root `README.md`**

```markdown
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

Setup instructions are added as each part of the app is built; see the
"Local Development" section below, which is filled in progressively.

## Local Development (backend)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy ..\.env.example .env     # then fill in real values
uvicorn app.main:app --reload
```

Backend: http://localhost:8000  API docs: http://localhost:8000/docs

## Local Development (frontend)

```bash
cd frontend
npm install
copy ..\.env.example .env.local   # then fill in NEXT_PUBLIC_API_BASE_URL
npm run dev
```

Frontend: http://localhost:3000

## Responsible data collection

This tool only collects publicly available business information (OpenStreetMap,
manually entered data, or CSV import) and performs conservative, low-rate
website crawling that respects robots.txt. It does not bypass CAPTCHAs,
authentication, or anti-bot protections, and does not send bulk/automated
email. You are responsible for complying with applicable privacy and
anti-spam laws (e.g. CAN-SPAM, GDPR, CASL) when using data collected here.
```

- [ ] **Step 5: Leave changes unstaged for the user** — do not run any git commands.

---

### Task 2: Backend FastAPI app skeleton with health check

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_health.py`

**Interfaces:**
- Produces: `app.main:app` (FastAPI instance) — later tasks (routers in Task 4+ of future plans) call `app.include_router(...)` on this instance.

- [ ] **Step 1: Create `backend/requirements.txt`**

```txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
pydantic==2.10.4
pydantic-settings==2.7.0
python-dotenv==1.0.1
httpx==0.28.1
beautifulsoup4==4.12.3
playwright==1.49.1
python-multipart==0.0.20
pytest==8.3.4
pytest-asyncio==0.25.0
```

- [ ] **Step 2: Create `backend/app/__init__.py`** (empty file)

- [ ] **Step 3: Write the failing test** — `backend/tests/test_health.py`

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 4: Create venv and install deps, then run test to verify it fails**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest tests/test_health.py -v
```

Expected: FAIL (`ModuleNotFoundError: No module named 'app.main'` or import error).

- [ ] **Step 5: Create `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.config import get_settings

settings = get_settings()

app = FastAPI(
    title="ProspectOS API",
    description="Internal sales prospecting and website opportunity intelligence API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

(This references `app.database.config.get_settings`, built in Task 4 — implement Task 4's `database/config.py` before running this test if executing tasks out of order. When executing in order, Task 4 comes after this task, so temporarily this import will fail; that's expected and resolved once Task 4 lands. To keep Task 2 independently green, inline a minimal settings read here instead:)

```python
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ProspectOS API",
    description="Internal sales prospecting and website opportunity intelligence API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

Use this second (dependency-free) version so Task 2 is self-contained. Task 4 will later replace the CORS line to use `get_settings()` — see Task 4 Step 6.

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tests/test_health.py -v
```

Expected: PASS.

---

### Task 3: Frontend Next.js app skeleton

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.mjs`
- Create: `frontend/postcss.config.mjs`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/page.tsx`
- Create: `frontend/app/globals.css`
- Create: `frontend/lib/utils.ts`
- Create: `frontend/components.json`

**Interfaces:**
- Produces: a buildable Next.js app at `frontend/`, Tailwind + shadcn/ui wired, dark theme default. Later frontend tasks add pages under `app/` and components under `components/`.

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "prospectos-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.2.18",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.5",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {
    "typescript": "^5.7.2",
    "@types/node": "^22.10.2",
    "@types/react": "^18.3.17",
    "@types/react-dom": "^18.3.5",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20"
  }
}
```

- [ ] **Step 2: Create `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 3: Create `frontend/next.config.mjs`**

```js
/** @type {import('next').NextConfig} */
const nextConfig = {};

export default nextConfig;
```

- [ ] **Step 4: Create `frontend/postcss.config.mjs`**

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 5: Create `frontend/tailwind.config.ts`**

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: "hsl(var(--card))",
        muted: "hsl(var(--muted))",
        primary: "hsl(var(--primary))",
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 6: Create `frontend/app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 222 47% 6%;
    --foreground: 210 20% 92%;
    --card: 222 40% 9%;
    --muted: 217 19% 27%;
    --border: 217 19% 20%;
    --primary: 199 89% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

- [ ] **Step 7: Create `frontend/app/layout.tsx`**

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProspectOS",
  description: "Internal sales opportunity intelligence dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 8: Create `frontend/app/page.tsx`**

```tsx
export default function HomePage() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">ProspectOS</h1>
        <p className="mt-2 text-muted-foreground">
          Internal sales opportunity intelligence — dashboard coming up.
        </p>
      </div>
    </main>
  );
}
```

- [ ] **Step 9: Create `frontend/lib/utils.ts`** (standard shadcn helper)

```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 10: Create `frontend/components.json`** (shadcn/ui config, so `npx shadcn@latest add <component>` works in later tasks without re-prompting)

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "app/globals.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

- [ ] **Step 11: Install and verify it builds**

```bash
cd frontend
npm install
npm run build
```

Expected: build completes successfully (Next.js prints route summary, no errors). If `npm run build` fails on a missing `app/favicon.ico` or similar non-critical asset warning, that's fine — only treat actual compile/type errors as failures to fix.

---

### Task 4: Database config, base, and session modules

**Files:**
- Create: `backend/app/database/__init__.py`
- Create: `backend/app/database/config.py`
- Create: `backend/app/database/base.py`
- Create: `backend/app/database/session.py`
- Modify: `backend/app/main.py` (swap inline CORS env read for `get_settings()`)
- Test: `backend/tests/test_database_config.py`

**Interfaces:**
- Produces: `get_settings() -> Settings` (cached via `functools.lru_cache`), `Settings.database_url: str`, `Settings.cors_origins_list: list[str]`; `Base` (SQLAlchemy declarative base, from `app.database.base`); `get_db()` FastAPI dependency yielding a `Session`; `engine`, `SessionLocal` in `app.database.session`.

- [ ] **Step 1: Write the failing test** — `backend/tests/test_database_config.py`

```python
import os

from app.database.config import get_settings


def test_settings_reads_database_url_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@host:5432/db")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.database_url == "postgresql+psycopg2://u:p@host:5432/db"
    assert settings.cors_origins_list == [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_database_config.py -v
```

Expected: FAIL (`ModuleNotFoundError: No module named 'app.database'`).

- [ ] **Step 3: Create `backend/app/database/__init__.py`** (empty file)

- [ ] **Step 4: Create `backend/app/database/config.py`**

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./prospectos_dev.db"
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_database_config.py -v
```

Expected: PASS.

- [ ] **Step 6: Create `backend/app/database/base.py`**

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 7: Create `backend/app/database/session.py`**

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 8: Modify `backend/app/main.py`** to use `get_settings()` for CORS (replacing the inline `os.environ` read from Task 2)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.config import get_settings

settings = get_settings()

app = FastAPI(
    title="ProspectOS API",
    description="Internal sales prospecting and website opportunity intelligence API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 9: Run full test suite to confirm nothing broke**

```bash
pytest -v
```

Expected: all tests PASS (test_health, test_database_config).

---

### Task 5: SQLAlchemy models — enums, Business, WebsiteAudit, Outreach, LeadStatusHistory, Note

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/enums.py`
- Create: `backend/app/models/business.py`
- Create: `backend/app/models/website_audit.py`
- Create: `backend/app/models/outreach.py`
- Create: `backend/app/models/lead_status_history.py`
- Create: `backend/app/models/note.py`
- Create: `backend/tests/conftest.py`
- Test: `backend/tests/test_models.py`

**Interfaces:**
- Produces: `Business`, `WebsiteAudit`, `Outreach`, `LeadStatusHistory`, `Note` (all `app.database.base.Base` subclasses, with `id: Mapped[str]` UUID-string primary keys, `created_at`/`updated_at` timestamps); enums `WebsiteStatus`, `QualityCategory`, `OpportunityType`, `PackageType`, `OutreachAngle`, `LeadStatus` in `app.models.enums`. Every later task that reads/writes these tables imports from `app.models`.
- Consumes: `Base` from `app.database.base` (Task 4).

- [ ] **Step 1: Write the failing test** — `backend/tests/conftest.py` (shared fixture: fresh in-memory SQLite DB per test, all tables created)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    import app.models  # noqa: F401  ensures all model classes are registered on Base

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session: Session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
```

`backend/tests/test_models.py`:

```python
import uuid

from app.models.business import Business
from app.models.enums import (
    LeadStatus,
    OpportunityType,
    PackageType,
    QualityCategory,
    WebsiteStatus,
)
from app.models.lead_status_history import LeadStatusHistory
from app.models.note import Note
from app.models.outreach import Outreach
from app.models.website_audit import WebsiteAudit


def test_create_business_with_defaults(db_session):
    business = Business(name="ABC Plumbing", category="Plumber", city="Houston")
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)

    assert business.id is not None
    assert uuid.UUID(business.id)
    assert business.website_status is None
    assert business.created_at is not None
    assert business.updated_at is not None


def test_website_audit_belongs_to_business_and_stores_score_reasons(db_session):
    business = Business(name="ABC Plumbing", category="Plumber")
    db_session.add(business)
    db_session.commit()

    audit = WebsiteAudit(
        business_id=business.id,
        url="https://example.com",
        quality_category=QualityCategory.POOR,
        opportunity_types=[OpportunityType.AI_CHATBOT.value, OpportunityType.BOOKING_AUTOMATION.value],
        opportunity_reasons=["No obvious AI chatbot was detected.", "No obvious booking option."],
        overall_opportunity_score=91,
    )
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    assert audit.business_id == business.id
    assert audit.opportunity_types == ["AI_CHATBOT", "BOOKING_AUTOMATION"]
    assert audit.overall_opportunity_score == 91


def test_outreach_and_lead_status_history_and_note_link_to_business(db_session):
    business = Business(name="ABC Plumbing", category="Plumber")
    db_session.add(business)
    db_session.commit()

    outreach = Outreach(business_id=business.id, angle="AI_CHATBOT", subject="Quick idea", body="Hi there...")
    history = LeadStatusHistory(business_id=business.id, status=LeadStatus.NEW.value)
    note = Note(business_id=business.id, content="Called, left voicemail.")

    db_session.add_all([outreach, history, note])
    db_session.commit()

    assert outreach.id is not None
    assert history.status == "NEW"
    assert note.content == "Called, left voicemail."


def test_website_status_enum_accepts_not_found(db_session):
    business = Business(name="No Website Co", category="Plumber", website_status=WebsiteStatus.NOT_FOUND.value)
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)

    assert business.website_status == "not_found"


def test_package_type_enum_values():
    assert {p.value for p in PackageType} == {"STANDARD", "FULL", "CUSTOM"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_models.py -v
```

Expected: FAIL (`ModuleNotFoundError: No module named 'app.models.business'`).

- [ ] **Step 3: Create `backend/app/models/__init__.py`**

```python
from app.models.business import Business
from app.models.lead_status_history import LeadStatusHistory
from app.models.note import Note
from app.models.outreach import Outreach
from app.models.website_audit import WebsiteAudit

__all__ = [
    "Business",
    "WebsiteAudit",
    "Outreach",
    "LeadStatusHistory",
    "Note",
]
```

- [ ] **Step 4: Create `backend/app/models/enums.py`**

```python
import enum


class WebsiteStatus(str, enum.Enum):
    EXISTS = "exists"
    NOT_FOUND = "not_found"
    UNREACHABLE = "unreachable"


class QualityCategory(str, enum.Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    AVERAGE = "AVERAGE"
    WEAK = "WEAK"
    POOR = "POOR"
    CRITICAL = "CRITICAL"


class OpportunityType(str, enum.Enum):
    NO_WEBSITE = "NO_WEBSITE"
    WEBSITE_REDESIGN = "WEBSITE_REDESIGN"
    MOBILE_IMPROVEMENT = "MOBILE_IMPROVEMENT"
    CONVERSION_IMPROVEMENT = "CONVERSION_IMPROVEMENT"
    LEAD_CAPTURE = "LEAD_CAPTURE"
    AI_CHATBOT = "AI_CHATBOT"
    FAQ_AUTOMATION = "FAQ_AUTOMATION"
    BOOKING_AUTOMATION = "BOOKING_AUTOMATION"
    CUSTOMER_SUPPORT_AUTOMATION = "CUSTOMER_SUPPORT_AUTOMATION"
    ANALYTICS = "ANALYTICS"
    FULL_DIGITAL_UPGRADE = "FULL_DIGITAL_UPGRADE"
    CUSTOM_AI_AUTOMATION = "CUSTOM_AI_AUTOMATION"


class PackageType(str, enum.Enum):
    STANDARD = "STANDARD"
    FULL = "FULL"
    CUSTOM = "CUSTOM"


class OutreachAngle(str, enum.Enum):
    NEW_WEBSITE = "NEW_WEBSITE"
    WEBSITE_REDESIGN = "WEBSITE_REDESIGN"
    MOBILE_IMPROVEMENT = "MOBILE_IMPROVEMENT"
    AI_CHATBOT = "AI_CHATBOT"
    BOOKING = "BOOKING"
    LEAD_CAPTURE = "LEAD_CAPTURE"
    FULL_DIGITAL_UPGRADE = "FULL_DIGITAL_UPGRADE"


class LeadStatus(str, enum.Enum):
    NEW = "NEW"
    AUDITED = "AUDITED"
    QUALIFIED = "QUALIFIED"
    CONTACTED = "CONTACTED"
    FOLLOW_UP = "FOLLOW_UP"
    REPLIED = "REPLIED"
    DEMO_SENT = "DEMO_SENT"
    CALL_BOOKED = "CALL_BOOKED"
    PROPOSAL = "PROPOSAL"
    WON = "WON"
    LOST = "LOST"
    NOT_INTERESTED = "NOT_INTERESTED"


class BusinessSource(str, enum.Enum):
    OPENSTREETMAP = "openstreetmap"
    CSV = "csv"
    MANUAL = "manual"
```

- [ ] **Step 5: Create `backend/app/models/business.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)

    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    google_maps_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    website_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 6: Create `backend/app/models/website_audit.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class WebsiteAudit(Base):
    __tablename__ = "website_audits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)

    url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    https_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crawl_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)

    has_viewport: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_contact_form: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_email: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_phone: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    has_booking: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_faq: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_live_chat: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_ai_chatbot: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_whatsapp: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    has_social_links: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    broken_link_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    mobile_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    design_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    technical_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversion_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    customer_experience_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    website_quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_opportunity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    redesign_opportunity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overall_opportunity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    quality_category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    opportunity_types: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    audit_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    opportunity_reasons: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    screenshot_desktop_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    screenshot_mobile_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Note: `opportunity_types` and `opportunity_reasons` are stored as JSON lists of plain strings (enum `.value`s), not native enum arrays, so the column works identically on SQLite (tests) and Postgres (Supabase).

- [ ] **Step 7: Create `backend/app/models/outreach.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Outreach(Base):
    __tablename__ = "outreach"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)

    angle: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)

    generated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "ollama" | "template"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 8: Create `backend/app/models/lead_status_history.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class LeadStatusHistory(Base):
    __tablename__ = "lead_status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 9: Create `backend/app/models/note.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 10: Run tests to verify they pass**

```bash
pytest tests/test_models.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 11: Run full backend test suite**

```bash
pytest -v
```

Expected: all tests across test_health, test_database_config, test_models PASS.

---

### Task 6: Alembic setup and initial migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/` (initial revision file, generated)
- Test: manual verification (migration apply/downgrade), documented below — Alembic migrations are not unit-tested with pytest, they're verified by running them against a disposable local Postgres or SQLite file.

**Interfaces:**
- Produces: `alembic upgrade head` creates all 5 tables matching the SQLAlchemy models exactly. Later phases assume `alembic upgrade head` is the only supported way to create/update the shared Supabase schema.

- [ ] **Step 1: Install alembic is already in requirements.txt (Task 2) — initialize alembic scaffolding**

```bash
cd backend
alembic init alembic
```

This generates `alembic.ini` and `alembic/` with `env.py`, `script.py.mako`, `versions/`. We will edit the generated `alembic.ini` and `alembic/env.py` per the next steps rather than hand-writing them from scratch.

- [ ] **Step 2: Edit `backend/alembic.ini`** — remove the hardcoded `sqlalchemy.url` line (leave it blank; `env.py` sets it from app settings instead)

Find the line:
```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```//
Replace with:
```ini
sqlalchemy.url =
```

- [ ] **Step 3: Replace `backend/alembic/env.py` contents**

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.database.base import Base
from app.database.config import get_settings
import app.models  # noqa: F401  registers all models on Base.metadata

config = context.config

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Generate the initial revision (autogenerate against a local disposable SQLite file, since no live Supabase DB exists yet)**

```bash
cd backend
set DATABASE_URL=sqlite:///./_alembic_bootstrap.db
alembic revision --autogenerate -m "initial schema: businesses, website_audits, outreach, lead_status_history, notes"
```

(On Windows PowerShell use `$env:DATABASE_URL = "sqlite:///./_alembic_bootstrap.db"` instead of `set`.)

- [ ] **Step 5: Inspect the generated migration file** in `backend/alembic/versions/`, confirm it creates all 5 tables (`businesses`, `website_audits`, `outreach`, `lead_status_history`, `notes`) with the columns from Task 5's models, and that foreign keys reference `businesses.id`.

- [ ] **Step 6: Apply the migration to the disposable SQLite file to verify it runs cleanly**

```bash
alembic upgrade head
```

Expected: command completes with no errors, prints the applied revision.

- [ ] **Step 7: Verify downgrade works**

```bash
alembic downgrade base
```

Expected: completes with no errors (all 5 tables dropped).

- [ ] **Step 8: Re-apply upgrade (leave schema in place for reference) then delete the bootstrap file**

```bash
alembic upgrade head
del _alembic_bootstrap.db
```

- [ ] **Step 9: Document in root `README.md`** — append a short "Database migrations" subsection under "Local Development (backend)":

```markdown
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
```

---

## Self-Review Notes (for the implementer to confirm before moving to Phase 3-4)

- Spec coverage check: repo layout (section 5) ✅ Task 1/2/3; env vars (section 6) ✅ Task 1; Business model fields (section 8) ✅ Task 5 field-for-field; WebsiteAudit fields (section 9) ✅ Task 5 field-for-field; migrations via Alembic, not SQLite as primary (section 7) ✅ Task 6 (SQLite used only as a bootstrap/test convenience, never as `DATABASE_URL` in `.env.example`); lead status enum (section 33) ✅ `enums.py`; no auth yet (section 37) ✅ nothing added; no secrets committed (section 38) ✅ `.env.example` only.
- Anything below this line is explicitly OUT of scope for this plan and belongs to later phase plans: discovery providers, CSV import, crawler, analyzer, scoring, outreach generation, API routers beyond `/health`, frontend pages beyond the placeholder home page, CLI, tests beyond models/config/health.

## After completing this plan

1. Run the full backend test suite (`pytest -v` from `backend/`) and confirm all green.
2. Run `npm run build` in `frontend/` and confirm it succeeds.
3. Tell the user this phase pair is done and suggest `/compact` before continuing to Phase 3-4 (Business Discovery + Core API), per their stated preference.
