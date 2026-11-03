# ProspectOS design system: "Assay Report"

Single source of truth for the frontend's visual layer. `app/globals.css` holds these
values as CSS variables and `tailwind.config.ts` exposes them as utilities. Components
use the utilities only: no raw Tailwind palette colors, no hex, no ad-hoc durations.
Spec: `docs/superpowers/specs/2026-11-02-ui-redesign-design.md`.

## Concept
Prospecting for opportunity the way an assay office grades ore. Every lead is a file
with a grade and an evidence trail. Calm paper, dark ink, one survey-green accent.

## Color
| Utility | Hex | Use |
|---|---|---|
| `paper` | `#F3F2EE` | app background |
| `sheet` | `#FBFAF8` | panels, tables, inputs, menus |
| `ink` | `#1C1F1D` | primary text, icons |
| `graphite` | `#5E625D` | secondary text (5.6:1 on paper) |
| `rule` | `#D9D7D0` | borders, dividers, empty meter ticks |
| `survey` | `#1E5A43` | primary action, focus, active nav, opportunity, Won |
| `survey-soft` | survey at 10% | selected rows, accent fills |
| `ochre` | `#8A5A0B` | warning: weak or average quality, needs review |
| `brick` | `#A23B2A` | error, destructive, poor or critical quality |
| `brick-soft` | brick at 8% | error and danger fills |

Text on `survey` is `sheet`. Never use color as the only signal: pair it with a word or icon.

## Type
- Serif: IBM Plex Serif 500/600 (`font-serif`). Page titles, lead names, large score numerals.
- Sans: IBM Plex Sans 400/500/600 (`font-sans`). Everything else. Numbers use `tabular-nums`.
- Scale: `text-xs` 12, `text-[13px]` 13, `text-sm` 14, `text-base` 16, `text-xl` 20, `text-[28px]` 28, `text-[40px]` 40.
- Page title: serif 28/34 medium. Section title: sans 16 semibold. Label: sans 12 medium graphite, sentence case.
- Not allowed: monospace, all-caps tracked labels, "A · B · C" meta strings, arrows appended to text.

## Space, radius, elevation
- Spacing: 4 8 12 16 24 32 48 64 (Tailwind 1 2 3 4 6 8 12 16).
- Radius: `rounded-tag` 4 (badges, tags), `rounded-control` 6 (buttons, inputs, menu items), `rounded-panel` 10 (panels, dialogs, drawers), `rounded-full` status dots only.
- Elevation: none on panels. `shadow-float` only on menus, dialogs, drawers, toasts, the selection bar.

## Components
- Button: heights 32 (`sm`) and 36 (`md`). `default` = survey fill, sheet text. `outline` = sheet fill, rule border. `ghost` = transparent. `destructive` = brick fill. Hover darkens or tints the background only.
- Input / Select / Textarea: height 36, sheet fill, rule border, survey border on focus.
- Focus ring (every interactive element): 2px survey ring, 2px offset on paper (`focus-ring` utility).
- Panel: sheet fill, rule border, `rounded-panel`, padding 16.
- Table: sheet fill, 40px rows, rule dividers, header 12px graphite medium.
- Disabled: 45% opacity, `cursor-not-allowed`, native `disabled`.

## Meaning
- Opportunity score: survey ticks; more score = more filled ticks. Word: Strong ≥70, Moderate ≥40, Low otherwise.
- Quality: the category word. Ochre for WEAK/AVERAGE, brick for POOR/CRITICAL, ink otherwise.
- Stage: dot + label. Won = survey. Lost / Not interested = graphite. Others = ink.
- Phases (`lib/stages.ts`): Research, Contact, Conversation, Closing, Outcome.

## Motion (`lib/motion.ts`)
- Durations: `fast` 120ms, `base` 180ms, `slow` 240ms. Ease `ease-assay` = `cubic-bezier(.2,.8,.2,1)`. Exit = 0.7 x enter.
- Hover: color or background only. No lift, no scale, no shadow change.
- Allowed: route fade, overlay enter/exit, and two signature moments (score reveal, stage marker).
- Forbidden: bounce, elastic, parallax, scroll reveals, gradient animation, animating width/height/top/left.
- Reduced motion: everything resolves to its final state immediately.
