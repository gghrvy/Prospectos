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
    "FULL_DIGITAL_UPGRADE": "FULL_DIGITAL_UPGRADE",
}


def pick_angle(opportunity_types: list[str]) -> str:
    for opportunity_type in opportunity_types:
        if opportunity_type in _OPPORTUNITY_TO_ANGLE:
            return _OPPORTUNITY_TO_ANGLE[opportunity_type]
    return "FULL_DIGITAL_UPGRADE"


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
        lines.append(sender["title"])
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

    resolved_angle = angle or pick_angle(opportunity_types)

    if provider is None:
        from app.database.config import get_settings

        settings = get_settings()
        provider, generated_by = get_ai_provider(settings.ollama_base_url, settings.ollama_model)

    ordered_reasons = _reorder_reasons_for_angle(resolved_angle, opportunity_types, opportunity_reasons)
    subject, body = provider.generate_outreach(
        business_name, category, resolved_angle, ordered_reasons, sender=sender, social_proof=social_proof
    )
    full_body = f"{body.rstrip()}\n\n{_build_signature(sender)}"

    return {
        "angle": resolved_angle,
        "subject": subject,
        "body": full_body,
        "generated_by": generated_by or "template",
    }
