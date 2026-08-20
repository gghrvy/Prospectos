import httpx
import pytest

from app.models.business import Business
from app.services.discovery import (
    CSVProvider,
    ManualProvider,
    OpenStreetMapProvider,
    deduplicate_businesses,
)
from app.services.discovery.base import social_url_from_tags


def test_manual_provider_wraps_single_business():
    provider = ManualProvider()
    results = provider.discover(name="Joe's Plumbing", city="Austin", category="Plumber")

    assert len(results) == 1
    assert results[0].name == "Joe's Plumbing"
    assert results[0].source == "manual"


def test_csv_provider_parses_and_maps_columns():
    csv_text = (
        "business_name,type,City,Phone Number,website\n"
        "ABC Plumbing,Plumber,Houston,555-1234,https://abcplumbing.com\n"
        ",,,, \n"  # missing name -> skipped
    )
    provider = CSVProvider()
    results = provider.discover(csv_text=csv_text)

    assert len(results) == 1
    business = results[0]
    assert business.name == "ABC Plumbing"
    assert business.category == "Plumber"
    assert business.city == "Houston"
    assert business.phone == "555-1234"  # "Phone Number" header normalizes to phone_number alias
    assert business.website == "https://abcplumbing.com"
    assert business.source == "csv"


def test_csv_provider_requires_name_column_mapping_case_insensitive():
    csv_text = "NAME,CITY\nJane's Bakery,Denver\n"
    provider = CSVProvider()
    results = provider.discover(csv_text=csv_text)

    assert len(results) == 1
    assert results[0].name == "Jane's Bakery"


def test_deduplicate_businesses_filters_by_phone_website_and_name_city():
    existing = [
        Business(name="ABC Plumbing", category="Plumber", city="Houston", phone="555-000-1234"),
        Business(name="City Dental", category="Dentist", city="Austin", website="https://citydental.com"),
    ]

    csv_text = (
        "name,city,phone\n"
        "ABC Plumbing,Houston,(555) 000-1234\n"  # dup by phone (different formatting)
        "New Plumbing Co,Houston,555-999-8888\n"  # not a dup
    )
    provider = CSVProvider()
    candidates = provider.discover(csv_text=csv_text)

    unique = deduplicate_businesses(existing, candidates)

    assert len(unique) == 1
    assert unique[0].name == "New Plumbing Co"


def test_deduplicate_businesses_drops_duplicates_within_candidates_too():
    provider = CSVProvider()
    csv_text = (
        "name,city\n"
        "Same Shop,Miami\n"
        "same shop,Miami\n"  # dup of the row above, case-insensitive
    )
    candidates = provider.discover(csv_text=csv_text)

    unique = deduplicate_businesses([], candidates)

    assert len(unique) == 1


def test_openstreetmap_provider_geocodes_then_queries_overpass():
    def handler(request: httpx.Request) -> httpx.Response:
        if "nominatim" in str(request.url):
            return httpx.Response(200, json=[{"lat": "30.2672", "lon": "-97.7431"}])
        if "overpass" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "elements": [
                        {
                            "type": "node",
                            "id": 123,
                            "lat": 30.27,
                            "lon": -97.74,
                            "tags": {
                                "name": "Joe's Plumbing",
                                "craft": "plumber",
                                "phone": "555-1234",
                                "website": "https://joesplumbing.com",
                                "addr:housenumber": "100",
                                "addr:street": "Main St",
                            },
                        },
                        {"type": "node", "id": 124, "lat": 30.28, "lon": -97.75, "tags": {}},  # no name -> skipped
                    ]
                },
            )
        raise AssertionError(f"unexpected request to {request.url}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenStreetMapProvider(http_client=client)

    results = provider.discover(category="plumber", city="Austin", country="USA", radius_km=5)

    assert len(results) == 1
    business = results[0]
    assert business.name == "Joe's Plumbing"
    assert business.source == "openstreetmap"
    assert business.phone == "555-1234"
    assert business.website == "https://joesplumbing.com"
    assert business.address == "100 Main St"
    assert business.latitude == 30.27


def test_openstreetmap_provider_sweeps_broadly_with_no_category():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "overpass" in str(request.url)
        import urllib.parse

        body = urllib.parse.unquote(request.content.decode())
        # Broad sweep should query shop/office/craft plus the curated
        # commercial-amenity regex, not a single narrow tag.
        assert '["shop"]' in body
        assert '["office"]' in body
        assert '["craft"]' in body
        assert "amenity" in body and "restaurant" in body
        return httpx.Response(
            200,
            json={
                "elements": [
                    {"type": "node", "id": 1, "lat": 40.71, "lon": -74.0, "tags": {"name": "Any Business", "shop": "yes"}}
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenStreetMapProvider(http_client=client)

    results = provider.discover(latitude=40.71, longitude=-74.0, radius_km=1)
    assert len(results) == 1
    assert results[0].name == "Any Business"


def test_social_url_from_tags_prefers_facebook_and_builds_full_url_from_handle():
    assert social_url_from_tags({"facebook": "DominiqueAnselBakery"}) == "https://www.facebook.com/DominiqueAnselBakery"


def test_social_url_from_tags_passes_through_full_url_unchanged():
    url = "https://www.facebook.com/burdickchocolate"
    assert social_url_from_tags({"contact:facebook": url}) == url


def test_social_url_from_tags_falls_back_to_instagram():
    assert social_url_from_tags({"contact:instagram": "springcafenyc"}) == "https://www.instagram.com/springcafenyc"


def test_social_url_from_tags_returns_none_when_no_social_tags():
    assert social_url_from_tags({"name": "No Social Co", "phone": "555-1234"}) is None


def test_openstreetmap_provider_raises_when_location_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenStreetMapProvider(http_client=client)

    with pytest.raises(ValueError):
        provider.discover(category="plumber", city="Nowhereville")
