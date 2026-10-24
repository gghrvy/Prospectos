from app.models.business import Business
from app.services.analyzer.analyzer import AnalysisFindings
from app.services.opportunities import assess_opportunities


def test_booking_is_rejected_for_coffee_shop_but_relevant_for_dental_clinic():
    findings = AnalysisFindings(url="https://example.com", has_booking=False, has_contact_form=True, has_ai_chatbot=True, has_faq=True, has_analytics=True)
    coffee = assess_opportunities(Business(name="Bennu", category="Coffee shop", website="https://example.com"), findings, {})
    dentist = assess_opportunities(Business(name="Smile", category="Dental clinic", website="https://example.com"), findings, {})
    coffee_booking = next(item for item in coffee if item["opportunity_type"] == "BOOKING_AUTOMATION")
    dentist_booking = next(item for item in dentist if item["opportunity_type"] == "BOOKING_AUTOMATION")
    assert coffee_booking["classification"] == "REJECTED"
    assert dentist_booking["recommendation_score"] > coffee_booking["recommendation_score"]


def test_24_hour_context_prevents_after_hours_chat_pitch():
    findings = AnalysisFindings(url="https://example.com", has_ai_chatbot=False, has_contact_form=True, has_booking=True, has_faq=True, has_analytics=True)
    items = assess_opportunities(Business(name="Bennu", category="Coffee shop", website="https://example.com"), findings, {"mentions_24_hour_service": True})
    chatbot = next(item for item in items if item["opportunity_type"] == "AI_CHATBOT")
    assert "24-hour operation" in chatbot["reasoning"]
    assert "outside business hours" not in chatbot["possible_impact"]


def test_apparel_retail_site_does_not_pitch_chat_from_generic_site_topics():
    findings = AnalysisFindings(url="https://example.com", has_ai_chatbot=False, has_contact_form=True, has_booking=True, has_faq=False, has_analytics=True)
    items = assess_opportunities(
        Business(name="Hutson Clothing Co", category="Clothing company", website="https://example.com"),
        findings,
        {"information_topics": ["hours", "locations", "menu"]},
    )
    chatbot = next(item for item in items if item["opportunity_type"] == "AI_CHATBOT")
    assert chatbot["classification"] == "REJECTED"


def test_existing_contact_path_prevents_chat_from_becoming_primary():
    findings = AnalysisFindings(url="https://example.com", has_ai_chatbot=False, has_contact_form=True, has_email=True, has_phone=True, has_booking=True, has_faq=True, has_analytics=True)
    items = assess_opportunities(
        Business(name="Information-rich business", category="Cafe", website="https://example.com"),
        findings,
        {"information_topics": ["menu", "hours", "locations"], "has_existing_contact_path": True},
    )
    chatbot = next(item for item in items if item["opportunity_type"] == "AI_CHATBOT")
    assert chatbot["classification"] != "PRIMARY"
