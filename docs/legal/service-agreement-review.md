# Vendor Agreement Review: ProspectOS Service Agreement Template (Self-Authored Draft)

RESEARCH NOTES — NOT LEGAL ADVICE — REVIEW WITH A LICENSED ATTORNEY,
SOLICITOR, BARRISTER, OR OTHER AUTHORISED LEGAL PROFESSIONAL IN YOUR
JURISDICTION BEFORE ACTING

**Reviewed:** 2026-08-20
**Reviewer:** commercial-legal plugin (quick-path playbook, `[PROVISIONAL — several playbook fields not yet filled in]`)
**Document:** `backend/app/services/contracts/templates.py::render_service_agreement`
**Our role:** Sales-side (Studio = vendor, this is our own paper)

---

## Bottom line

This is a reasonable starting skeleton — it has the core commercial terms
(scope, fee, deposit, IP transfer, liability cap, termination) and doesn't
contain anything actively dangerous. It is **not send-ready as-is**: it's
missing several standard boilerplate clauses whose absence creates real risk
for a solo studio specifically (no dispute-resolution mechanism, no force
majeure, no warranty disclaimer beyond liability cap, no assignment clause),
and Section 9 (Governing Law) is a live placeholder that must be filled in
per your actual jurisdiction before this is usable at all.

**Issues (legal risk):** 0🔴 3🟠 4🟡 2🟢

---

## Deal-breaker check

✅ Clear — no "one thing" deal-breaker configured yet in the playbook to
check against (marked `[PENDING]`). Recommend deciding this and adding it
to `CLAUDE.md` before the first real negotiation, so future reviews can
check it automatically.

---

## Issues by severity

### §9: Governing Law — unfilled placeholder

**Playbook says:** `[PENDING]` — not yet decided.

**Contract says:**
> "[GOVERNING LAW / JURISDICTION TO BE FILLED IN]"

**Gap:** Missing term (literally, not just underspecified — this is a
bracketed placeholder in the template).

**Legal risk:** 🟠 High
**Business friction:** 🟠 Slows deals

**Why it matters:** Without a governing-law clause, if a dispute happens,
which state/country's law applies becomes its own fight — exactly the kind
of expensive uncertainty this clause exists to prevent. This is also the
clause every other jurisdiction-dependent analysis in this memo (liability
exclusions, indemnity, confidentiality term limits) depends on — the review
below is written jurisdiction-agnostic because this field is empty.

**Proposed fix:** Fill with your actual home state/country before ever
sending this to a client. Once picked, this whole template should be
re-reviewed for that specific jurisdiction's enforceability rules (see
"Needs a lawyer" section below) — liability exclusions and indemnity
enforceability vary meaningfully by state/country. `[jurisdiction — verify]`

**If unresolved:** Do not send this agreement out with this field still
bracketed.

---

### §6: Limitation of Liability — cap-carveout interaction not addressed

**Playbook says:** "Cap total liability at the amount actually paid by the
client... No liability for indirect, incidental, or consequential damages."

**Contract says:**
> "Studio's total liability under this agreement is limited to the amount
> actually paid by Client. Studio is not liable for indirect, incidental,
> or consequential damages..."

**Gap:** Weaker than a complete clause — matches the playbook's stated
position, but the clause doesn't address what sits *above* the cap. As
written, the cap appears to apply to everything with no carveouts at all —
which sounds protective, but most real templates carve out a few
categories (confidentiality breach, IP infringement by Studio, gross
negligence/willful misconduct) specifically because in many jurisdictions
courts are reluctant to enforce a liability cap that would excuse willful
misconduct entirely, and having zero carveouts can actually make the whole
clause more likely to be challenged rather than less.

**Legal risk:** 🟡 Medium
**Business friction:** 🟢 Invisible until it matters

**Why it matters:** An unconditional cap looks good to the studio on paper,
but a clause that tries to cap even willful misconduct or IP claims is the
kind of overreach that invites a court to strike the whole limitation
clause rather than read it narrowly. A cap with sensible, narrow carveouts
is usually *more* enforceable, not less.

**Proposed redline:**
> "...except for (a) breaches of the confidentiality obligations in Section
> 5, (b) claims arising from Studio's gross negligence or willful
> misconduct, and (c) amounts owed under Section 2 (Fees and Payment)."

**If unresolved:** Low urgency for a first small deal, but worth fixing
before this template is reused at higher project values.

---

### Missing: Dispute resolution clause

**Gap:** No mechanism specified for what happens if there's a
disagreement — no mediation/arbitration clause, no venue for litigation, no
attorneys'-fees provision.

**Legal risk:** 🟠 High
**Business friction:** 🟡 Confuses clients (and costs the studio if a real
dispute ever happens)

**Why it matters:** For a solo/small studio, going straight to litigation
over a $2,000-$5,000 project is economically absurd for both sides — legal
fees alone would exceed the contract value. A cheap, fast dispute path
(e.g., mediation first, then small-claims court or arbitration below a
dollar threshold) protects a small studio specifically, since you can't
absorb litigation costs the way a larger business could.

**Proposed addition (new §10):**
> "10. DISPUTE RESOLUTION
>    Before initiating any formal legal action, both parties agree to
>    attempt to resolve any dispute through good-faith negotiation for at
>    least 14 days. If unresolved, disputes will be resolved in the small
>    claims court of [jurisdiction], for claims within that court's
>    monetary limit, or otherwise by binding arbitration/litigation in
>    [jurisdiction] as determined by Section 9."

**If unresolved:** Medium urgency — worth adding before the template is
used for anything above a token project value.

---

### Missing: Force majeure

**Gap:** No clause excusing either party from performance due to events
outside their control (illness, natural disaster, internet/infrastructure
outage, etc.).

**Legal risk:** 🟡 Medium
**Business friction:** 🟢 Invisible until it matters

**Why it matters:** Without this, a delay caused by something genuinely
outside either party's control (you get sick for two weeks, a third-party
API/hosting provider has an extended outage) has no contractual cover — the
termination clause is the only lever either side has, which is a blunt
instrument for what's often a temporary problem.

**Proposed addition (new section):**
> "Neither party is liable for delay or failure to perform due to causes
> beyond its reasonable control, including illness, natural disaster,
> internet or infrastructure outages, or governmental action. The affected
> party will notify the other promptly and resume performance as soon as
> reasonably possible."

**If unresolved:** Low-medium urgency.

---

### Missing: Warranty disclaimer

**Gap:** Section 6 addresses liability limits but never states what
Studio does *not* warrant (e.g., that the software will be error-free, that
it will achieve any particular business result, fitness for a particular
purpose beyond what's scoped).

**Legal risk:** 🟡 Medium
**Business friction:** 🟢 Invisible until it matters

**Why it matters:** "Professional manner consistent with industry
standards" (already in §6) is a reasonable affirmative promise, but pairing
it with an explicit disclaimer of implied warranties is standard practice
and closes a gap a client's lawyer would likely flag if they ever review
this closely.

**Proposed addition (extend §6):**
> "Except as expressly stated in this Section, Studio makes no other
> warranties, express or implied, including any implied warranty of
> merchantability or fitness for a particular purpose."

**If unresolved:** Low urgency for early small deals.

---

### Missing: Assignment clause

**Gap:** Nothing addresses whether either party can transfer/assign the
agreement to someone else (e.g., if the client's business is sold, or if
the studio brings on additional contractors/subcontracts part of the
work).

**Legal risk:** 🟢 Low
**Business friction:** 🟢 Invisible until it matters

**Why it matters:** Minor for a small deal, but relevant given the
studio explicitly wants a multi-person team (per the "teammate" sender
feature already built into ProspectOS) — worth clarifying that Studio may
use subcontractors/employees to perform the work, so the Client can't later
claim the specific named representative was required to do all the work
personally.

**Proposed addition (new section):**
> "Studio may use employees, contractors, or subcontractors to perform the
> services, and remains responsible for their work. Neither party may
> assign this agreement without the other's written consent, except that
> Client may assign it in connection with a sale of substantially all of
> its business."

**If unresolved:** Low urgency.

---

### §2: Late payment — "may pause work" is vague on the remedy

**Playbook says:** No specific position recorded yet.

**Contract says:**
> "Late payments beyond 14 days of the due date may pause work until
> resolved."

**Gap:** Non-standard structure — "may pause" gives Studio discretion but
no automatic interest/late-fee mechanism, and doesn't address what happens
if payment never resolves (when can Studio treat the contract as
terminated for non-payment, versus just paused indefinitely?).

**Legal risk:** 🟢 Low
**Business friction:** 🟡 Confuses clients

**Why it matters:** For a solo studio, cash flow matters — an explicit
late fee (even a modest one) creates a real incentive to pay on time, and
an explicit "we can terminate for non-payment after X days" closes the
"paused forever" ambiguity.

**Proposed redline:**
> "Late payments beyond 14 days of the due date accrue a late fee of 1.5%
> per month (or the maximum allowed by law, if lower) and may cause Studio
> to pause work until resolved. If payment remains outstanding more than
> 30 days past the due date, Studio may terminate this agreement under
> Section 8."

**If unresolved:** Low urgency, easy fix.

---

## Favorable terms

- **§4 IP transfer timing (on final payment, not before)** — this protects
  the studio correctly; a common mistake small studios make is transferring
  IP/handing over source before being paid in full. This template already
  gets that right.
- **§8 Termination requiring payment for work completed + pro-rated deposit**
  — fair to both sides, and specifically protects the studio from a client
  canceling after most of the work is done to avoid paying the balance.
- **§1 Change-order language** ("any work outside this scope... quoted
  separately and requires Client's written approval") — this is exactly the
  kind of scope-creep protection freelancers commonly forget to include.

## Missing provisions

- Dispute resolution (flagged above, 🟠)
- Force majeure (flagged above, 🟡)
- Warranty disclaimer (flagged above, 🟡)
- Assignment / subcontracting (flagged above, 🟢)
- Entire-agreement / severability / no-waiver boilerplate — standard
  "this is the whole agreement, if one clause is unenforceable the rest
  still stands, failing to enforce a right once doesn't waive it forever"
  language. Low risk but cheap to add and closes easy gaps.
- Notice mechanism — how/where written notices (e.g. the 14-day termination
  notice) are actually delivered (email to X address? certified mail?).

---

## Approval routing

Solo/small practice — no internal approval chain (per `CLAUDE.md`
escalation section). Per the playbook's automatic-escalation triggers, none
of the issues above hit "unlimited liability" or "IP doesn't transfer" —
so nothing here requires escalation by the playbook's own rules.

**Recommended next step:** Fix the 🟠 items (governing law placeholder,
dispute resolution, cap carveouts) and the 🟡 items (force majeure, warranty
disclaimer, late-payment mechanics) directly in the template source
(`backend/app/services/contracts/templates.py`), then — per the
"Non-lawyer without attorney access" role in `CLAUDE.md` — **get a real
lawyer to review the finished version once before it's used for a deal of
any real size.** A single consult (many jurisdictions have low-cost
small-business legal clinics or a flat-fee contract review) is far cheaper
than a dispute down the line, especially for the jurisdiction-specific
questions this memo explicitly can't answer (see below).

---

## Needs a lawyer, not just this plugin

This review deliberately stayed jurisdiction-agnostic because §9 is still a
placeholder. Once you pick a governing-law jurisdiction, the following
should be specifically re-checked against that jurisdiction's actual rules
(none of these were verified against a live legal-research source — no
research connector is configured yet):

- Whether the liability-cap language as redlined is enforceable there
  (some jurisdictions restrict excluding liability for gross negligence
  even with carveout language).
- Whether a 14-day pre-litigation negotiation requirement + small-claims
  routing is standard/enforceable there, and what your local small-claims
  dollar limit actually is.
- Any local requirement for a written contract for services above a
  certain dollar amount, or specific consumer-protection rules if any
  client could be considered a "consumer" rather than a business.
- State/country-specific late-fee/interest-rate caps (usury limits) before
  finalizing the 1.5%/month late-fee redline above.

`[model knowledge — verify]` applies to every specific rule referenced
above — none of it was checked against a current legal database.

---

## Next steps

- [ ] Fill in Section 9 (Governing Law) with your real jurisdiction
- [ ] Apply the 🟠/🟡 redlines above directly to `templates.py`
- [ ] Decide the playbook's "one thing" deal-breaker and record it in
      `CLAUDE.md` (`## Playbook → Sales-side playbook → The one thing`)
- [ ] Get one real lawyer review of the finished template before using it
      on an actual signed deal
- [ ] Something else — tell me and I'll adjust
