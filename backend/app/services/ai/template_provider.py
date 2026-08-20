import re

from app.services.ai.base import AIProvider

_ANGLE_LABELS: dict[str, str] = {
    "NEW_WEBSITE": "a first website",
    "WEBSITE_REDESIGN": "a website refresh",
    "MOBILE_IMPROVEMENT": "a mobile-friendly upgrade",
    "AI_CHATBOT": "an AI chat assistant for after-hours questions",
    "BOOKING": "online booking",
    "LEAD_CAPTURE": "a simple way to capture leads",
    "FULL_DIGITAL_UPGRADE": "a full digital upgrade",
}

# Loss-framed consequence, one per angle -- deliberately NOT a single
# generic sentence reused everywhere. The earlier version always talked
# about "a visitor outside business hours" even when the actual finding
# was e.g. a mobile-rendering problem, which reads as a non-sequitur to
# anyone who actually looks at their own site. Each of these ties the
# cost directly to the thing that angle's opportunity_type is about.
_ANGLE_CONSEQUENCES: dict[str, str] = {
    "NEW_WEBSITE": (
        "Right now anyone who searches for you online finds nothing to click on, "
        "so they call whichever competitor does show up."
    ),
    "WEBSITE_REDESIGN": (
        "Right now that's likely costing you trust in the first few seconds someone "
        "lands on the page, before they even read what you offer."
    ),
    "MOBILE_IMPROVEMENT": (
        "That means a visitor searching for you on the spot — the moment they're "
        "actually closest to calling or showing up — leaves before finding your "
        "number, hours, or what you offer."
    ),
    "AI_CHATBOT": (
        "Right now a visitor with a quick question outside business hours gets no "
        "answer at all, and most of them don't wait — they just try the next result."
    ),
    "BOOKING": (
        "Right now booking only happens by phone during business hours, which loses "
        "every customer who'd rather just tap a button at 9pm."
    ),
    "LEAD_CAPTURE": (
        "Right now an interested visitor has no easy way to leave their info, so "
        "most of them just leave and you never know they were there."
    ),
    "FULL_DIGITAL_UPGRADE": (
        "Right now these add up to a visitor experience that loses people at several "
        "different points, not just one."
    ),
}

# Rewrites the raw scorer language (app/services/scoring/scoring.py's
# opportunity_reasons) into how a business owner actually talks about
# their own site, rather than piping audit-tool jargon straight into the
# email. Regex, not exact-match, so it still survives the interpolated
# score number in the redesign reason. Order matters -- first match wins.
# Falls back to the raw text if nothing matches, so an unexpected reason
# string never breaks the draft, it's just less polished.
_OBSERVATION_REWRITES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^Website not found from available sources\.?$", re.I), "you don't have a website online right now"),
    (
        re.compile(r"^Overall website quality scored \d+/100.*$", re.I),
        "your site is showing its age compared to what customers expect these days",
    ),
    (
        re.compile(r"^No mobile viewport meta tag.*phones\.?$", re.I),
        "your site doesn't display well on a phone — and that's where most local searches happen",
    ),
    (
        re.compile(r"^Conversion elements.*losing interested visitors\.?$", re.I),
        "there's no clear way for a visitor to contact you (no contact form, phone, or email standing out)",
    ),
    (
        re.compile(r"^No visible way to capture a lead.*$", re.I),
        "there's no way for an interested visitor to leave their info",
    ),
    (
        re.compile(r"^No AI chatbot was detected.*$", re.I),
        "there's no way to get an instant answer outside business hours",
    ),
    (
        re.compile(r"^No FAQ section was found.*$", re.I),
        "there's no FAQ section, so simple questions turn into phone calls",
    ),
    (
        re.compile(r"^No online booking/scheduling option.*$", re.I),
        "there's no way to book or schedule online — everything goes through a phone call",
    ),
    (
        re.compile(r"^No live chat or AI support.*$", re.I),
        "customers have to call or email for even basic questions",
    ),
    (
        re.compile(r"^No analytics tracking.*$", re.I),
        "there's likely no visibility into how many people visit or where they drop off",
    ),
    (
        re.compile(r"^Multiple automation gaps were found together.*$", re.I),
        "a handful of these gaps showed up together, not just one",
    ),
]


def _humanize_observation(raw: str | None) -> str:
    if not raw:
        return "your website has a few areas that could be improved"
    stripped = raw.strip()
    for pattern, plain in _OBSERVATION_REWRITES:
        if pattern.match(stripped):
            return plain
    # Unknown reason text (e.g. a future scorer change) -- still usable,
    # just de-capitalized and de-punctuated so it reads as a clause.
    return stripped.rstrip(".").rstrip()[:1].lower() + stripped.rstrip(".")[1:]


# Liking/authority line built ONLY from real, verified numbers already on
# the business record (Google/OSM rating + review count) -- never a
# fabricated "customers love us" claim. Thresholds exist so a single
# fluke 5-star review or an unrated listing doesn't produce a misleading
# line; below them, this returns "" and the email simply says nothing
# about ratings rather than stretching thin data.
_MIN_RATING = 4.0
_MIN_REVIEW_COUNT = 3


def _build_social_proof_line(social_proof: dict | None) -> str:
    if not social_proof:
        return ""
    rating = social_proof.get("rating")
    review_count = social_proof.get("review_count")
    if not rating or not review_count or rating < _MIN_RATING or review_count < _MIN_REVIEW_COUNT:
        return ""
    return (
        f"With a {rating:g}-star rating from {review_count} reviews, people clearly already like what you do "
        "— I just want to make sure your site does that justice.\n\n"
    )


class TemplateProvider(AIProvider):
    """Rule-based, no-network fallback — always available, satisfies the
    "must work without Ollama" requirement (spec section 26). Uses only
    the verified observations passed in; never invents facts, never
    insults the business. Structure: Observation -> Improvement -> Benefit
    -> soft CTA (spec section 27).

    Copy is built on a deliberately narrow, honest slice of persuasion
    psychology (via the marketing-psychology skill) -- picked because this
    is real B2B outreach about a real, verified observation, not growth
    hacking:
      - Curiosity-gap subject line (specific to this business, not a
        template cliché like "Quick idea for X") instead of a generic hook.
      - Loss framing on the benefit ("a missed call/booking every time it
        happens" reads as more urgent than the equivalent gain-framed
        sentence, per prospect theory) -- still 100% grounded in the real
        observation, nothing fabricated.
      - Reciprocity + low activation energy on the CTA: offer something
        concrete and free (a mockup) rather than a vague "let's talk",
        and make the ask itself trivial (just reply).
    Explicitly NOT used: fake urgency/scarcity, fabricated social proof,
    or any dark pattern -- none of those are honest here, so they're left
    out entirely rather than faked."""

    def is_available(self) -> bool:
        return True

    def generate_outreach(
        self,
        business_name: str,
        category: str | None,
        angle: str,
        observations: list[str],
        sender: dict | None = None,
        social_proof: dict | None = None,
    ) -> tuple[str, str]:
        angle_label = _ANGLE_LABELS.get(angle, "a few improvements")
        observation = _humanize_observation(observations[0] if observations else None)
        consequence = _ANGLE_CONSEQUENCES.get(
            angle, "Right now that's likely costing you visitors who'd otherwise become customers."
        )
        # Aside-clause construction avoids the plural/singular mismatch of
        # "businesses as a hospital" while still naming the category.
        category_aside = f" — as a {category.lower()} —" if category else ""
        proof_line = _build_social_proof_line(social_proof)

        subject = f"Something I noticed on {business_name}'s site"
        body = (
            "Hi there,\n\n"
            f"I took a quick look at {business_name}'s site and noticed {observation}.\n\n"
            f"{consequence}\n\n"
            f"{proof_line}"
            f"I help local businesses like yours{category_aside} fix exactly that, usually with {angle_label}.\n\n"
            "Want me to put together a quick mockup of what it could look like? No cost, no obligation — "
            "just reply and I'll send it over."
        )
        return subject, body
