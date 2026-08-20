import httpx

from app.services.ai.ollama_provider import OllamaProvider
from app.services.ai.template_provider import TemplateProvider


def test_template_provider_is_always_available():
    assert TemplateProvider().is_available() is True


def test_template_provider_uses_only_given_observations():
    provider = TemplateProvider()
    subject, body = provider.generate_outreach(
        business_name="ABC Plumbing",
        category="Plumber",
        angle="AI_CHATBOT",
        observations=["No AI chatbot was detected on the site."],
    )

    assert "ABC Plumbing" in subject
    # The raw scorer sentence is rewritten into owner-facing language
    # (see _OBSERVATION_REWRITES) rather than piped through verbatim —
    # this asserts on the grounded fact it's still built from, not the
    # literal audit-tool phrasing.
    assert "instant answer outside" in body.lower()
    assert "plumber" in body.lower()
    # Never insults — no negative adjectives about the business itself.
    assert "bad" not in body.lower() and "terrible" not in body.lower()


def test_template_provider_falls_back_to_raw_text_for_unrecognized_observation():
    provider = TemplateProvider()
    _, body = provider.generate_outreach(
        business_name="ABC Plumbing",
        category="Plumber",
        angle="FULL_DIGITAL_UPGRADE",
        observations=["Some brand-new scorer reason nobody's seen before."],
    )
    assert "some brand-new scorer reason nobody's seen before" in body.lower()


def test_template_provider_handles_no_observations_gracefully():
    provider = TemplateProvider()
    subject, body = provider.generate_outreach("ABC Plumbing", None, "FULL_DIGITAL_UPGRADE", [])
    assert subject
    assert body


def test_template_provider_consequence_matches_the_angle_not_a_generic_line():
    provider = TemplateProvider()
    _, mobile_body = provider.generate_outreach(
        "ABC Plumbing",
        "Plumber",
        "MOBILE_IMPROVEMENT",
        ["No mobile viewport meta tag was detected or the mobile experience scored low — most local searches happen on phones."],
    )
    _, chatbot_body = provider.generate_outreach(
        "ABC Plumbing", "Plumber", "AI_CHATBOT", ["No AI chatbot was detected on the site."]
    )
    # The old version always said "visitor outside business hours" even
    # for a mobile-rendering finding -- a non-sequitur. Each angle now
    # gets its own consequence, so these two bodies must differ.
    assert mobile_body != chatbot_body
    assert "phone" in mobile_body.lower()
    assert "after hours" in chatbot_body.lower() or "outside business hours" in chatbot_body.lower()


def test_template_provider_greets_generically_not_by_business_name():
    # "Hi ABC Plumbing," reads like addressing a company as a person --
    # the business name should appear naturally in the first sentence
    # instead, not in the salutation.
    provider = TemplateProvider()
    _, body = provider.generate_outreach("ABC Plumbing", "Plumber", "FULL_DIGITAL_UPGRADE", [])
    assert not body.startswith("Hi ABC Plumbing,")
    assert "Hi there," in body


def test_template_provider_cites_real_strong_rating_as_social_proof():
    provider = TemplateProvider()
    _, body = provider.generate_outreach(
        "ABC Plumbing",
        "Plumber",
        "FULL_DIGITAL_UPGRADE",
        [],
        social_proof={"rating": 4.8, "review_count": 42},
    )
    assert "4.8" in body
    assert "42 reviews" in body


def test_template_provider_omits_social_proof_when_rating_is_thin_or_missing():
    provider = TemplateProvider()
    _, no_rating_body = provider.generate_outreach(
        "ABC Plumbing", "Plumber", "FULL_DIGITAL_UPGRADE", [], social_proof=None
    )
    _, low_review_count_body = provider.generate_outreach(
        "ABC Plumbing", "Plumber", "FULL_DIGITAL_UPGRADE", [], social_proof={"rating": 5.0, "review_count": 1}
    )
    _, low_rating_body = provider.generate_outreach(
        "ABC Plumbing", "Plumber", "FULL_DIGITAL_UPGRADE", [], social_proof={"rating": 3.2, "review_count": 50}
    )
    for body in (no_rating_body, low_review_count_body, low_rating_body):
        assert "rating" not in body.lower()
        assert "reviews" not in body.lower()


def test_ollama_provider_is_available_when_reachable():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.1", http_client=client)

    assert provider.is_available() is True


def test_ollama_provider_is_unavailable_when_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.1", http_client=client)

    assert provider.is_available() is False


def test_ollama_provider_parses_subject_and_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "Subject: Quick idea for ABC Plumbing\n\nHi there,\nBody text."})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.1", http_client=client)

    subject, body = provider.generate_outreach("ABC Plumbing", "Plumber", "AI_CHATBOT", ["No chatbot found."])

    assert subject == "Quick idea for ABC Plumbing"
    assert "Body text." in body


def test_ollama_provider_falls_back_to_raw_text_when_no_subject_line():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "Just a plain response with no subject line."})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.1", http_client=client)

    subject, body = provider.generate_outreach("ABC Plumbing", "Plumber", "AI_CHATBOT", [])

    assert subject == "Quick idea for ABC Plumbing"
    assert "Just a plain response" in body
