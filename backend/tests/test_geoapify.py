import httpx
import pytest

from app.services.discovery import GeoapifyProvider
from app.services.discovery.geoapify import _resolve_category
from app.services.discovery.search_cache import SearchCache


def test_geoapify_provider_geocodes_then_queries_places():
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocode" in str(request.url):
            return httpx.Response(
                200,
                json={"features": [{"geometry": {"coordinates": [-97.7431, 30.2672]}, "properties": {"formatted": "Austin, TX, USA"}}]},
            )
        if "/v2/places" in str(request.url):
            assert "categories=catering.cafe" in str(request.url)
            return httpx.Response(
                200,
                json={
                    "features": [
                        {
                            "properties": {
                                # address_line1 is the NAME in Geoapify's own
                                "name": "Corner Cafe",
                                "address_line1": "Corner Cafe",
                                "street": "Main St",
                                "housenumber": "100",
                                "city": "Austin",
                                "state": "TX",
                                "country": "USA",
                                "lat": 30.27,
                                "lon": -97.74,
                                "website": "https://cornercafe.example",
                                "contact": {"phone": "555-1234", "email": "hi@cornercafe.example"},
                                "place_id": "abc123",
                                "datasource": {
                                    "sourcename": "openstreetmap",
                                    "raw": {"osm_type": "n", "osm_id": 999},
                                },
                            }
                        },
                        {"properties": {"address_line1": "no name here"}},  # no name -> skipped
                    ]
                },
            )
        raise AssertionError(f"unexpected request to {request.url}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeoapifyProvider(api_key="fake-key", http_client=client)

    results = provider.discover(category="cafe", city="Austin", country="USA", radius_km=5)

    assert len(results) == 1
    business = results[0]
    assert business.name == "Corner Cafe"
    assert business.source == "geoapify"
    assert business.city == "Austin"
    assert business.state == "TX"
    assert business.address == "100 Main St"
    assert business.phone == "555-1234"
    assert business.email == "hi@cornercafe.example"
    assert business.website == "https://cornercafe.example"
    assert business.source_url == "https://www.openstreetmap.org/node/999"


def test_geoapify_provider_raises_on_unmapped_category():
    provider = GeoapifyProvider(api_key="fake-key", http_client=httpx.Client())

    with pytest.raises(ValueError, match="no category matching"):
        provider.discover(category="plumber", city="Austin")


def test_geoapify_provider_uses_latitude_longitude_directly_without_geocoding():
    def handler(request: httpx.Request) -> httpx.Response:
        if "geocode" in str(request.url):
            raise AssertionError("should not geocode when lat/lon are given")
        return httpx.Response(200, json={"features": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeoapifyProvider(api_key="fake-key", http_client=client)

    results = provider.discover(category="cafe", latitude=30.27, longitude=-97.74, radius_km=3)
    assert results == []


def test_geoapify_provider_raises_when_location_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"features": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeoapifyProvider(api_key="fake-key", http_client=client)

    with pytest.raises(ValueError):
        provider.discover(category="cafe", city="Nowhereville")


def test_resolve_category_multi_term_ors_them_together():
    resolved = _resolve_category("cafe, restaurant")
    assert resolved == "catering.cafe,catering.restaurant"


def test_resolve_category_falls_back_to_substring_match_for_unmapped_term():
    # "sushi" isn't in the curated dict but is a real Geoapify subcategory
    # (catering.restaurant.sushi) -- should resolve via substring fallback
    # instead of failing, without fabricating a category that doesn't exist.
    assert _resolve_category("sushi") == "catering.restaurant.sushi"


def test_resolve_category_still_raises_for_truly_unmapped_term():
    with pytest.raises(ValueError, match="no category matching"):
        _resolve_category("plumber")


def test_geoapify_provider_uses_multiple_categories_in_one_request():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "geocode" in str(request.url):
            return httpx.Response(
                200,
                json={"features": [{"geometry": {"coordinates": [-97.7431, 30.2672]}, "properties": {}}]},
            )
        calls.append(str(request.url))
        assert "categories=catering.cafe%2Ccatering.restaurant" in str(request.url)
        return httpx.Response(200, json={"features": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeoapifyProvider(api_key="fake-key", http_client=client)

    provider.discover(category="cafe, restaurant", city="Austin")
    assert len(calls) == 1  # one API call, not two


def test_geoapify_provider_reuses_cached_result_without_a_second_call():
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            json={"features": [{"properties": {"name": "Cached Cafe", "lat": 30.27, "lon": -97.74}}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeoapifyProvider(api_key="fake-key", http_client=client)
    provider._client = client  # noqa: SLF001 -- test wiring

    from app.services.discovery import geoapify as geoapify_module

    geoapify_module.search_cache.clear()

    first = provider.discover(category="cafe", latitude=30.27, longitude=-97.74, radius_km=3)
    second = provider.discover(category="cafe", latitude=30.27, longitude=-97.74, radius_km=3)

    assert call_count == 1
    assert first == second
    assert first[0].name == "Cached Cafe"

    geoapify_module.search_cache.clear()


def test_resolve_category_blank_sweeps_all_business_categories():
    from app.services.discovery.geoapify import _BROAD_SWEEP_CATEGORIES

    assert _resolve_category("") == _BROAD_SWEEP_CATEGORIES
    assert _resolve_category(None) == _BROAD_SWEEP_CATEGORIES
    assert "commercial" in _BROAD_SWEEP_CATEGORIES
    assert "office" in _BROAD_SWEEP_CATEGORIES


def test_geoapify_provider_discovers_without_a_category():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "categories=accommodation%2Cactivity%2Ccommercial" in str(request.url)
        return httpx.Response(
            200, json={"features": [{"properties": {"name": "Any Business", "lat": 40.71, "lon": -74.0}}]}
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeoapifyProvider(api_key="fake-key", http_client=client)

    results = provider.discover(latitude=40.71, longitude=-74.0, radius_km=1)
    assert len(results) == 1
    assert results[0].name == "Any Business"


def test_search_cache_expires_after_ttl():
    cache = SearchCache(ttl_seconds=0)
    key = cache.make_key("geoapify", "cafe", "Austin", None, None, None, 5.0, 50)
    cache.set(key, ["placeholder"])
    assert cache.get(key) is None  # expired immediately with ttl=0
