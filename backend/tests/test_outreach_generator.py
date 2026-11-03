import httpx

from app.services.ai.base import AIProvider
from app.services.ai.ollama_provider import OllamaProvider
from app.services.ai.template_provider import TemplateProvider
from app.services.outreach.generator import generate_outreach_draft, has_internal_audit_language, pick_angle, pick_primary_angle


class FakeProvider(AIProvider):
    def __init__(self):
        self.calls = []

    def is_available(self) -> bool:
        return True

    def generate_outreach(self, business_name, category, angle, observations, sender=None, social_proof=None):
        self.calls.append((business_name, category, angle, observations))
        return f"Subject for {business_name}", f"Body about {angle}"


def test_generate_outreach_draft_falls_back_to_template_when_ollama_generation_fails():
    # Ollama answers the probe but the model isn't pulled: /api/generate is a 404.
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": []})
        return httpx.Response(404, json={"error": "model 'llama3.1' not found"})

    provider = OllamaProvider(
        base_url="http://localhost:11434", model="llama3.1", http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    draft = generate_outreach_draft(
        business_name="ABC Plumbing",
        category="Plumber",
        opportunity_types=["AI_CHATBOT"],
        opportunity_reasons=["No chatbot found."],
        provider=provider,
        generated_by="ollama",
    )

    assert draft["generated_by"] == "template"
    assert draft["subject"]
    assert "ABC Plumbing" in draft["body"]


def test_generate_outreach_draft_falls_back_to_template_when_ollama_returns_non_json():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>proxy error</html>")

    provider = OllamaProvider(
        base_url="http://localhost:11434", model="llama3.1", http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    draft = generate_outreach_draft(
        business_name="ABC Plumbing",
        category="Plumber",
        opportunity_types=["AI_CHATBOT"],
        opportunity_reasons=["No chatbot found."],
        provider=provider,
        generated_by="ollama",
    )

    assert draft["generated_by"] == "template"


def test_pick_angle_prefers_first_matching_opportunity_type():
    assert pick_angle(["MOBILE_IMPROVEMENT", "AI_CHATBOT"]) == "MOBILE_IMPROVEMENT"
    assert pick_angle(["ANALYTICS", "AI_CHATBOT"]) == "ANALYTICS"
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


def test_primary_outreach_uses_customer_facing_observation_not_internal_evidence():
    draft = generate_outreach_draft(
        business_name="Ants Pants Cafe",
        category="Cafe",
        opportunity_types=["AI_CHATBOT"],
        opportunity_reasons=["No AI chatbot was detected on the crawled pages."],
        provider=TemplateProvider(),
        opportunity_assessments=[{
            "classification": "PRIMARY", "opportunity_type": "AI_CHATBOT",
            "outreach_observation": "visitors can browse menu and location information, but do not have a quick way to ask a question directly on the site",
            "possible_impact": "A small assistant could make common questions easier to answer while keeping existing contact options in place.",
        }],
    )
    assert not has_internal_audit_language(draft["body"])
    assert "quick way to ask a question" in draft["body"]


def test_no_primary_angle_is_not_auto_pickable():
    assert pick_primary_angle([{"classification": "SECONDARY", "opportunity_type": "LEAD_CAPTURE"}]) is None
