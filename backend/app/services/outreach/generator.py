import re

from app.services.ai.base import AIProvider
from app.services.ai.ollama_provider import OllamaProvider
from app.services.ai.template_provider import TemplateProvider

# Maps an opportunity_type (from scoring) to the outreach angle that best
# fits it (spec section 28 defines the OutreachAngle set). First match in
# opportunity_types (already priority-ordered by the scorer) wins.
_OPPORTUNITY_TO_ANGLE: dict[str, str] = {
    "NO_WEBSITE": "NEW_WEBSITE",
    "WEBSITE_REDESIGN": "WEBSITE_REDESIGN",
    "MOBILE_IMPROVEMENT": "MOBILE_IMPROVEMENT",
    "AI_CHATBOT": "AI_CHATBOT",
    "BOOKING_AUTOMATION": "BOOKING",
    "LEAD_CAPTURE": "LEAD_CAPTURE",
    "CONVERSION_IMPROVEMENT": "CONVERSION_IMPROVEMENT",
    "FAQ_AUTOMATION": "FAQ_AUTOMATION",
    "CUSTOMER_SUPPORT_AUTOMATION": "CUSTOMER_SUPPORT_AUTOMATION",
    "ANALYTICS": "ANALYTICS",
    "CUSTOM_AI_AUTOMATION": "CUSTOM_AI_AUTOMATION",
    "FULL_DIGITAL_UPGRADE": "FULL_DIGITAL_UPGRADE",
}

_BANNED_OUTREACH_LANGUAGE = re.compile(
    r"\b(?:was detected|was not detected|crawled(?: pages)?|our audit|website score|scanner found|"
    r"crawler found|opportunity score|technical analysis|confidence score|\bDOM\b)\b", re.IGNORECASE
)


def has_internal_audit_language(text: str) -> bool:
    return bool(_BANNED_OUTREACH_LANGUAGE.search(text))


def needs_editorial_rewrite(text: str) -> bool:
    if has_internal_audit_language(text):
        return True
    sentences = [set(re.findall(r"[a-z]{4,}", sentence.lower())) for sentence in re.split(r"[.!?]+", text)]
    sentences = [words for words in sentences if words]
    for index, words in enumerate(sentences[:-1]):
        following = sentences[index + 1]
        if len(words) >= 4 and len(following) >= 4 and len(words & following) / min(len(words), len(following)) >= 0.7:
            return True
    return False


def customer_facing_observation(assessment: dict | None) -> str | None:
    """The sole bridge from internal opportunity data to email language.
    Future opportunity types work as long as they provide an interpretation
    or customer-facing observation; raw evidence is intentionally never a
    fallback for an email."""
    if not assessment:
        return None
    observation = assessment.get("outreach_observation") or assessment.get("business_interpretation")
    if not observation or has_internal_audit_language(observation):
        return None
    return observation.strip()


def pick_angle(opportunity_types: list[str]) -> str:
    for opportunity_type in opportunity_types:
        if opportunity_type in _OPPORTUNITY_TO_ANGLE:
            return _OPPORTUNITY_TO_ANGLE[opportunity_type]
    return "FULL_DIGITAL_UPGRADE"


def pick_primary_angle(opportunity_assessments: list[dict] | None) -> str | None:
    """Auto-pick only a credible primary recommendation, never the first
    broadly detected missing feature."""
    for item in opportunity_assessments or []:
        if item.get("classification") == "PRIMARY":
            return _OPPORTUNITY_TO_ANGLE.get(item.get("opportunity_type", ""), item.get("opportunity_type"))
    return None


def _reorder_reasons_for_angle(
    angle: str, opportunity_types: list[str], opportunity_reasons: list[str]
) -> list[str]:
    """opportunity_types and opportunity_reasons are parallel lists (same
    index = same finding). When the angle is auto-picked, reasons[0]
    always matches it by construction. But the "Angle" dropdown lets the
    user override the angle -- and without this, the draft would still
    lead with reasons[0], which could be a completely different finding
    than the one the chosen angle is actually about (e.g. angle=AI_CHATBOT
    but the observation talks about mobile rendering). This puts whichever
    reason actually corresponds to the chosen angle first."""
    for opportunity_type, reason in zip(opportunity_types, opportunity_reasons):
        if _OPPORTUNITY_TO_ANGLE.get(opportunity_type) == angle:
            reordered = [reason] + [r for r in opportunity_reasons if r != reason]
            return reordered
    return opportunity_reasons


def get_ai_provider(ollama_base_url: str, ollama_model: str) -> tuple[AIProvider, str]:
    """Prefers a locally running Ollama model; falls back to the always-
    available TemplateProvider (spec section 26: must work with zero AI
    installed, no paid AI APIs)."""
    ollama = OllamaProvider(base_url=ollama_base_url, model=ollama_model)
    if ollama.is_available():
        return ollama, "ollama"
    return TemplateProvider(), "template"


def _build_signature(sender: dict | None) -> str:
    """A signature block is the difference between a draft that looks like
    a real person sent it and one that ends at "Best," with nothing after
    -- the single biggest credibility gap in cold outreach. Falls back to
    a bare "Best," (previous behavior) if no sender was picked."""
    if not sender or not sender.get("name"):
        return "Best,"

    lines = ["Best,", sender["name"]]
    if sender.get("title"):
        title = sender["title"]
        lines.append(title if title.isupper() else title.title())
    # Prefer a portfolio link (stronger credibility signal) over a bare
    # email in the signature; email is still usable via reply-to either way.
    contact = sender.get("portfolio_url") or sender.get("email")
    if contact:
        lines.append(contact)
    if sender.get("phone"):
        lines.append(sender["phone"])
    return "\n".join(lines)


def generate_outreach_draft(
    business_name: str,
    category: str | None,
    opportunity_types: list[str],
    opportunity_reasons: list[str],
    angle: str | None = None,
    provider: AIProvider | None = None,
    generated_by: str | None = None,
    sender: dict | None = None,
    social_proof: dict | None = None,
    opportunity_assessments: list[dict] | None = None,
) -> dict:
    """Builds one outreach draft. Always creates fresh output — callers
    persist this as a new Outreach row rather than overwriting a previous
    draft, so "Regenerate Outreach" keeps history (spec section 36).

    `sender`, if given (dict with name/title/email/phone/portfolio_url),
    identifies which teammate is sending this one — their signature is
    appended after whatever the provider writes, so the same real identity
    shows up regardless of which provider (template or Ollama) generated
    the body.

    `social_proof`, if given (dict with rating/review_count), lets the
    provider optionally cite the business's own real rating as a liking
    cue -- never fabricated, and silently skipped when absent or thin."""

    primary = next((item for item in (opportunity_assessments or []) if item.get("classification") == "PRIMARY"), None)
    resolved_angle = angle or pick_primary_angle(opportunity_assessments) or pick_angle(opportunity_types)
    selected_assessment = primary if not angle else next(
        (item for item in (opportunity_assessments or []) if _OPPORTUNITY_TO_ANGLE.get(item.get("opportunity_type", "")) == resolved_angle),
        None,
    )

    if provider is None:
        from app.database.config import get_settings

        settings = get_settings()
        provider, generated_by = get_ai_provider(settings.ollama_base_url, settings.ollama_model)

    ordered_reasons = _reorder_reasons_for_angle(resolved_angle, opportunity_types, opportunity_reasons)
    observation = customer_facing_observation(selected_assessment)
    if selected_assessment and observation:
        possible_impact = selected_assessment.get("possible_impact") or selected_assessment.get("business_interpretation")
        if not possible_impact or has_internal_audit_language(possible_impact):
            raise ValueError("This opportunity has no safe, evidence-based business interpretation.")
        ordered_reasons = [observation, possible_impact]
    elif has_internal_audit_language(" ".join(ordered_reasons)):
        raise ValueError("This opportunity has no safe customer-facing observation. Re-audit or select a different angle.")
    subject, body = provider.generate_outreach(
        business_name, category, resolved_angle, ordered_reasons, sender=sender, social_proof=social_proof
    )
    # An LLM must never be allowed to leak internal audit terminology. The
    # deterministic provider receives only the customer-facing translation.
    if needs_editorial_rewrite(f"{subject}\n{body}"):
        subject, body = TemplateProvider().generate_outreach(
            business_name, category, resolved_angle, ordered_reasons, sender=sender, social_proof=social_proof
        )
    full_body = f"{body.rstrip()}\n\n{_build_signature(sender)}"

    return {
        "angle": resolved_angle,
        "subject": subject,
        "body": full_body,
        "generated_by": generated_by or "template",
    }
