# ProspectOS UI Redesign: "Assay Report"

Status: direction approved 2026-11-02. Frontend only.

## Why
ProspectOS is the owner's main portfolio piece. The current UI works but reads as
unfinished: inconsistent type and spacing, contradictory score colors, a purple status
palette, no pipeline view, a broken tab layout on the lead page, and bare
loading/empty/error states. Goal: a premium, hand-made feel without generic AI-dashboard
tells (default shadcn look, purple gradients, emoji icons, cookie-cutter card grids).

## Concept
The product prospects for opportunity the way an assay office grades ore. Each lead is
a file with a grade and an evidence trail. The visual vernacular is the field survey book
and assay certificate, not a magazine or a SaaS kit.

## Visual thesis
Warm stone-paper background with green-tinted near-black ink and a single deep
survey-green accent. IBM Plex Serif for page titles, business names and large score
numerals; IBM Plex Sans with tabular figures for everything else. Dense 4px-based
spacing. Small hierarchy-based radii; panels are filled sheets on paper. No card shadows.

## Interaction thesis
Fast and dry: 120-240ms, ease-out, exits about 30% faster than entrances. Hover changes
color or background only (no lift, no scale). No scroll reveals inside the app.
Keyboard-first. Exactly two signature moments: the score reveal after an audit and the
stage marker sliding along the pipeline track. Forbidden: bounce/elastic, parallax,
staggered fade-ins on every section, gradients, animating width/height/top/left.
`prefers-reduced-motion` reduces all motion to opacity or nothing.

## Tokens (canonical copy lives in `frontend/MASTER.md`)
| Token | Value | Use |
|---|---|---|
| paper | `#F3F2EE` | app background |
| sheet | `#FBFAF8` | panels, tables, inputs |
| ink | `#1C1F1D` | primary text |
| graphite | `#5E625D` | secondary text (5.6:1 on paper) |
| rule | `#D9D7D0` | borders, dividers |
| survey | `#1E5A43` | accent: primary actions, focus, active nav, opportunity |
| ochre | `#8A5A0B` | warning (5.3:1) |
| brick | `#A23B2A` | error and destructive only |

- Type scale (px): 12 / 13 / 14 / 16 / 20 / 28 / 40. Labels are 12px sans, sentence case.
  No mono font, no all-caps tracked labels, no "A · B · C" meta strings.
- Spacing: 4 8 12 16 24 32 48 64. Table rows 40px.
- Radius: 4 tags, 6 controls, 10 panels/dialogs, full for status dots only.
- Elevation: shadows only on floating layers (menu, dialog, selection bar, toast).
- Motion: `fast` 120ms, `base` 180ms, `slow` 240ms; ease `cubic-bezier(.2,.8,.2,1)`;
  exit = 0.7 x enter.

## Meaning rules
- Opportunity: one survey-green scale; more ink = more opportunity.
- Quality: shown as a word; ochre for WEAK/AVERAGE, brick for POOR/CRITICAL, plain ink otherwise.
- Lead stages: the 16 `LEAD_STATUSES` group into 5 frontend-only phases:
  Research (NEW, AUDITED, QUALIFIED, OUTREACH_READY), Contact (CONTACTED, FOLLOW_UP),
  Conversation (REPLIED, INTERESTED, CONCEPT_SENT, DISCUSSION),
  Closing (DEMO_SENT, CALL_BOOKED, PROPOSAL), Outcome (WON, LOST, NOT_INTERESTED).
  A null status is NEW. An unrecognized status lands in Research and shows its raw label.
  WON uses survey green; LOST and NOT_INTERESTED use graphite.

## Scope
Shell (sidebar ≥1024px, top bar + drawer below), dashboard, leads list, lead detail,
new Pipeline page (`/pipeline`), outreach, discover, shared empty/loading/error states,
motion pass, final paint audit, SEO for the public demo landing only.

## Non-goals and constraints
- No backend logic or API contract changes. The pipeline pages through `GET /api/businesses`
  (max 200 per call) and groups on the client.
- Demo mode keeps working: every mutation control stays hidden or disabled when
  `isDemoMode`; the backend `enforce_demo_mode` remains the boundary.
- No drag-and-drop stage changes (keyboard-accessible "Move to" menu only, live mode only).
- The only new dependency is `framer-motion@^11.18.2` (approved).
- The owner runs all git commands; each phase ends with a suggested commit message.
