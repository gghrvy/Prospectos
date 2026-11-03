# ProspectOS UI Redesign ("Assay Report") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the ProspectOS visual layer with the approved "Assay Report" design system and fix the UX defects found in the audit, without touching backend logic or API contracts.

**Architecture:** Tokens live once in `frontend/MASTER.md`, mirrored as CSS variables in `globals.css` and exposed through `tailwind.config.ts`. Shared primitives in `components/ui/` and domain pieces in `components/` consume only tokens. Pages are restyled one at a time; motion is added last through framer-motion with a global `MotionConfig reducedMotion="user"`.

**Tech Stack:** Next.js 14 App Router, TypeScript, Tailwind 3, framer-motion 11, lucide-react, next/font (IBM Plex Sans + Plex Serif).

**Spec:** `docs/superpowers/specs/2026-11-02-ui-redesign-design.md`

## Global Constraints
- Colors, sizes, radii, shadows and durations come from tokens only. No raw Tailwind palette colors (`emerald-400`, `slate-950`, ...) and no hex values in components.
- No `font-mono`, no all-caps tracked labels, no middle-dot meta strings, no `→` suffixes on links or buttons.
- No backend files change. `lib/api.ts` request shapes do not change (new helpers built on existing calls are fine).
- Every mutation control is hidden or disabled when `isDemoMode` is true.
- Interactive elements have default, hover, focus-visible, active and disabled states. Focus ring: 2px `survey`, 2px offset on `paper`.
- Hooks are never called after an early return.
- Motion: 120 / 180 / 240ms, ease `cubic-bezier(.2,.8,.2,1)`, exits at 0.7x; transform and opacity only.
- Keyboard shortcuts never fire while focus is in an `input`, `textarea`, `select` or `[contenteditable]`.
- Owner runs git. "Commit" steps mean: print the suggested message and stop for the owner.

## Review Focus
1. More than 200 leads: dashboard and pipeline counts must cover every lead, not the first page. Pinned by `fetchAllBusinesses` in Task 3 and checked in Task 6.
2. `current_status` is null or a string missing from `LEAD_STATUSES`: treated as NEW / shown raw in Research, never a crash or a dropped lead. Pinned in Task 1 (`phaseOf`).
3. Typing "j", "/" or "g" inside the search box or a note textarea must type the letter, not trigger a shortcut. Pinned in Task 2.
4. Demo mode: no status-change, delete, import, note, sender, Gmail or batch control is reachable on any page, including the new Pipeline page. Checked in Tasks 5, 6, 7 and 10.
5. Reduced motion on: score reveal and stage marker show their final state immediately. Checked in Task 9.

## Verification used by every task
- `cd frontend; npx tsc --noEmit` → no output, exit 0.
- `cd frontend; npm run build` → "Compiled successfully".
- Visual check with the Playwright MCP against `npm run dev` at 1440x900 and 375x812: screenshot each touched page, live mode (backend `.\scripts\dev.ps1`) and demo mode (`$env:NEXT_PUBLIC_DEMO_MODE='true'` for the frontend, `$env:DEMO_MODE='true'` in the backend shell; no `.env` edits).
- There is no frontend test runner; pure helpers get a one-off check via `browser_evaluate` or a scratchpad `node` script, not a new test framework.

---

### Task 1: Design tokens, fonts and base primitives
Skills: paint (design system phase), ui-ux-pro-max, frontend-design.

**Files:**
- Create: `frontend/MASTER.md` (the token tables and meaning rules from the spec, plus component specs)
- Create: `frontend/lib/stages.ts`, `frontend/lib/motion.ts`
- Modify: `frontend/app/globals.css`, `frontend/tailwind.config.ts`, `frontend/app/layout.tsx` (fonts only)
- Modify: `frontend/components/ui/{button,input,select,textarea,label,card,badge,gauge}.tsx`
- Create: `frontend/components/ui/checkbox.tsx`

**Interfaces:**
- Produces Tailwind color names: `paper sheet ink graphite rule survey ochre brick`, plus `survey-soft` (survey at 10% on sheet) and `brick-soft`. Font families `font-sans` (Plex Sans) and `font-serif` (Plex Serif). `rounded-tag|control|panel` = 4/6/10px. `shadow-float`. `duration-fast|base|slow` = 120/180/240ms and `ease-assay`.
- `lib/stages.ts`:
  `type Phase = "research" | "contact" | "conversation" | "closing" | "outcome"`;
  `PHASES: { id: Phase; label: string; statuses: LeadStatus[] }[]` (spec grouping);
  `phaseOf(status: string | null): Phase` (null → research; unknown → research);
  `stageIndex(status: string | null): number` (position in the 13 progress stages, -1 for outcomes);
  `stageLabel(status: string | null): string` (LEAD_STATUS_LABELS, else raw string with `_` → space, null → "New").
- `lib/motion.ts`: `DURATION = { fast: 0.12, base: 0.18, slow: 0.24 }`, `EASE = [0.2, 0.8, 0.2, 1] as const`, `exit(d: number) => d * 0.7`.
- Components keep their current exported names and props so pages compile untouched: `Button` (variants `default | outline | ghost | destructive`, sizes `sm | md`), `Card/PrimaryCard/CardHeader/CardTitle/CardContent`, `Badge`, `QualityBadge`, `SignalMeter`/`OpportunityScoreBadge`, `StatusBadge`, `RadialGauge`. New: `Checkbox` (forwardRef over `<input type="checkbox">`, same props).

- [ ] Write `MASTER.md` from the spec tokens; add per-component rules (button heights 32/36, input height 36, table row 40, panel padding 16).
- [ ] Replace `:root` variables in `globals.css` with the spec hexes (store as `R G B` triplets for `/alpha` support), set `color-scheme: light`, remove the Leaflet dark overrides in favor of token-based ones, remove `.page-kicker` and `.font-display`, rewrite `.data-table` with 40px rows and `py-0`-free cells, and add `@media (prefers-reduced-motion: reduce)` that sets transition and animation durations to 0.01ms.
- [ ] Swap `IBM_Plex_Mono` for `IBM_Plex_Serif` (weights 500, 600) in `layout.tsx`; drop `className="dark"`.
- [ ] Restyle the primitives. Badge: sentence case, 12px, `rounded-tag`. SignalMeter: survey ticks at opacity steps (more score = more ink), number in tabular sans. QualityBadge: ochre for WEAK/AVERAGE, brick for POOR/CRITICAL, ink otherwise. StatusBadge: dot + `stageLabel`; WON survey, LOST/NOT_INTERESTED graphite, others ink. RadialGauge colors from CSS variables, no hex.
- [ ] Check `phaseOf(null) === "research"`, `phaseOf("BOGUS") === "research"`, `phaseOf("WON") === "outcome"`, `stageIndex("PROPOSAL") === 12`, `stageLabel("BOGUS_STATE") === "BOGUS STATE"` with a scratchpad node script (transpile with `npx tsc --outDir` into the scratchpad).
- [ ] Run tsc + build; screenshot all pages (they will look half-migrated; that's expected, just confirm nothing is broken).
- [ ] Commit: `style(frontend): add Assay Report tokens, fonts and base primitives`

### Task 2: App shell
Skills: desktop-principles, frontend-design.

**Files:**
- Create: `frontend/components/shell/sidebar.tsx`, `frontend/components/shell/mobile-bar.tsx`, `frontend/components/shell/demo-notice.tsx`, `frontend/components/shell/page-header.tsx`, `frontend/components/shell/shortcuts.tsx`
- Modify: `frontend/app/layout.tsx`; Delete: `frontend/components/nav.tsx`

**Interfaces:**
- `PageHeader({ title: string; description?: string; actions?: ReactNode; meta?: ReactNode })`: serif 28px title, 14px graphite description, actions wrap on narrow screens.
- `DemoNotice({ children: ReactNode })`: the single demo banner; renders nothing when not in demo mode.
- `ShortcutsProvider` (client) in `layout.tsx`: `g`+`d` → `/`, `g`+`l` → `/prospects`, `g`+`p` → `/pipeline`, `g`+`o` → `/outreach`, `g`+`x` → `/discover`, `?` toggles a shortcut-list dialog (Esc closes, focus returns to trigger). Exposes `useShortcut(key: string, handler: () => void, deps)` for page-level keys. Ignores events from editable targets and any event with Ctrl/Meta/Alt.
- Nav items: Dashboard, Leads (`/prospects`), Pipeline (`/pipeline`), Discover, Outreach. Footer of the sidebar: Gmail status dot (live) or "Demo" (demo), and a "Keyboard shortcuts" button.

- [ ] Build the sidebar (≥1024px, 224px wide, sticky, active item = survey text + 2px survey bar) and mobile bar (<1024px, menu button opens a left drawer with the same items; Esc and backdrop close; focus trapped).
- [ ] Add a "Skip to content" link targeting `<main id="main">`; main is `max-w-[1200px]`, gutters 16 / 24 / 32px.
- [ ] Verify: at 375px no horizontal scroll (`document.documentElement.scrollWidth === 375` via browser_evaluate); keyboard-only you can reach every nav item; pressing `g` then `l` navigates; typing `gl` in a focused input does not.
- [ ] Commit: `style(frontend): new sidebar shell, page header, demo notice and shortcuts`

### Task 3: Dashboard
Skills: frontend-design, ui-ux-pro-max.

**Files:**
- Modify: `frontend/app/page.tsx`
- Create: `frontend/lib/fetch-all.ts`, `frontend/components/pipeline/phase-summary.tsx`

**Interfaces:**
- `fetchAllBusinesses(params?: Omit<ListBusinessesParams, "limit" | "offset">): Promise<BusinessListItem[]>`: loops `api.listBusinesses` with `limit: 200` and increasing `offset` until `offset >= total`.
- `PhaseSummary({ businesses: BusinessListItem[] })`: five phases with counts, each linking to `/pipeline#<phase>`.

- [ ] Split the page into `LiveDashboard` and `DemoLanding` components so no hook runs after a conditional return.
- [ ] Delete the three `className="hidden"` cards and their state (approval queue, outreach results, batches). Batch controls move to Outreach in Task 7.
- [ ] Live layout: PageHeader ("Today" title, one primary action "Find leads"); attention row (drafts to review, ready to send, replies, strong opportunities) as linked figures; RadialGauge beside it; PhaseSummary from `fetchAllBusinesses`; Top opportunities table; Gmail activity list with the existing `activityLabel` wording.
- [ ] Demo landing: replace the four-tile grid with one editorial introduction (what ProspectOS does, in three short plain sentences) and a single sample lead preview showing grade + stage track, linking to the leads list. Real demo data only (the highest-scoring item from `api.listBusinesses({ limit: 200 })`, which demo mode allows); no invented figures.
- [ ] Error state names the problem and the fix in plain words; do not show `localhost` unless `NEXT_PUBLIC_API_BASE_URL` is unset in dev.
- [ ] Verify live + demo at both widths; commit: `style(frontend): redesign dashboard and demo landing`

### Task 4: Leads list
Skills: desktop-principles, ui-ux-pro-max.

**Files:**
- Modify: `frontend/app/prospects/page.tsx`
- Create: `frontend/components/ui/menu.tsx`, `frontend/components/ui/confirm-dialog.tsx`, `frontend/components/leads/leads-table.tsx`, `frontend/components/leads/selection-bar.tsx`

**Interfaces:**
- `Menu({ label: string; items: { label: string; onSelect: () => void; tone?: "danger" }[] })`: button with `aria-haspopup="menu"`, arrow-key navigation, Esc and outside click close, focus returns to the button.
- `useConfirm(): (opts: { title: string; body: string; confirmLabel: string; tone?: "danger" }) => Promise<boolean>` with a `ConfirmProvider` in `layout.tsx`; replaces every `confirm()` in the app (Tasks 4, 5, 7 use it).
- `LeadsTable({ items, selected, onToggle, onToggleAll, sortBy, sortDir, onSort, onDelete, demo })`.

- [ ] Sortable column headers for the existing `sort_by` values (name, city, category, created_at) with `aria-sort`; click toggles direction. Remove the Sort by and Direction dropdowns and the Apply button; filters apply 300ms after typing stops.
- [ ] Columns: Lead (serif name, category and city as two separate lines), Website ("Has website" link with the host as text, "Social only", or "No website"), Quality, Opportunity, Stage, row Menu. Drop the duplicate Category and City columns.
- [ ] Keyboard: `/` focuses search, `j`/`k` move a visible row highlight (`aria-selected` on the row), `Enter` opens, `x` toggles selection (live mode only).
- [ ] Pagination shows "Page 2 of 7" with Previous and Next.
- [ ] Below 768px rows collapse to a two-line list (name + grade, stage) instead of a 720px scrolling table.
- [ ] Verify sorting changes the request (network tab via browser_network_requests), shortcuts, demo hides select/import/delete; commit: `style(frontend): redesign leads table with sorting, keyboard nav and menus`

### Task 5: Lead detail
Skills: frontend-design, desktop-principles.

**Files:**
- Modify: `frontend/app/prospects/[id]/page.tsx` (split into the files below; the page keeps data loading and handlers)
- Create: `frontend/components/lead/{lead-header,score-grade,stage-track,overview-tab,audit-tab,outreach-tab,activity-tab,documents-tab}.tsx`

**Interfaces:**
- `ScoreGrade({ score: number | null; label: string })`: 40px serif numeral + SignalMeter + word ("Strong", "Moderate", "Low" at the existing 70/40 thresholds).
- `StageTrack({ status: string | null })`: 13 progress stages drawn as connected dots grouped by phase, current stage marked, label under it; outcomes shown as an end cap. `role="img"` with `aria-label="Stage: <label>, step N of 13"`.
- Tab state reads and writes `?tab=overview|audit|outreach|activity|documents` with `router.replace` (default overview).

- [ ] Fix the tab bug: each tab renders only its own content. Overview = contact details + scores summary + recommended approach. Audit = latest audit, sub-scores, reasons, screenshots. Status history appears only in Activity.
- [ ] Header: back link, serif name, location line, ScoreGrade, StageTrack, primary action (Generate outreach / View draft preview), secondary (Run audit), Menu with Delete (live only, via `useConfirm`).
- [ ] Status change (live only) moves into the header as a "Move to" Menu listing `LEAD_STATUSES` labels, with an optional note field in a small popover; uses the existing `api.changeStatus`.
- [ ] Replace both `confirm()` calls (send, delete) with `useConfirm`; the send dialog keeps the "cannot be unsent" wording.
- [ ] Verify each tab via `?tab=` deep link, demo mode (no Move to, no Delete, no notes form), 375px; commit: `style(frontend): redesign lead detail with grade, stage track and working tabs`

### Task 6: Pipeline page
Skills: frontend-design, desktop-principles.

**Files:**
- Create: `frontend/app/pipeline/page.tsx`, `frontend/components/pipeline/phase-column.tsx`

**Interfaces:**
- Consumes `fetchAllBusinesses` (Task 3), `PHASES`/`phaseOf`/`stageLabel` (Task 1), `Menu` (Task 4), `StatusBadge`.
- `PhaseColumn({ phase: Phase; leads: BusinessListItem[]; demo: boolean; onMove(id: string, status: LeadStatus): Promise<void> })`.

- [ ] Five columns at ≥1280px (each with `id` = phase for `/pipeline#research` links), stacked sections below. Each lead is a compact row (serif name, stage label, opportunity meter), not a card tile. Column header shows count; empty column says what moves a lead into it.
- [ ] Live mode: each row has a "Move to" Menu calling `api.changeStatus`; on success the row moves to its new column without a full reload. Demo mode: no menu.
- [ ] Verify with >200 leads: seed local SQLite through the existing CLI or API (`POST /api/businesses` in a scratchpad loop; local dev DB only, never Supabase) and confirm the column totals equal `total` from `listBusinesses`. Delete the seeded rows afterward.
- [ ] Commit: `feat(frontend): add pipeline page grouped by phase`

### Task 7: Outreach and Discover
Skills: frontend-design, desktop-principles.

**Files:**
- Modify: `frontend/app/outreach/page.tsx`, `frontend/app/discover/page.tsx`, `frontend/components/map-picker.tsx` (marker/circle colors from tokens)
- Create: `frontend/components/outreach/{approval-queue,batch-list,activity-feed}.tsx`, `frontend/lib/activity.ts` (move `activityLabel`/`activityTone` here from `app/page.tsx`)

- [ ] Rewrite the outreach page as readable components: summary figures, approval queue (selection only for APPROVED drafts, batch name + "Create batch"), batch list (dispatch / pause / resume / cancel via existing endpoints, cancel through `useConfirm`, refresh state instead of `location.reload()`), activity feed using `activityLabel`. Show a retryable error when loading fails.
- [ ] Approval rules stay exactly as they are: only APPROVED drafts are selectable; dispatch relies on the backend's limits and send windows; no new send path.
- [ ] Discover: split into `DemoDiscover` and `LiveDiscover` to fix the hooks order; mode switch as a segmented control; restyle the search form and results table with the Task 4 table and Checkbox; quick picks as tags.
- [ ] Verify live create-batch flow against local SQLite only, demo pages, both widths; commit: `style(frontend): redesign outreach and discover`

### Task 8: Empty, loading and error states
Skills: ui-ux-pro-max, frontend-design.

**Files:**
- Create: `frontend/components/ui/{skeleton,empty-state,error-state,toast}.tsx`; Modify: every page touched above.

**Interfaces:**
- `Skeleton({ className })`: sheet-colored block with a 1.2s opacity pulse (static under reduced motion).
- `EmptyState({ title: string; body: string; action?: ReactNode })`.
- `ErrorState({ title: string; body: string; onRetry?: () => void })` with `role="alert"`.
- `useToast(): (message: string, tone?: "success" | "error") => void`, `aria-live="polite"`, 4s auto-dismiss; replaces the inline green/red status lines (import, audit, save results).

- [ ] Replace every "Loading…" with a skeleton shaped like the content (table rows, header block), every gray empty sentence with `EmptyState` including a next action, and every red error line with `ErrorState` or a toast.
- [ ] Verify by stopping the backend (error states), using an empty local DB (empty states), and throttling network in Playwright (skeletons); commit: `style(frontend): consistent empty, loading and error states`

### Task 9: Motion pass and signature moments
Skills: motion-design, motion-principles, framer-motion, cast, animation-performance.

**Files:**
- Create: `frontend/app/template.tsx`, `frontend/components/motion/motion-root.tsx`
- Modify: `stage-track.tsx`, `score-grade.tsx`, `phase-column.tsx`, `menu.tsx`, `confirm-dialog.tsx`, `toast.tsx`, `mobile-bar.tsx`, `selection-bar.tsx`

- [ ] `MotionRoot` wraps the app in `<MotionConfig reducedMotion="user" transition={{ duration: DURATION.base, ease: EASE }}>`.
- [ ] Route change: `template.tsx` fades content in (opacity 0→1, y 4→0, `base`). No exit animation on routes.
- [ ] Overlays (menu, dialog, drawer, toast, selection bar): `AnimatePresence` enter at `base`, exit at `exit(base)`; menus scale from 0.98 at their trigger origin.
- [ ] Signature 1, score reveal: when an audit finishes on the lead page, the numeral counts from the previous score to the new one over 600ms and the meter ticks fill left to right (40ms stagger). Only after a user-triggered audit, never on page load.
- [ ] Signature 2, stage change: the StageTrack marker is a `layoutId` element that slides to the new stage (`slow`); on the Pipeline page the row uses `layout` to move between columns.
- [ ] Performance check: Playwright trace (or Chrome performance via `browser_run_code_unsafe` with `performance.measure`) during stage change and score reveal shows no forced layout and no frame over 16ms; only transform/opacity animate. With `browser_emulate_media({ reducedMotion: "reduce" })` both signatures show the final state immediately.
- [ ] Commit: `feat(frontend): motion pass with score reveal and stage marker`

### Task 10: Paint audit, rules review and demo-landing SEO
Skills: paint (design-audit phase), seo-audit; agent `rules-reviewer`.

**Files:**
- Modify: `frontend/app/layout.tsx` (metadata), create `frontend/app/robots.ts`, `frontend/app/sitemap.ts`, `frontend/app/opengraph-image.tsx` (only if the SEO audit calls for them)

- [ ] Run the paint audit checklist (reduced motion, exits, no layout animation, focus visible, five states, token-only colors, contrast ≥4.5:1, no clickable divs, 375/768/1024/1440 widths). Grep for rogue values: `rg "emerald-|amber-|red-|slate-|sky-|indigo-|purple-|fuchsia-|#[0-9A-Fa-f]{3,6}|font-mono" frontend/app frontend/components` → only token definitions remain.
- [ ] Run `rules-reviewer` on the diff; fix anything it flags.
- [ ] SEO audit of the demo landing only: title, description, canonical, Open Graph, robots for the demo build; app pages beyond the landing stay `noindex` in demo builds.
- [ ] Final tsc + build + screenshots of every page in both modes; report findings by severity.
- [ ] Commit: `chore(frontend): design audit fixes and demo landing SEO`
