import app.api.businesses as businesses_api


def _create_business(client, **overrides) -> dict:
    payload = {"name": "ABC Plumbing", "category": "Plumber", "city": "Houston", "website": "https://abcplumbing.com"}
    payload.update(overrides)
    response = client.post("/api/businesses", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _fake_audit_data(**overrides) -> dict:
    data = {
        "url": "https://abcplumbing.com",
        "http_status": 200,
        "https_enabled": True,
        "title": "ABC Plumbing",
        "meta_description": "We fix pipes.",
        "page_count": 3,
        "crawl_depth": 1,
        "has_viewport": False,
        "has_contact_form": False,
        "has_email": True,
        "has_phone": True,
        "has_booking": False,
        "has_faq": False,
        "has_live_chat": False,
        "has_ai_chatbot": False,
        "has_whatsapp": False,
        "has_social_links": False,
        "broken_link_count": 1,
        "mobile_score": 30,
        "design_score": 40,
        "technical_score": 50,
        "content_score": 40,
        "conversion_score": 35,
        "customer_experience_score": 20,
        "website_quality_score": 35,
        "quality_category": "WEAK",
        "ai_opportunity_score": 75,
        "redesign_opportunity_score": 65,
        "overall_opportunity_score": 70,
        "opportunity_types": ["WEBSITE_REDESIGN", "AI_CHATBOT"],
        "opportunity_reasons": ["Low overall quality score.", "No AI chatbot detected."],
        "audit_summary": "WEAK website scoring 35/100 overall, with 2 opportunity area(s) identified.",
    }
    data.update(overrides)
    return data


def test_run_audit_creates_website_audit_and_updates_business_status(client, monkeypatch):
    created = _create_business(client)

    monkeypatch.setattr(businesses_api, "run_audit", lambda business: _fake_audit_data())

    response = client.post(f"/api/businesses/{created['id']}/audit")
    assert response.status_code == 201, response.text
    audit = response.json()
    assert audit["business_id"] == created["id"]
    assert audit["overall_opportunity_score"] == 70
    assert audit["opportunity_types"] == ["WEBSITE_REDESIGN", "AI_CHATBOT"]

    detail = client.get(f"/api/businesses/{created['id']}").json()
    assert detail["website_status"] == "exists"
    assert detail["latest_audit"]["overall_opportunity_score"] == 70
    assert len(detail["audits"]) == 1


def test_running_audit_twice_creates_two_rows_never_overwrites(client, monkeypatch):
    created = _create_business(client)

    monkeypatch.setattr(businesses_api, "run_audit", lambda business: _fake_audit_data(overall_opportunity_score=70))
    client.post(f"/api/businesses/{created['id']}/audit")

    monkeypatch.setattr(businesses_api, "run_audit", lambda business: _fake_audit_data(overall_opportunity_score=40))
    client.post(f"/api/businesses/{created['id']}/audit")

    detail = client.get(f"/api/businesses/{created['id']}").json()
    assert len(detail["audits"]) == 2
    # latest_audit is the most recently created one (score 40)
    assert detail["latest_audit"]["overall_opportunity_score"] == 40


def test_audit_no_website_business_sets_website_status_not_found(client, monkeypatch):
    created = _create_business(client, website=None)

    monkeypatch.setattr(
        businesses_api,
        "run_audit",
        lambda business: {
            "url": None,
            "quality_category": "CRITICAL",
            "opportunity_types": ["NO_WEBSITE", "FULL_DIGITAL_UPGRADE"],
            "opportunity_reasons": ["Website not found from available sources."],
            "ai_opportunity_score": 90,
            "redesign_opportunity_score": 100,
            "overall_opportunity_score": 95,
            "audit_summary": "No website found.",
        },
    )

    response = client.post(f"/api/businesses/{created['id']}/audit")
    assert response.status_code == 201
    assert response.json()["overall_opportunity_score"] == 95

    detail = client.get(f"/api/businesses/{created['id']}").json()
    assert detail["website_status"] == "not_found"


def test_audit_fills_blank_business_email_from_discovered_email(client, monkeypatch):
    created = _create_business(client, email=None)

    monkeypatch.setattr(
        businesses_api, "run_audit", lambda business: _fake_audit_data(discovered_email="owner@abcplumbing.com")
    )
    client.post(f"/api/businesses/{created['id']}/audit")

    detail = client.get(f"/api/businesses/{created['id']}").json()
    assert detail["email"] == "owner@abcplumbing.com"


def test_audit_never_overwrites_an_existing_business_email(client, monkeypatch):
    created = _create_business(client, email="already-on-file@abcplumbing.com")

    monkeypatch.setattr(
        businesses_api, "run_audit", lambda business: _fake_audit_data(discovered_email="different@abcplumbing.com")
    )
    client.post(f"/api/businesses/{created['id']}/audit")

    detail = client.get(f"/api/businesses/{created['id']}").json()
    assert detail["email"] == "already-on-file@abcplumbing.com"


def test_audit_business_not_found_returns_404(client):
    response = client.post("/api/businesses/does-not-exist/audit")
    assert response.status_code == 404


def test_list_businesses_includes_latest_opportunity_score_and_status(client, monkeypatch):
    created = _create_business(client)

    monkeypatch.setattr(businesses_api, "run_audit", lambda business: _fake_audit_data(overall_opportunity_score=82))
    client.post(f"/api/businesses/{created['id']}/audit")
    client.post(f"/api/businesses/{created['id']}/status", json={"status": "QUALIFIED"})

    listing = client.get("/api/businesses").json()
    row = listing["items"][0]
    assert row["latest_opportunity_score"] == 82
    assert row["latest_quality_category"] == "WEAK"
    assert row["current_status"] == "QUALIFIED"
