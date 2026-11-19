import json

import httpx
import pytest

from app.services.discovery.apify import ApifyBudgetError, ApifyGoogleMapsProvider, map_place

PLACE = {
    "title": "Cool Air Plumbing",
    "categoryName": "Plumber",
    "address": "1 Main St, Tampa, FL 33602",
    "city": "Tampa",
    "state": "Florida",
    "countryCode": "US",
    "location": {"lat": 27.95, "lng": -82.45},
    "phone": "(813) 555-0100",
    "website": "https://coolairplumbing.com/",
    "emails": ["Info@CoolAirPlumbing.com"],
    "facebooks": ["https://facebook.com/coolair"],
    "url": "https://www.google.com/maps/place/?q=place_id:abc",
    "totalScore": 4.7,
    "reviewsCount": 212,
}


def _client(usage_usd, items=None, calls=None, limits_status=200):
    def handler(request: httpx.Request):
        if calls is not None:
            calls.append(request)
        if request.url.path.endswith("/users/me/limits"):
            if limits_status != 200:
                return httpx.Response(limits_status, json={})
            return httpx.Response(200, json={"data": {"current": {"monthlyUsageUsd": usage_usd},
                                                      "limits": {"maxMonthlyUsageUsd": 5}}})
        return httpx.Response(201, json=items or [])
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_map_place_keeps_real_fields_and_lowercases_email():
    b = map_place(PLACE, "plumber")
    assert b.name == "Cool Air Plumbing" and b.category == "plumber"
    assert b.email == "info@coolairplumbing.com"
    assert b.source == "apify_google_maps" and b.review_count == 212
    assert b.social_url == "https://facebook.com/coolair"


def test_closed_place_is_dropped():
    assert map_place({**PLACE, "permanentlyClosed": True}, "plumber") is None


def test_run_passes_hard_charge_cap_and_result_cap():
    calls = []
    provider = ApifyGoogleMapsProvider("tok", monthly_budget_usd=4.5, max_results=50,
                                       client=_client(1.0, [PLACE], calls))
    results = provider.discover(category="plumber", city="Tampa", country="US", limit=500)
    assert [r.name for r in results] == ["Cool Air Plumbing"]
    run = calls[-1]
    assert run.url.params["maxTotalChargeUsd"] == "0.5"  # Apify's minimum cap
    assert run.url.params["maxItems"] == "50"
    body = json.loads(run.content)
    assert body["maxCrawledPlacesPerSearch"] == 50 and body["scrapeContacts"] is True
    assert body["locationQuery"] == "Tampa, US"


def test_refuses_when_run_could_exceed_budget():
    calls = []
    provider = ApifyGoogleMapsProvider("tok", monthly_budget_usd=4.5, client=_client(4.3, [PLACE], calls))
    with pytest.raises(ApifyBudgetError):
        provider.discover(category="plumber", city="Tampa", limit=50)
    assert all("run-sync" not in str(c.url) for c in calls)  # nothing was run


def test_refuses_when_usage_cannot_be_read():
    calls = []
    provider = ApifyGoogleMapsProvider("tok", client=_client(0, [PLACE], calls, limits_status=500))
    with pytest.raises(ApifyBudgetError):
        provider.discover(category="plumber", city="Tampa")
    assert all("run-sync" not in str(c.url) for c in calls)


def test_search_endpoint_google_maps_without_token_is_400(client, monkeypatch):
    from app.database.config import get_settings

    monkeypatch.setattr(get_settings(), "apify_token", None)
    response = client.post("/api/businesses/search",
                           json={"category": "plumber", "city": "Tampa", "source": "google_maps"})
    assert response.status_code == 400
    assert "APIFY_TOKEN" in response.json()["detail"]
