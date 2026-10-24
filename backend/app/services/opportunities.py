"""Context-aware commercial interpretation of crawl findings."""
from __future__ import annotations

import re

from app.models.business import Business
from app.models.enums import OpportunityType
from app.services.analyzer.analyzer import AnalysisFindings
from app.services.crawler.crawler import CrawlResult

_BOOKING_HIGH = ("dent", "clinic", "medical", "doctor", "health", "therapy", "salon", "spa", "barber", "fitness", "gym")
_BOOKING_LOW = ("coffee", "cafe", "restaurant", "bakery", "retail", "store")
_SERVICE_HIGH = ("plumb", "electric", "roof", "law", "account", "consult", "agency", "real estate", "repair")
_HOSPITALITY = ("coffee", "cafe", "restaurant", "bakery", "bar", "food")
_APPAREL_RETAIL = ("clothing", "apparel", "fashion", "boutique", "retail")


def build_website_context(crawl: CrawlResult, findings: AnalysisFindings) -> dict:
    html = " ".join(page.html or "" for page in crawl.pages)
    text = re.sub(r"<[^>]+>", " ", html).lower()
    information_topics = []
    for topic, patterns in {
        "menu": ("our menu", "food menu", "drink menu"), "hours": ("opening hours", "store hours", "business hours"), "locations": ("our locations", "find a location", "locations"),
        "services": ("services", "treatments"), "pricing": ("pricing", "prices"),
        "events": ("events", "upcoming events"), "policies": ("return policy", "shipping policy", "privacy policy", "policies"),
    }.items():
        if any(pattern in text for pattern in patterns):
            information_topics.append(topic)
    return {
        "mentions_24_hour_service": bool(re.search(r"(?:open\s*)?24\s*(?:hours?|hrs?)|24\s*/\s*7", text)),
        "has_existing_contact_path": bool(findings.has_contact_form or findings.has_email or findings.has_phone or findings.has_whatsapp),
        "crawled_page_count": findings.page_count,
        "information_topics": information_topics,
    }


def _category_score(category: str | None, high: tuple[str, ...], low: tuple[str, ...] = ()) -> int:
    value = (category or "").lower()
    if any(term in value for term in high): return 88
    if any(term in value for term in low): return 28
    return 55


def _item(kind: str, evidence: str, outreach_observation: str, relevance: int, impact: int, outreach: int, visual: int, reasoning: str,
          possible_impact: str, concept: str, flow: str, confidence: int = 85, penalty: int = 0) -> dict:
    score = round(max(0, min(100, confidence * .25 + relevance * .25 + impact * .22 + outreach * .20 + visual * .08 - penalty)))
    return {"opportunity_type": kind, "evidence": evidence, "outreach_observation": outreach_observation, "evidence_confidence": confidence,
            "business_relevance": relevance, "estimated_business_impact": impact, "outreach_suitability": outreach,
            "visual_demo_score": visual, "recommendation_score": score, "reasoning": reasoning,
            "business_interpretation": possible_impact,
            "possible_impact": possible_impact, "recommended_concept": concept, "customer_flow": flow,
            "classification": "REJECTED"}


def assess_opportunities(business: Business, findings: AnalysisFindings, context: dict) -> list[dict]:
    """Scores are internal prioritisation aids, never claims of measured impact."""
    if not business.website:
        candidates = [_item(OpportunityType.NO_WEBSITE.value, "No website was available in the prospect record.", "I could not find a website where visitors can learn about the business online.", 95, 90, 92, 85,
            "A first website is directly relevant because no current site exists to preserve.",
            "This may make it harder for people who search online to understand the business and find a next step.",
            "Create a focused first website with contact details and a clear next action.",
            "Search result → website → understand offering → contact or visit.", 95)]
    else:
        candidates = []
        contact_path = context.get("has_existing_contact_path", False)
        category = business.category
        if not findings.has_contact_form:
            relevance = 76 if any(x in (category or "").lower() for x in _SERVICE_HIGH) else 62
            candidates.append(_item(OpportunityType.LEAD_CAPTURE.value, "No visible contact or lead-capture form was detected on the crawled pages.", "there is not an obvious way for an interested visitor to leave their details directly on the site", relevance, 70 if not contact_path else 56, 78 if not contact_path else 68, 92,
                "Existing phone, email, or messaging options are considered, so this is not treated as a total lack of contact options.",
                "This may make it harder to stay connected with visitors who are interested but not ready to call or email immediately.",
                "Add a lightweight, on-brand enquiry or callback form within the existing experience.",
                "Visitor explores site → submits a short enquiry → business follows up.", 90, 10 if contact_path else 0))
        if findings.conversion_score < 60:
            candidates.append(_item(OpportunityType.CONVERSION_IMPROVEMENT.value, "The website's conversion score is below the configured threshold.", "a few parts of the site make the next step less obvious than it could be", 64, 62, 66, 78,
                "A conversion improvement is considered from the combined availability and clarity of existing action paths, rather than from any single missing feature.",
                "This may make it harder for visitors to move from browsing to a useful next step.", "Clarify the most relevant next action within the existing design.",
                "Visitor understands the offer → sees a clear next step → contacts, enquires, or books.", 78))
        if not findings.has_booking:
            relevance = _category_score(category, _BOOKING_HIGH, _BOOKING_LOW)
            candidates.append(_item(OpportunityType.BOOKING_AUTOMATION.value, "No visible online booking or scheduling option was detected.", "appointments appear to require another step outside the website", relevance, relevance, relevance, 74,
                "Booking is ranked by whether the category typically relies on scheduled appointments, not merely by the feature being absent.",
                "For appointment-based businesses, this may offer visitors a more direct way to request a time.",
                "Add an appointment request or scheduling step that fits the current site.",
                "Visitor selects service → chooses a time or requests one → receives confirmation.", 85, 22 if relevance < 45 else 0))
        if not findings.has_ai_chatbot:
            penalty = 25 if context.get("mentions_24_hour_service") else 0
            topics = context.get("information_topics", [])
            category_text = (category or "").lower()
            is_hospitality = any(term in category_text for term in _HOSPITALITY)
            is_apparel_retail = any(term in category_text for term in _APPAREL_RETAIL)
            enough_context = len(topics) >= 2 and (is_hospitality or findings.has_faq or "services" in topics or "policies" in topics)
            relevance = 76 if enough_context else 30
            impact = 64 if enough_context else 28
            outreach = 70 if enough_context else 22
            if is_apparel_retail:
                relevance = min(relevance, 42)
                impact = min(impact, 38)
                outreach = min(outreach, 32)
            if contact_path or findings.has_live_chat:
                relevance = min(relevance, 30)
                impact = min(impact, 28)
                outreach = min(outreach, 18)
            topic_text = ", ".join(topics[:3])
            observation = (f"visitors can browse information about {topic_text}, but do not have a quick way to ask a question directly on the site"
                           if enough_context else "there is no direct question-and-answer option on the site")
            candidates.append(_item(OpportunityType.AI_CHATBOT.value, "No AI chat assistant was detected on the crawled pages.", observation, relevance, impact, outreach - penalty, 82,
                "An assistant is only considered when the website contains several customer-facing information areas and no sufficiently easy existing support path. A 24-hour operation is not described as unavailable.",
                "A chat assistant could make common website questions easier to answer without replacing existing support channels.",
                "Offer an optional on-site assistant for common questions and routing.",
                "Visitor asks a common question → gets guided answer → follows an existing action path.", 78, penalty))
        if not findings.has_faq:
            candidates.append(_item(OpportunityType.FAQ_AUTOMATION.value, "No visible FAQ section was detected on the crawled pages.", "common information is spread across the site rather than available in one quick-reference place", 48, 45, 44, 65,
                "A missing FAQ alone is usually a secondary improvement unless other evidence makes common questions central.",
                "A concise FAQ could make routine information easier to find.", "Add a small FAQ section or make it available through an optional assistant.",
                "Visitor opens FAQ → finds routine answer → continues to an existing action.", 75))
        if not findings.has_live_chat and not findings.has_ai_chatbot and len(context.get("information_topics", [])) >= 2:
            candidates.append(_item(OpportunityType.CUSTOMER_SUPPORT_AUTOMATION.value, "No live chat or AI support was detected on the crawled pages.", "visitors can browse useful information, but do not have a direct way to get help with a question on the site", 62, 55, 52, 70,
                "Support automation is only considered when the site offers several information areas and no direct support channel is visible.",
                "This could make routine questions easier to handle while preserving existing contact options.", "Add a simple support and routing option for common questions.",
                "Visitor asks a question → gets guidance → follows the relevant existing action path.", 76))
        if not findings.has_analytics:
            candidates.append(_item(OpportunityType.ANALYTICS.value, "No common analytics tracking signal was detected in the crawled pages.", "there is an opportunity to make key website actions easier to review", 55, 48, 42, 40,
                "Tracking is useful operationally but usually less compelling as a first cold-email angle because visitors cannot see it directly.",
                "This could limit what the business can learn about website traffic and completed actions.", "Add privacy-conscious measurement for key website actions.",
                "Visitor completes an action → event is recorded → business reviews trends.", 65))
        if findings.mobile_score < 60 or not findings.has_viewport:
            candidates.append(_item(OpportunityType.MOBILE_IMPROVEMENT.value, "The mobile score was low or no mobile viewport meta tag was detected.", "the site may be less comfortable to use on a phone than it could be", 75, 72, 76, 88,
                "This is based on a direct technical/mobile observation.", "This may make the site less comfortable to use on a phone.",
                "Improve mobile layout and tap targets while preserving the site identity.", "Mobile visitor opens page → reads and navigates comfortably → takes an existing action.", 88))
        if findings.website_quality_score < 50:
            candidates.append(_item(OpportunityType.WEBSITE_REDESIGN.value, f"Website quality scored {findings.website_quality_score}/100.", "a few parts of the website could be clearer and easier to use", 70, 70, 64, 90,
                "A broader refresh is considered only when several observable quality signals are weak.", "This may make it harder for visitors to quickly understand and use the site.",
                "Refresh the site structure and presentation around the strongest business action.", "Visitor lands → understands offering → takes a clear next step.", 78))
        automation_count = sum(1 for item in candidates if item["opportunity_type"] in {
            OpportunityType.AI_CHATBOT.value, OpportunityType.FAQ_AUTOMATION.value,
            OpportunityType.CUSTOMER_SUPPORT_AUTOMATION.value, OpportunityType.BOOKING_AUTOMATION.value,
        })
        if automation_count >= 3:
            candidates.append(_item(OpportunityType.CUSTOM_AI_AUTOMATION.value, "Several distinct automation opportunities were identified from the website.", "there may be an opportunity to make a few common website tasks easier to handle in one connected experience", 58, 58, 45, 65,
                "A broader automation idea is kept secondary unless the individual customer use cases are already strong.",
                "This could simplify how visitors find information and take the next step.", "Connect the most relevant small automation improvements into one focused workflow.",
                "Visitor asks, enquires, or books → receives the relevant guidance → continues with the business.", 72))
    candidates.sort(key=lambda item: item["recommendation_score"], reverse=True)
    primary = False
    for item in candidates:
        # 60+ is strong enough for a focused, evidence-backed first
        # outreach. Below that, keep the item as context only rather than
        # forcing a pitch.
        if not primary and item["recommendation_score"] >= 60:
            item["classification"] = "PRIMARY"; primary = True
        elif item["recommendation_score"] >= 45:
            item["classification"] = "SECONDARY"
    return candidates
