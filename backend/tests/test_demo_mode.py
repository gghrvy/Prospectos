import app.api.businesses as businesses_api
import app.main as main_api
from app.database.config import Settings


def _enable_demo_mode(monkeypatch):
    settings = Settings(database_url="sqlite://", demo_mode=True)
    monkeypatch.setattr(main_api, "get_settings", lambda: settings)
    monkeypatch.setattr(businesses_api, "get_settings", lambda: settings)


def test_production_defaults_to_demo_mode_and_explicit_flag_overrides_it():
    assert Settings(database_url="sqlite://", environment="production").is_demo_mode is True
    assert Settings(database_url="sqlite://", environment="production", demo_mode=False).is_demo_mode is False
    assert Settings(database_url="sqlite://", environment="development").is_demo_mode is False


def test_demo_mode_returns_prepared_fictional_records_and_replays_an_audit(client, monkeypatch):
    _enable_demo_mode(monkeypatch)

    listing = client.get("/api/businesses")
    assert listing.status_code == 200
    assert listing.json()["total"] == 4
    assert {item["category"] for item in listing.json()["items"]} == {
        "Dental clinic", "Restaurant", "Real estate agency", "Home services"
    }

    business_id = "demo-brightsmile-dental"
    detail = client.get(f"/api/businesses/{business_id}")
    assert detail.status_code == 200
    assert detail.json()["latest_audit"]["overall_opportunity_score"] == 86
    assert detail.json()["outreach_drafts"][0]["sent_at"] is None

    audit = client.post(f"/api/businesses/{business_id}/audit")
    assert audit.status_code == 201
    assert audit.json()["business_id"] == business_id
    assert audit.json()["audit_summary"].startswith("Prepared demo audit")


def test_demo_mode_rejects_live_operations_before_they_can_reach_integrations(client, monkeypatch):
    _enable_demo_mode(monkeypatch)

    blocked_requests = [
        ("post", "/api/businesses", {"json": {"name": "Real visitor URL", "website": "https://example.com"}}),
        ("post", "/api/businesses/search", {"json": {"category": "plumber", "city": "Austin"}}),
        ("post", "/api/businesses/demo-brightsmile-dental/outreach", {"json": {}}),
        ("post", "/api/gmail/outreach/draft-demo/send", {}),
        ("get", "/api/gmail/connect", {}),
        ("get", "/api/businesses/export-csv", {}),
        ("post", "/api/businesses/not-a-demo/audit", {}),
    ]
    for method, path, kwargs in blocked_requests:
        response = getattr(client, method)(path, **kwargs)
        assert response.status_code == 403, (path, response.text)
        assert "Demo Mode is read-only" in response.json()["detail"]
