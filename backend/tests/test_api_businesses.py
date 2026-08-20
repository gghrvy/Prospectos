import io

import app.api.businesses as businesses_api
from app.database.config import Settings
from app.services.discovery.base import DiscoveredBusiness
from app.services.discovery.geoapify import GeoapifyProvider
from app.services.discovery.openstreetmap import OpenStreetMapProvider


def _create_business(client, **overrides) -> dict:
    payload = {
        "name": "ABC Plumbing",
        "category": "Plumber",
        "city": "Houston",
    }
    payload.update(overrides)
    response = client.post("/api/businesses", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_get_business(client):
    created = _create_business(client)
    assert created["source"] == "manual"  # defaulted when not supplied

    response = client.get(f"/api/businesses/{created['id']}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["name"] == "ABC Plumbing"
    assert detail["current_status"] is None
    assert detail["latest_audit"] is None
    assert detail["notes"] == []


def test_get_business_not_found_returns_404(client):
    response = client.get("/api/businesses/does-not-exist")
    assert response.status_code == 404


def test_list_businesses_filters_and_paginates(client):
    _create_business(client, name="ABC Plumbing", city="Houston", category="Plumber")
    _create_business(client, name="XYZ Dental", city="Austin", category="Dentist")
    _create_business(client, name="Zeta Plumbing", city="Houston", category="Plumber")

    response = client.get("/api/businesses", params={"city": "Houston"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert {b["name"] for b in body["items"]} == {"ABC Plumbing", "Zeta Plumbing"}

    response = client.get("/api/businesses", params={"limit": 1, "offset": 0, "sort_by": "name", "sort_dir": "asc"})
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 1
    assert body["items"][0]["name"] == "ABC Plumbing"


def test_update_and_delete_business(client):
    created = _create_business(client)

    response = client.patch(f"/api/businesses/{created['id']}", json={"city": "Dallas"})
    assert response.status_code == 200
    assert response.json()["city"] == "Dallas"

    response = client.delete(f"/api/businesses/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/api/businesses/{created['id']}")
    assert response.status_code == 404


def test_add_note_and_change_status_appear_in_detail(client):
    created = _create_business(client)
    business_id = created["id"]

    note_response = client.post(f"/api/businesses/{business_id}/notes", json={"content": "Called, left voicemail."})
    assert note_response.status_code == 201

    status_response = client.post(f"/api/businesses/{business_id}/status", json={"status": "CONTACTED", "note": "Sent outreach"})
    assert status_response.status_code == 201

    detail = client.get(f"/api/businesses/{business_id}").json()
    assert detail["current_status"] == "CONTACTED"
    assert len(detail["notes"]) == 1
    assert len(detail["status_history"]) == 1


def test_csv_export_and_import_round_trip(client):
    _create_business(client, name="ABC Plumbing", city="Houston")

    export_response = client.get("/api/businesses/export-csv")
    assert export_response.status_code == 200
    assert "ABC Plumbing" in export_response.text

    csv_text = "name,city,category\nNew Import Co,Miami,Restaurant\n"
    files = {"file": ("prospects.csv", io.BytesIO(csv_text.encode()), "text/csv")}
    import_response = client.post("/api/businesses/import-csv", files=files)
    assert import_response.status_code == 200
    body = import_response.json()
    assert body["imported"] == 1
    assert body["businesses"][0]["name"] == "New Import Co"

    # Re-importing the same row should be deduped.
    import_response_2 = client.post("/api/businesses/import-csv", files=files)
    assert import_response_2.json()["imported"] == 0
    assert import_response_2.json()["skipped_duplicates"] == 1


def test_search_returns_candidates_without_saving_by_default(client, monkeypatch):
    def fake_discover(self, **kwargs):
        return [DiscoveredBusiness(name="Found Co", city=kwargs["city"], source="openstreetmap")]

    monkeypatch.setattr(OpenStreetMapProvider, "discover", fake_discover)

    response = client.post("/api/businesses/search", json={"category": "plumber", "city": "Austin"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Found Co"

    # Not saved: business list should still be empty.
    listing = client.get("/api/businesses").json()
    assert listing["total"] == 0


def test_search_with_save_persists_businesses(client, monkeypatch):
    def fake_discover(self, **kwargs):
        return [DiscoveredBusiness(name="Saved Co", city=kwargs["city"], source="openstreetmap")]

    monkeypatch.setattr(OpenStreetMapProvider, "discover", fake_discover)

    response = client.post(
        "/api/businesses/search",
        json={"category": "plumber", "city": "Austin", "save": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body[0]["name"] == "Saved Co"
    assert "id" in body[0]

    listing = client.get("/api/businesses").json()
    assert listing["total"] == 1


def test_search_invalid_location_returns_400(client, monkeypatch):
    def fake_discover(self, **kwargs):
        raise ValueError("Could not geocode location: 'Nowhereville'")

    monkeypatch.setattr(OpenStreetMapProvider, "discover", fake_discover)

    response = client.post("/api/businesses/search", json={"category": "plumber", "city": "Nowhereville"})
    assert response.status_code == 400


def test_save_selected_businesses_persists_only_the_chosen_ones(client):
    response = client.post(
        "/api/businesses/save",
        json={
            "businesses": [
                {"name": "Picked Cafe", "city": "Austin", "source": "geoapify"},
                {"name": "Also Picked", "city": "Austin", "source": "openstreetmap"},
            ]
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert {b["name"] for b in body} == {"Picked Cafe", "Also Picked"}

    listing = client.get("/api/businesses").json()
    assert listing["total"] == 2


def test_save_selected_businesses_dedupes_against_existing(client):
    _create_business(client, name="Existing Co", city="Austin", category="Cafe")

    response = client.post(
        "/api/businesses/save",
        json={"businesses": [{"name": "Existing Co", "city": "Austin", "source": "geoapify"}]},
    )
    assert response.status_code == 201
    assert response.json() == []

    listing = client.get("/api/businesses").json()
    assert listing["total"] == 1  # not duplicated


def test_search_falls_back_to_geoapify_when_osm_fails_and_key_configured(client, monkeypatch):
    def osm_fails(self, **kwargs):
        raise ValueError("OpenStreetMap's Overpass API is temporarily unavailable...")

    def geoapify_succeeds(self, **kwargs):
        return [DiscoveredBusiness(name="Fallback Co", city=kwargs.get("city"), source="geoapify")]

    monkeypatch.setattr(OpenStreetMapProvider, "discover", osm_fails)
    monkeypatch.setattr(GeoapifyProvider, "discover", geoapify_succeeds)
    monkeypatch.setattr(
        businesses_api, "get_settings", lambda: Settings(geoapify_api_key="fake-key", database_url="sqlite://")
    )

    response = client.post("/api/businesses/search", json={"category": "cafe", "city": "Austin"})
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Fallback Co"


def test_search_reports_both_errors_when_osm_and_geoapify_both_fail(client, monkeypatch):
    def osm_fails(self, **kwargs):
        raise ValueError("OSM down")

    def geoapify_fails(self, **kwargs):
        raise ValueError("Geoapify has no category matching 'plumber'")

    monkeypatch.setattr(OpenStreetMapProvider, "discover", osm_fails)
    monkeypatch.setattr(GeoapifyProvider, "discover", geoapify_fails)
    monkeypatch.setattr(
        businesses_api, "get_settings", lambda: Settings(geoapify_api_key="fake-key", database_url="sqlite://")
    )

    response = client.post("/api/businesses/search", json={"category": "plumber", "city": "Austin"})
    assert response.status_code == 400
    assert "OSM down" in response.json()["detail"]
    assert "no category matching" in response.json()["detail"]
