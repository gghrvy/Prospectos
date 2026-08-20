from dataclasses import dataclass

from app.models.enums import OpportunityType, QualityCategory
from app.services.analyzer.analyzer import AnalysisFindings
from app.services.scoring.weights import DEFAULT_WEIGHTS, ScoringWeights

AI_SIGNAL_FIELDS = ("has_ai_chatbot", "has_live_chat", "has_booking", "has_faq")
_AUTOMATION_TYPES = (
    OpportunityType.AI_CHATBOT.value,
    OpportunityType.BOOKING_AUTOMATION.value,
    OpportunityType.CUSTOMER_SUPPORT_AUTOMATION.value,
    OpportunityType.FAQ_AUTOMATION.value,
)


@dataclass
class ScoringResult:
    ai_opportunity_score: int
    redesign_opportunity_score: int
    overall_opportunity_score: int
    opportunity_types: list[str]
    opportunity_reasons: list[str]
    quality_category: str


def score_no_website(weights: ScoringWeights = DEFAULT_WEIGHTS) -> ScoringResult:
    """A missing website is, by itself, the strongest opportunity signal
    (spec section 8/21) — short-circuits the rest of the formula."""
    return ScoringResult(
        ai_opportunity_score=weights.no_website_ai_score,
        redesign_opportunity_score=weights.no_website_redesign_score,
        overall_opportunity_score=weights.no_website_overall_score,
        opportunity_types=[OpportunityType.NO_WEBSITE.value, OpportunityType.FULL_DIGITAL_UPGRADE.value],
        opportunity_reasons=[
            "Website not found from available sources.",
            "A business with no online presence at all represents the strongest possible opportunity for a full digital upgrade.",
        ],
        quality_category=QualityCategory.CRITICAL.value,
    )


def score_website(
    findings: AnalysisFindings, quality_category: str, weights: ScoringWeights = DEFAULT_WEIGHTS
) -> ScoringResult:
    """Opportunity formula for a business with a reachable website: every
    opportunity_type carries a corresponding human-readable reason (spec
    section 22 requires reasons always be shown, never a bare score)."""

    opportunity_types: list[str] = []
    reasons: list[str] = []

    redesign_gap = 100 - findings.website_quality_score
    if quality_category in (QualityCategory.POOR.value, QualityCategory.CRITICAL.value) or findings.website_quality_score < 50:
        opportunity_types.append(OpportunityType.WEBSITE_REDESIGN.value)
        reasons.append(
            f"Overall website quality scored {findings.website_quality_score}/100 ({quality_category}) — "
            "a redesign would meaningfully improve first impressions."
        )

    if findings.mobile_score < 60 or not findings.has_viewport:
        opportunity_types.append(OpportunityType.MOBILE_IMPROVEMENT.value)
        reasons.append(
            "No mobile viewport meta tag was detected or the mobile experience scored low — "
            "most local searches happen on phones."
        )

    if findings.conversion_score < 60 or not findings.has_contact_form:
        opportunity_types.append(OpportunityType.CONVERSION_IMPROVEMENT.value)
        reasons.append("Conversion elements (contact form, clear phone/email) are weak or missing, likely losing interested visitors.")

    if not findings.has_contact_form and not findings.has_email and not findings.has_phone:
        opportunity_types.append(OpportunityType.LEAD_CAPTURE.value)
        reasons.append("No visible way to capture a lead (form, email, or phone) was found on the site.")

    if not findings.has_ai_chatbot:
        opportunity_types.append(OpportunityType.AI_CHATBOT.value)
        reasons.append("No AI chatbot was detected; visitors outside business hours have no way to get instant answers.")

    if not findings.has_faq:
        opportunity_types.append(OpportunityType.FAQ_AUTOMATION.value)
        reasons.append("No FAQ section was found; an automated FAQ/chatbot could reduce repetitive phone inquiries.")

    if not findings.has_booking:
        opportunity_types.append(OpportunityType.BOOKING_AUTOMATION.value)
        reasons.append("No online booking/scheduling option was found; automating this could reduce phone-tag with customers.")

    if not findings.has_live_chat and not findings.has_ai_chatbot:
        opportunity_types.append(OpportunityType.CUSTOMER_SUPPORT_AUTOMATION.value)
        reasons.append("No live chat or AI support was detected; customers have to call or email for basic questions.")

    if not findings.has_analytics:
        opportunity_types.append(OpportunityType.ANALYTICS.value)
        reasons.append("No analytics tracking (e.g. Google Analytics/Tag Manager) was detected, so traffic and conversions likely aren't being measured.")

    ai_signals_missing = sum(1 for field in AI_SIGNAL_FIELDS if not getattr(findings, field))
    ai_opportunity_score = round((ai_signals_missing / len(AI_SIGNAL_FIELDS)) * 100)

    automation_gap_count = sum(1 for t in _AUTOMATION_TYPES if t in opportunity_types)
    if automation_gap_count >= 3:
        opportunity_types.append(OpportunityType.CUSTOM_AI_AUTOMATION.value)
        reasons.append(
            "Multiple automation gaps were found together — a custom AI automation package would address "
            "them as one system rather than piecemeal."
        )

    overall = (
        weights.redesign_weight * redesign_gap
        + weights.ai_gap_weight * ai_opportunity_score
        + weights.conversion_gap_weight * (100 - findings.conversion_score)
    )
    overall = round(max(0, min(100, overall)))

    if overall >= 80 and len(opportunity_types) >= 4 and OpportunityType.FULL_DIGITAL_UPGRADE.value not in opportunity_types:
        opportunity_types.append(OpportunityType.FULL_DIGITAL_UPGRADE.value)
        reasons.append("The combined scope of these gaps is broad enough to justify a full digital upgrade rather than one-off fixes.")

    return ScoringResult(
        ai_opportunity_score=ai_opportunity_score,
        redesign_opportunity_score=round(redesign_gap),
        overall_opportunity_score=overall,
        opportunity_types=opportunity_types,
        opportunity_reasons=reasons,
        quality_category=quality_category,
    )
