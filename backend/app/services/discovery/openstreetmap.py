import re

import httpx

from app.services.discovery.base import BusinessDiscoveryProvider, DiscoveredBusiness, social_url_from_tags
from app.services.discovery.ranking import rank_and_limit

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "ProspectOS/0.1 (internal prospecting tool; contact via repo)"

# The public Overpass API has a single canonical endpoint but several
# independently-run mirrors that share the same query language. The main
# instance (overpass-api.de) is free but shared/overloaded and frequently
# returns 504s under load, so we retry across mirrors before giving up
# rather than failing the whole search on one flaky instance.
#
# NOTE: overpass.osm.ch was tried and rejected here -- it's a fast-
# responding but *regional* (Swiss/EU) replica: it returns real results for
# Zurich but a silent, valid-looking empty list for New York or Austin.
# That's worse than an honest failure (looks like "no businesses here"
# instead of "wrong server"), so only full-planet mirrors belong in this
# list.
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# Common category -> (OSM tag key, OSM tag value) for a precise query.
# Categories not listed here fall back to a regex search across the most
# common business tag keys (shop/amenity/office/craft).
_CATEGORY_TAG_MAP: dict[str, tuple[str, str]] = {
    "plumber": ("craft", "plumber"),
    "electrician": ("craft", "electrician"),
    "dentist": ("amenity", "dentist"),
    "doctor": ("amenity", "doctors"),
    "restaurant": ("amenity", "restaurant"),
    "cafe": ("amenity", "cafe"),
    "bar": ("amenity", "bar"),
    "hairdresser": ("shop", "hairdresser"),
    "salon": ("shop", "hairdresser"),
    "gym": ("leisure", "fitness_centre"),
    "lawyer": ("office", "lawyer"),
    "accountant": ("office", "accountant"),
    "real_estate": ("office", "estate_agent"),
    "auto_repair": ("shop", "car_repair"),
    "car_repair": ("shop", "car_repair"),
    "veterinary": ("amenity", "veterinary"),
    "vet": ("amenity", "veterinary"),
    "bakery": ("shop", "bakery"),
    "florist": ("shop", "florist"),
    "clothing": ("shop", "clothes"),
    "hardware": ("shop", "hardware"),
    "pharmacy": ("amenity", "pharmacy"),
}


# Public so the API layer can offer these as real, known-good suggestions
# in the category input instead of a freeform box that silently fails for
# unrecognized terms (e.g. "Water" matches nothing).
KNOWN_CATEGORIES = sorted(_CATEGORY_TAG_MAP.keys())

# amenity=* values that are reliably a commercial/professional business
# (as opposed to public infrastructure like amenity=bench, amenity=toilets,
# amenity=waste_basket) -- used only for the no-category "sweep everything
# nearby" query in map mode, joined into a single regex alternation.
_BROAD_AMENITY_VALUES = "|".join(
    [
        "restaurant", "cafe", "bar", "pub", "fast_food", "food_court", "biergarten",
        "bank", "pharmacy", "dentist", "doctors", "clinic", "hospital", "veterinary",
        "cinema", "theatre", "nightclub", "casino",
        "fuel", "car_wash", "car_rental", "driving_school",
        "coworking_space", "conference_centre", "events_venue",
        "childcare", "kindergarten", "language_school", "music_school",
        "post_office", "money_transfer", "bureau_de_change",
    ]
)


class OpenStreetMapProvider(BusinessDiscoveryProvider):
    """Finds businesses via OSM's free Nominatim (geocoding) and Overpass
    (data query) APIs — no Google Maps scraping, no paid API keys (spec
    section 11). An httpx.Client can be injected for testing so no real
    network call is made in unit tests."""

    def __init__(self, http_client: httpx.Client | None = None):
        self._client = http_client or httpx.Client(
            timeout=30.0, headers={"User-Agent": USER_AGENT}
        )

    def discover(
        self,
        category: str | None = None,
        city: str | None = None,
        country: str | None = None,
        radius_km: float = 5.0,
        limit: int = 50,
        latitude: float | None = None,
        longitude: float | None = None,
        **kwargs,
    ) -> list[DiscoveredBusiness]:
        """`city` is geocoded via Nominatim unless `latitude`/`longitude` are
        given directly (map-based search), in which case geocoding is
        skipped entirely and the Overpass query centers on that point."""
        if latitude is not None and longitude is not None:
            lat, lon = latitude, longitude
        else:
            if not city:
                raise ValueError("Either city or latitude/longitude must be provided.")
            lat, lon = self._geocode(city, country)
        query = self._build_overpass_query(category, lat, lon, radius_km)
        elements = self._query_overpass(query)

        results: list[DiscoveredBusiness] = []
        for element in elements:
            tags = element.get("tags", {})
            name = tags.get("name")
            if not name:
                continue

            el_lat = element.get("lat")
            el_lon = element.get("lon")
            if el_lat is None and "center" in element:
                el_lat = element["center"].get("lat")
                el_lon = element["center"].get("lon")

            results.append(
                DiscoveredBusiness(
                    name=name,
                    category=tags.get("shop") or tags.get("amenity") or tags.get("office") or tags.get("craft") or category,
                    address=self._format_address(tags),
                    city=tags.get("addr:city") or city,
                    country=tags.get("addr:country") or country,
                    latitude=el_lat,
                    longitude=el_lon,
                    phone=tags.get("phone") or tags.get("contact:phone"),
                    email=tags.get("email") or tags.get("contact:email"),
                    website=tags.get("website") or tags.get("contact:website"),
                    social_url=social_url_from_tags(tags),
                    source="openstreetmap",
                    source_url=f"https://www.openstreetmap.org/{element['type']}/{element['id']}",
                )
            )

        # Rank by lead quality (no website, has contact info, has a real
        # address) before truncating to `limit` -- Overpass's own element
        # order is roughly database/insertion order, not relevance, so
        # slicing before ranking silently drops good leads in favor of
        # whatever happened to come first.
        return rank_and_limit(results, limit)

    def _query_overpass(self, query: str) -> list[dict]:
        last_error: Exception | None = None
        for mirror_url in OVERPASS_MIRRORS:
            try:
                # Generous on purpose: the primary instance (overpass-api.de)
                # fails fast when it's down, but working backup mirrors have
                # been observed taking 18s+ even for a small query -- a
                # tight timeout here means giving up on a mirror that would
                # have succeeded a few seconds later.
                response = self._client.post(mirror_url, data={"data": query}, timeout=55.0)
                response.raise_for_status()
                payload = response.json()
                # A server-side query timeout comes back as HTTP 200 with an
                # empty "elements" list and a "remark" explaining why --
                # left unchecked, that reads as "zero businesses here"
                # instead of "the search itself failed". Treat it as a
                # failure so we retry the next mirror instead of silently
                # reporting no results.
                remark = payload.get("remark", "")
                if "timed out" in remark.lower() or "timeout" in remark.lower():
                    last_error = ValueError(remark)
                    continue
                return payload.get("elements", [])
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                last_error = exc
                continue
        raise ValueError(
            "OpenStreetMap's Overpass API is temporarily unavailable or the query timed "
            "out on every mirror. Try again in a bit, or narrow the search (smaller radius "
            "or a more specific category)."
        ) from last_error

    def geocode(self, place: str) -> dict:
        """Public single-place geocode used by the map search box (recenter
        on a typed place name) and to validate a city before running the
        full discovery query. Returns the best match's coordinates and
        display name, or raises ValueError if nothing was found."""
        response = self._client.get(
            NOMINATIM_URL, params={"q": place, "format": "json", "limit": 1}
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError(f"Could not find a location matching {place!r}.")
        return {
            "latitude": float(data[0]["lat"]),
            "longitude": float(data[0]["lon"]),
            "display_name": data[0].get("display_name", place),
        }

    def _geocode(self, city: str, country: str | None) -> tuple[float, float]:
        query = city if not country else f"{city}, {country}"
        result = self.geocode(query)
        return result["latitude"], result["longitude"]

    def _build_overpass_query(self, category: str | None, lat: float, lon: float, radius_km: float) -> str:
        """Supports a comma-separated `category` (e.g. "cafe, restaurant")
        by unioning one clause per term into a single Overpass query --
        still exactly one network call, just matching more tags. A blank
        category (map mode, no filter typed) runs a broad sweep instead:
        any named place tagged shop/office/craft, or a curated set of
        clearly-commercial amenity values -- this deliberately excludes
        untagged infrastructure (benches, waste bins, etc.) that happens to
        carry a name, so "no filter" still means "businesses", not
        "literally everything on the map"."""
        radius_m = int(radius_km * 1000)
        if not category or not category.strip():
            return (
                f"[out:json][timeout:50];\n(\n"
                f'  nwr(around:{radius_m},{lat},{lon})["name"]["shop"];\n'
                f'  nwr(around:{radius_m},{lat},{lon})["name"]["office"];\n'
                f'  nwr(around:{radius_m},{lat},{lon})["name"]["craft"];\n'
                f'  nwr(around:{radius_m},{lat},{lon})["name"]["amenity"~"^({_BROAD_AMENITY_VALUES})$"];\n'
                f");\nout center tags;"
            )

        terms = [t.strip() for t in category.split(",") if t.strip()] or [category.strip()]

        clauses: list[str] = []
        for term in terms:
            known = _CATEGORY_TAG_MAP.get(term.lower())
            if known:
                key, value = known
                clauses.append(f'nwr(around:{radius_m},{lat},{lon})["name"]["{key}"="{value}"];')
            else:
                escaped = re.escape(term)
                clauses.extend(
                    f'nwr(around:{radius_m},{lat},{lon})["name"]["{key}"~"{escaped}",i];'
                    for key in ("shop", "amenity", "office", "craft")
                )

        clause = "\n  ".join(clauses)
        return f"[out:json][timeout:50];\n(\n  {clause}\n);\nout center tags;"

    @staticmethod
    def _format_address(tags: dict) -> str | None:
        parts = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
        ]
        parts = [p for p in parts if p]
        return " ".join(parts) if parts else None
