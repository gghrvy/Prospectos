import app.api.businesses as businesses_api


def _create_business(client, **overrides) -> dict:
    payload = {"name": "ABC Plumbing", "category": "Plumber", "city": "Houston", "website": "https://abcplumbing.com"}
    payload.update(overrides)
    response = client.post("/api/businesses", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _fake_draft(**overrides) -> dict:
    data = {"angle": "AI_CHATBOT", "subject": "Quick idea for ABC Plumbing", "body": "Hi there...", "generated_by": "template"}
    data.update(overrides)
    return data


def test_generate_outreach_without_prior_audit_defaults_to_no_website_angle(client, monkeypatch):
    created = _create_business(client)

    captured = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return _fake_draft()

    monkeypatch.setattr(businesses_api, "generate_outreach_draft", fake_generate)

    response = client.post(f"/api/businesses/{created['id']}/outreach", json={})
    assert response.status_code == 201, response.text
    assert captured["opportunity_types"] == ["NO_WEBSITE"]


def test_generate_outreach_uses_latest_audit_opportunity_data(client, monkeypatch):
    created = _create_business(client)

    monkeypatch.setattr(businesses_api, "run_audit", lambda business: {
        "url": "https://abcplumbing.com",
        "quality_category": "WEAK",
        "opportunity_types": ["AI_CHATBOT", "MOBILE_IMPROVEMENT"],
        "opportunity_reasons": ["No chatbot.", "No viewport."],
        "ai_opportunity_score": 70,
        "redesign_opportunity_score": 50,
        "overall_opportunity_score": 60,
    })
    client.post(f"/api/businesses/{created['id']}/audit")

    captured = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return _fake_draft()

    monkeypatch.setattr(businesses_api, "generate_outreach_draft", fake_generate)

    response = client.post(f"/api/businesses/{created['id']}/outreach", json={})
    assert response.status_code == 201
    assert captured["opportunity_types"] == ["AI_CHATBOT", "MOBILE_IMPROVEMENT"]
    assert captured["opportunity_reasons"] == ["No chatbot.", "No viewport."]


def test_regenerate_outreach_creates_new_row_not_overwrite(client, monkeypatch):
    created = _create_business(client)

    monkeypatch.setattr(businesses_api, "generate_outreach_draft", lambda **kwargs: _fake_draft(subject="First draft"))
    client.post(f"/api/businesses/{created['id']}/outreach", json={})

    monkeypatch.setattr(businesses_api, "generate_outreach_draft", lambda **kwargs: _fake_draft(subject="Second draft"))
    client.post(f"/api/businesses/{created['id']}/outreach", json={})

    detail = client.get(f"/api/businesses/{created['id']}").json()
    assert len(detail["outreach_drafts"]) == 2
    assert detail["outreach_drafts"][0]["subject"] == "Second draft"


def test_generate_outreach_business_not_found_returns_404(client):
    response = client.post("/api/businesses/does-not-exist/outreach", json={})
    assert response.status_code == 404


def test_generate_outreach_with_sender_snapshots_and_returns_signature_fields(client, monkeypatch):
    created = _create_business(client)

    sender_response = client.post(
        "/api/senders",
        json={"name": "Jordan Lee", "title": "Web Developer", "portfolio_url": "https://jordanlee.dev"},
    )
    assert sender_response.status_code == 201
    sender_id = sender_response.json()["id"]

    captured = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return _fake_draft()

    monkeypatch.setattr(businesses_api, "generate_outreach_draft", fake_generate)

    response = client.post(f"/api/businesses/{created['id']}/outreach", json={"sender_id": sender_id})
    assert response.status_code == 201, response.text
    body = response.json()

    assert captured["sender"] == {
        "name": "Jordan Lee",
        "title": "Web Developer",
        "email": None,
        "phone": None,
        "portfolio_url": "https://jordanlee.dev",
    }
    assert body["sender_id"] == sender_id
    assert body["sender_name"] == "Jordan Lee"
    assert body["sender_portfolio_url"] == "https://jordanlee.dev"


def test_generate_outreach_with_unknown_sender_id_returns_404(client):
    created = _create_business(client)
    response = client.post(f"/api/businesses/{created['id']}/outreach", json={"sender_id": "does-not-exist"})
    assert response.status_code == 404
