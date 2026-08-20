from app.services.ai.base import AIProvider
from app.services.outreach.generator import generate_outreach_draft, pick_angle


class FakeProvider(AIProvider):
    def __init__(self):
        self.calls = []

    def is_available(self) -> bool:
        return True

    def generate_outreach(self, business_name, category, angle, observations, sender=None, social_proof=None):
        self.calls.append((business_name, category, angle, observations))
        return f"Subject for {business_name}", f"Body about {angle}"


def test_pick_angle_prefers_first_matching_opportunity_type():
    assert pick_angle(["MOBILE_IMPROVEMENT", "AI_CHATBOT"]) == "MOBILE_IMPROVEMENT"
    assert pick_angle(["ANALYTICS", "AI_CHATBOT"]) == "AI_CHATBOT"  # ANALYTICS has no mapped angle
    assert pick_angle([]) == "FULL_DIGITAL_UPGRADE"


def test_generate_outreach_draft_uses_injected_provider():
    provider = FakeProvider()

    draft = generate_outreach_draft(
        business_name="ABC Plumbing",
        category="Plumber",
        opportunity_types=["AI_CHATBOT"],
        opportunity_reasons=["No chatbot found."],
        provider=provider,
        generated_by="template",
    )

    assert draft["angle"] == "AI_CHATBOT"
    assert draft["subject"] == "Subject for ABC Plumbing"
    assert draft["body"] == "Body about AI_CHATBOT\n\nBest,"  # signature appended by generate_outreach_draft()
    assert draft["generated_by"] == "template"
    assert provider.calls == [("ABC Plumbing", "Plumber", "AI_CHATBOT", ["No chatbot found."])]


def test_generate_outreach_draft_appends_sender_signature():
    provider = FakeProvider()
    draft = generate_outreach_draft(
        business_name="ABC Plumbing",
        category="Plumber",
        opportunity_types=["AI_CHATBOT"],
        opportunity_reasons=[],
        provider=provider,
        generated_by="template",
        sender={"name": "Jordan Lee", "title": "Web Developer", "portfolio_url": "https://jordanlee.dev"},
    )
    assert draft["body"] == "Body about AI_CHATBOT\n\nBest,\nJordan Lee\nWeb Developer\nhttps://jordanlee.dev"


def test_generate_outreach_draft_respects_explicit_angle_override():
    provider = FakeProvider()
    draft = generate_outreach_draft(
        business_name="ABC Plumbing",
        category="Plumber",
        opportunity_types=["AI_CHATBOT"],
        opportunity_reasons=[],
        angle="BOOKING",
        provider=provider,
        generated_by="template",
    )
    assert draft["angle"] == "BOOKING"
