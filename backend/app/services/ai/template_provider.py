import re

from app.services.ai.base import AIProvider

_ANGLE_LABELS: dict[str, str] = {
    "NEW_WEBSITE": "a first website",
    "WEBSITE_REDESIGN": "a website refresh",
    "MOBILE_IMPROVEMENT": "a mobile-friendly upgrade",
    "AI_CHATBOT": "a small on-site assistant for common questions",
    "BOOKING": "a simple way to request an appointment",
    "LEAD_CAPTURE": "a short enquiry form",
    "CONVERSION_IMPROVEMENT": "a clearer next step for interested visitors",
    "FAQ_AUTOMATION": "a simple place for common questions and answers",
    "CUSTOMER_SUPPORT_AUTOMATION": "a simple on-site support option",
    "ANALYTICS": "a clearer way to review key website actions",
    "CUSTOM_AI_AUTOMATION": "a focused automation improvement",
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

_OPENINGS = (
    "I took a quick look at {business}'s website and noticed {observation}.",
    "I came across {business}'s site and noticed {observation}.",
    "One thing that stood out when I looked at {business}'s site was that {observation}.",
)
_SUBJECTS = (
    "Quick idea for {business}",
    "Something I noticed on {business}'s site",
    "Small idea for {business}'s website",
)
_CTAS = (
    "Would you like me to put together a quick mockup and send it over?",
    "Want me to send over a quick visual of what I mean?",
    "If you'd like, I can put together a quick concept and send it over.",
)
_SALESY_LANGUAGE = re.compile(r"\b(?:boost your revenue|skyrocket|transform your business|maximize engagement|unlock growth|game-changing|revolutionary|cutting-edge|take your business to the next level|losing customers|missing out on revenue)\b", re.I)


def _variant_index(business_name: str, angle: str, count: int) -> int:
    return sum(ord(char) for char in f"{business_name}|{angle}") % count


def _polish_observation(observation: str) -> str:
    result = observation.strip().rstrip(".")
    result = re.sub(r"^visitors can browse information about ", "visitors can find things like your ", result, flags=re.I)
    result = re.sub(r"^there is not ", "there isn't ", result, flags=re.I)
    return result.replace(" directly on the site", " directly through the site")


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
        angle_label = _ANGLE_LABELS.get(angle, "a focused improvement")
        observation = _polish_observation(_humanize_observation(observations[0] if observations else None))
        variant = _variant_index(business_name, angle, len(_OPENINGS))
        subject = _SUBJECTS[variant].format(business=business_name)
        opening = _OPENINGS[variant].format(business=business_name, observation=observation)
        ideas = (
            f"I had an idea for {angle_label} that could fit naturally into the current site.",
            f"I had an idea for {angle_label} without changing the existing design.",
            f"There may be a straightforward way to add {angle_label} while keeping the current site familiar.",
        )
        body = "Hi there,\n\n" + opening + "\n\n" + ideas[variant] + "\n\n" + _CTAS[variant]
        if _SALESY_LANGUAGE.search(f"{subject}\n{body}"):
            raise ValueError("Salesy language failed the editorial quality check.")
        return subject, body

        angle_label = _ANGLE_LABELS.get(angle, "a few improvements")
        observation = _humanize_observation(observations[0] if observations else None)
        consequence = _ANGLE_CONSEQUENCES.get(
            angle, "Right now that's likely costing you visitors who'd otherwise become customers."
        )
        # Aside-clause construction avoids the plural/singular mismatch of
        # "businesses as a hospital" while still naming the category.
        proof_line = _build_social_proof_line(social_proof)

        subject = f"Quick idea for {business_name}"
        body = (
            "Hi there,\n\n"
            f"I took a quick look at {business_name}'s site and noticed {observation}.\n\n"
            f"{observations[1] if len(observations) > 1 else consequence}\n\n"
            f"{proof_line}"
            f"I had a simple idea for how {angle_label} could fit into the existing site.\n\n"
            "Want me to put together a quick mockup of what it could look like? No cost, no obligation — "
            "just reply and I'll send it over."
        )
        body = re.sub(
            r"Want me to put together.*?send it over\.",
            "Would you like me to put together a quick mockup and send it over?",
            body,
        )
        return subject, body.replace("—", " ").replace("â€”", " ")
