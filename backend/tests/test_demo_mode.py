import re

import pytest

import app.api.businesses as businesses_api
import app.main as main_api
from app.database.config import Settings
from app.services.discovery.base import DiscoveredBusiness
from app.services.discovery.demo_limits import demo_search_limiter
from app.services.discovery.openstreetmap import OpenStreetMapProvider


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
        ("post", "/api/businesses/search", {"json": {"category": "plumber", "city": "Austin", "save": True}}),
        ("post", "/api/businesses/demo-brightsmile-dental/outreach", {"json": {}}),
        ("post", "/api/gmail/outreach/draft-demo/send", {}),
        ("post", "/api/gmail/batches/any-batch/dispatch", {}),
        ("post", "/api/gmail/batches/any-batch/pause", {}),
        ("get", "/api/gmail/connect", {}),
        ("get", "/api/businesses/export-csv", {}),
        ("post", "/api/businesses/not-a-demo/audit", {}),
    ]
    for method, path, kwargs in blocked_requests:
        response = getattr(client, method)(path, **kwargs)
        assert response.status_code == 403, (path, response.text)
        assert "Demo Mode is read-only" in response.json()["detail"]


def test_demo_leads_stay_in_research_stages_because_no_draft_was_sent():
    from app.services import demo_data

    research = {"NEW", "AUDITED", "QUALIFIED", "OUTREACH_READY"}
    items = demo_data.list_businesses()["items"]
    assert len({item["current_status"] for item in items}) > 1
    for item in items:
        detail = demo_data.business_detail(item["id"])
        assert item["current_status"] in research
        assert detail["current_status"] == item["current_status"]
        assert all(draft["sent_at"] is None for draft in detail["outreach_drafts"])


@pytest.fixture()
def demo_search(client, monkeypatch):
    _enable_demo_mode(monkeypatch)
    demo_search_limiter.reset()
    calls = []

    def fake_discover(self, **kwargs):
        calls.append(kwargs)
        return [DiscoveredBusiness(name="Found Co", city=kwargs.get("city"), source="openstreetmap")]

    monkeypatch.setattr(OpenStreetMapProvider, "discover", fake_discover)
    monkeypatch.setattr(OpenStreetMapProvider, "geocode", lambda self, place: {"latitude": 1.0, "longitude": 2.0, "display_name": place})
    yield client, calls
    demo_search_limiter.reset()


def test_demo_search_returns_live_results_with_capped_size(demo_search):
    client, calls = demo_search

    response = client.post("/api/businesses/search", json={"category": "plumber", "city": "Austin", "radius_km": 50, "limit": 500})

    assert response.status_code == 200, response.text
    assert [b["name"] for b in response.json()] == ["Found Co"]
    assert calls[0]["limit"] == 25
    assert calls[0]["radius_km"] == 10


def test_demo_search_never_saves(demo_search):
    client, calls = demo_search

    response = client.post("/api/businesses/search", json={"category": "plumber", "city": "Austin", "save": True})

    assert response.status_code == 403
    assert "Demo Mode is read-only" in response.json()["detail"]
    assert calls == []


def test_demo_search_is_rate_limited_per_visitor(demo_search):
    client, calls = demo_search
    statuses = [
        client.post("/api/businesses/search", json={"category": "plumber", "city": f"Town {i}"}).status_code for i in range(7)
    ]

    assert statuses[:6] == [200] * 6
    assert statuses[6] == 429
    assert len(calls) == 6


def test_demo_repeat_search_is_served_from_cache(demo_search):
    client, calls = demo_search
    for _ in range(2):
        assert client.post("/api/businesses/search", json={"category": "bakery", "city": "Austin"}).status_code == 200

    assert len(calls) == 1


def test_demo_geocode_is_allowed(demo_search):
    client, _ = demo_search

    response = client.post("/api/businesses/search/geocode", json={"place": "Austin"})

    assert response.status_code == 200, response.text


def test_demo_lists_known_categories(demo_search):
    client, _ = demo_search

    response = client.get("/api/businesses/search/categories")

    assert response.status_code == 200
    assert response.json()["categories"]


def test_demo_search_falls_back_to_geoapify_when_a_key_is_set(demo_search, monkeypatch):
    from app.services.discovery.geoapify import GeoapifyProvider

    client, _ = demo_search
    settings = Settings(database_url="sqlite://", demo_mode=True, geoapify_api_key="test-key")
    monkeypatch.setattr(main_api, "get_settings", lambda: settings)
    monkeypatch.setattr(businesses_api, "get_settings", lambda: settings)

    def osm_down(self, **kwargs):
        raise ValueError("Overpass is at capacity")

    monkeypatch.setattr(OpenStreetMapProvider, "discover", osm_down)
    monkeypatch.setattr(
        GeoapifyProvider, "discover", lambda self, **kwargs: [DiscoveredBusiness(name="Backup Co", source="geoapify")]
    )

    response = client.post("/api/businesses/search", json={"category": "dentist", "city": "Austin"})

    assert response.status_code == 200, response.text
    assert [b["name"] for b in response.json()] == ["Backup Co"]


def test_overpass_query_cannot_be_broken_out_of_by_a_category():
    query = OpenStreetMapProvider()._build_overpass_query('x"];node(1);out;("', 1.0, 2.0, 1.0)

    # Each of the four tag clauses keeps the term inside its own quotes.
    values = re.findall(r'~"([^"]*)",i\]', query)
    assert len(values) == 4
    assert all('"' not in value and "]" not in value for value in values)


def test_demo_rejects_oversized_or_odd_search_input(demo_search):
    client, calls = demo_search
    too_long = client.post("/api/businesses/search", json={"category": "a" * 81, "city": "Austin"})
    too_many_terms = client.post("/api/businesses/search", json={"category": "a,b,c,d", "city": "Austin"})
    long_place = client.post("/api/businesses/search/geocode", json={"place": "x" * 201})

    assert too_long.status_code == 422
    assert too_many_terms.status_code == 422
    assert long_place.status_code == 422
    assert calls == []


def test_demo_clamps_negative_radius_and_limit(demo_search):
    client, calls = demo_search

    response = client.post("/api/businesses/search", json={"category": "dentist", "city": "Austin", "radius_km": -5, "limit": -3})

    assert response.status_code == 200
    assert calls[0]["radius_km"] >= 0.5
    assert calls[0]["limit"] >= 1


def test_demo_rate_limit_uses_the_proxy_appended_address(demo_search):
    client, calls = demo_search
    statuses = [
        client.post(
            "/api/businesses/search",
            json={"category": "dentist", "city": f"Town {i}"},
            headers={"X-Forwarded-For": f"10.0.0.{i}, 203.0.113.9"},
        ).status_code
        for i in range(7)
    ]

    assert statuses[6] == 429  # forged first entries don't make a new visitor


def test_demo_geocode_has_its_own_per_visitor_limit(demo_search):
    client, _ = demo_search
    statuses = [client.post("/api/businesses/search/geocode", json={"place": f"Town {i}"}).status_code for i in range(21)]

    assert statuses[:20] == [200] * 20
    assert statuses[20] == 429


def test_demo_global_cap_and_rejected_visitors_are_not_remembered():
    from app.services.discovery import demo_limits

    limiter = demo_limits.DemoSearchLimiter()
    allowed = [limiter.allow(f"visitor-{i}") for i in range(demo_limits.GLOBAL_LIMIT + 5)]

    assert allowed.count(True) == demo_limits.GLOBAL_LIMIT
    assert len(limiter._visitors) == demo_limits.GLOBAL_LIMIT


def test_demo_search_writes_no_rows(demo_search):
    client, _ = demo_search
    client.post("/api/businesses/search", json={"category": "dentist", "city": "Austin"})
    blocked_save = client.post("/api/businesses/save", json={"businesses": [{"name": "Found Co", "source": "openstreetmap"}]})

    assert blocked_save.status_code == 403
