"""Plain-text templates for the documents sent once a prospect says yes:
a Service Agreement, an NDA, and a Welcome Packet.

These are starting-point templates, not legal advice -- standard freelance/
small-studio clauses (deposit terms, IP transfer on final payment,
liability limitation, dispute resolution, force majeure, termination,
confidentiality). Reviewed once via the `commercial-legal` plugin --
see docs/legal/service-agreement-review.md for the full memo and what's
still open (notably: Section 11's governing-law placeholder must be filled
in with your real jurisdiction before this is send-ready, and a real
lawyer should review the finished version once before it's used on an
actual signed deal).
"""

from datetime import date


def _fmt_money(amount: float | None, currency: str) -> str:
    if amount is None:
        return "[TOTAL PROJECT FEE TO BE FILLED IN]"
    return f"{amount:,.2f} {currency}"


def render_service_agreement(
    business_name: str,
    studio_name: str,
    sender_name: str | None,
    sender_title: str | None,
    sender_email: str | None,
    project_description: str | None,
    price_amount: float | None,
    currency: str,
    deposit_percent: int,
) -> str:
    today = date.today().isoformat()
    scope = project_description or "[SCOPE OF WORK TO BE FILLED IN -- describe deliverables, e.g. 'a 5-page marketing website with an integrated AI chatbot']"
    fee = _fmt_money(price_amount, currency)
    deposit = _fmt_money(price_amount * deposit_percent / 100, currency) if price_amount is not None else "[DEPOSIT AMOUNT]"
    rep_name = sender_name or "[STUDIO REPRESENTATIVE NAME]"
    rep_title = f" ({sender_title})" if sender_title else ""
    rep_contact = f" — {sender_email}" if sender_email else ""

    return f"""SERVICE AGREEMENT

Effective Date: {today}

Between:
  {studio_name} ("Studio"), represented by {rep_name}{rep_title}{rep_contact}
and:
  {business_name} ("Client")

1. SCOPE OF WORK
   Studio will provide the following services to Client:
   {scope}

   Any work outside this scope (additional pages, features, or revision
   rounds beyond what's agreed below) will be quoted separately and
   requires Client's written approval before work begins.

2. FEES AND PAYMENT
   Total project fee: {fee}
   Deposit ({deposit_percent}% of total, due before work begins): {deposit}
   Remaining balance is due upon completion, before final deliverables
   (source files, credentials, deployed site) are handed over.
   Late payments beyond 14 days of the due date accrue a late fee of 1.5%
   per month (or the maximum allowed by law, if lower) and may cause
   Studio to pause work until resolved. If payment remains outstanding
   more than 30 days past the due date, Studio may terminate this
   agreement under Section 8.

3. TIMELINE AND REVISIONS
   Studio will provide an estimated timeline once the scope above is
   finalized. Client is entitled to two rounds of revisions per
   deliverable; additional rounds may incur extra cost.

4. OWNERSHIP AND INTELLECTUAL PROPERTY
   Upon receipt of final payment in full, all custom code, designs, and
   content created specifically for this project transfer to Client.
   Studio retains the right to reuse general methods, non-client-specific
   code, and to list this project in its portfolio unless Client requests
   otherwise in writing.

5. CONFIDENTIALITY
   Both parties agree to keep confidential any non-public business
   information shared during this engagement (e.g. credentials, internal
   data, business plans), and to use it only for the purposes of this
   project.

6. WARRANTIES AND LIMITATION OF LIABILITY
   Studio will perform services in a professional manner consistent with
   industry standards. Except as expressly stated in this Section, Studio
   makes no other warranties, express or implied, including any implied
   warranty of merchantability or fitness for a particular purpose.
   Studio's total liability under this agreement is limited to the amount
   actually paid by Client, except for (a) breaches of the confidentiality
   obligations in Section 5, (b) claims arising from Studio's gross
   negligence or willful misconduct, and (c) amounts owed under Section 2
   (Fees and Payment). Studio is not liable for indirect, incidental, or
   consequential damages (e.g. lost profits, lost business opportunities)
   arising from this engagement.

7. INDEPENDENT CONTRACTOR; SUBCONTRACTING; ASSIGNMENT
   Studio is an independent contractor, not an employee, agent, or partner
   of Client. Nothing in this agreement creates an employment relationship.
   Studio may use employees, contractors, or subcontractors to perform the
   services, and remains responsible for their work. Neither party may
   assign this agreement without the other's written consent, except that
   Client may assign it in connection with a sale of substantially all of
   its business.

8. TERMINATION
   Either party may terminate this agreement with 14 days' written notice.
   Client is responsible for payment for all work completed up to the
   termination date, including a pro-rated share of the deposit for work
   already performed.

9. FORCE MAJEURE
   Neither party is liable for delay or failure to perform due to causes
   beyond its reasonable control, including illness, natural disaster,
   internet or infrastructure outages, or governmental action. The
   affected party will notify the other promptly and resume performance
   as soon as reasonably possible.

10. DISPUTE RESOLUTION
    Before initiating any formal legal action, both parties agree to
    attempt to resolve any dispute through good-faith negotiation for at
    least 14 days. If unresolved, disputes will be resolved in the small
    claims court of the jurisdiction named in Section 11, for claims
    within that court's monetary limit, or otherwise by binding
    arbitration or litigation in that jurisdiction.

11. GOVERNING LAW
    [GOVERNING LAW / JURISDICTION TO BE FILLED IN]

12. GENERAL
    This agreement is the entire agreement between the parties on this
    subject and supersedes any prior discussions or agreements. If any
    provision is found unenforceable, the remaining provisions stay in
    effect. Failing to enforce a right under this agreement on one
    occasion does not waive that right for the future. Notices under this
    agreement should be sent to the email addresses on file for each
    party's representative.

Signatures:

_____________________________          _____________________________
{rep_name}, {studio_name}                {business_name}
Date: ______________                     Date: ______________
"""


def render_nda(
    business_name: str,
    studio_name: str,
    sender_name: str | None,
) -> str:
    today = date.today().isoformat()
    rep_name = sender_name or "[STUDIO REPRESENTATIVE NAME]"

    return f"""MUTUAL NON-DISCLOSURE AGREEMENT

Effective Date: {today}

Between:
  {studio_name} ("Studio"), represented by {rep_name}
and:
  {business_name} ("Business")

1. PURPOSE
   The parties wish to discuss a potential working relationship (website
   development, AI automation, or related services) and may exchange
   confidential information for that purpose.

2. CONFIDENTIAL INFORMATION
   Any non-public information disclosed by either party, whether written,
   oral, or observed, including business plans, financial information,
   customer data, technical designs, and login credentials.

3. OBLIGATIONS
   Each party agrees to:
   - Use the other party's confidential information solely to evaluate or
     carry out the potential engagement.
   - Not disclose it to any third party without prior written consent.
   - Protect it with at least the same care used to protect its own
     confidential information.

4. EXCLUSIONS
   This agreement does not apply to information that is already public,
   already known to the receiving party without obligation of
   confidentiality, or independently developed without reference to the
   disclosing party's confidential information.

5. TERM
   These obligations remain in effect for 2 years from the Effective Date,
   or until the information becomes public through no fault of the
   receiving party.

6. NO OBLIGATION TO PROCEED
   Nothing in this agreement obligates either party to enter into a
   further business relationship.

Signatures:

_____________________________          _____________________________
{rep_name}, {studio_name}                {business_name}
Date: ______________                     Date: ______________
"""


def render_welcome_packet(
    business_name: str,
    studio_name: str,
    sender_name: str | None,
    sender_title: str | None,
    sender_email: str | None,
    sender_phone: str | None,
    sender_portfolio_url: str | None,
    project_description: str | None,
) -> str:
    rep_name = sender_name or "your point of contact"
    rep_title = f", {sender_title}" if sender_title else ""
    scope = project_description or "the project we discussed"

    contact_lines = []
    if sender_email:
        contact_lines.append(f"Email: {sender_email}")
    if sender_phone:
        contact_lines.append(f"Phone: {sender_phone}")
    if sender_portfolio_url:
        contact_lines.append(f"Portfolio: {sender_portfolio_url}")
    contact_block = "\n".join(contact_lines) if contact_lines else "(contact details to follow)"

    return f"""Welcome to {studio_name}, {business_name}!

We're genuinely glad to be working with you on {scope}. Here's what
happens next.

YOUR POINT OF CONTACT
{rep_name}{rep_title}
{contact_block}

WHAT HAPPENS NEXT
1. Kickoff — a short call to confirm scope, timeline, and what we need
   from you (see below).
2. Build — we'll share progress at each major milestone so you're never
   waiting in the dark.
3. Review — you'll get two rounds of revisions to make sure it's right.
4. Launch — once approved and final payment is received, we hand over
   everything (source, credentials, a walkthrough of how it works).

WHAT WE NEED FROM YOU
- Any existing brand assets (logo, colors, photos) you'd like used.
- Access to your domain/hosting if you already have one (or we'll help
  you set one up).
- Key content: business hours, service list, and anything you want
  visitors or the chatbot to know.
- One point of contact on your side for approvals, to keep things moving.

Questions any time — just reach out using the contact info above. Looking
forward to this one.

— {rep_name}, {studio_name}
"""
