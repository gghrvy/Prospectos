from abc import ABC, abstractmethod

from pydantic import BaseModel


class DiscoveredBusiness(BaseModel):
    """Provider-agnostic result shape. Every BusinessDiscoveryProvider
    returns a list of these; the API layer converts them into `Business`
    rows. Nothing here is fabricated — providers leave fields None rather
    than guessing."""

    name: str
    category: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    # A Facebook or Instagram page, when the source data has one but no
    # website -- common for small local businesses that use a social page
    # as their whole web presence. Not automated (no DM-sending feature),
    # but it's a real, clickable contact path for the no-website case
    # where there's otherwise no automated way in at all.
    social_url: str | None = None
    source: str
    source_url: str | None = None
    google_maps_url: str | None = None
    rating: float | None = None
    review_count: int | None = None


def social_url_from_tags(tags: dict) -> str | None:
    """Builds a real, clickable social-page URL from OSM-style contact
    tags, checking Facebook first (Messenger is the more common direct-
    contact channel for local businesses) then Instagram. Tag values are
    inconsistent in the wild -- sometimes a full URL, sometimes just a
    page handle -- so this normalizes both instead of assuming one shape.
    Returns None if no social tag is present, never guesses a URL from a
    business name."""
    for key in ("contact:facebook", "facebook"):
        value = tags.get(key)
        if value:
            return value if value.startswith("http") else f"https://www.facebook.com/{value}"
    for key in ("contact:instagram", "instagram"):
        value = tags.get(key)
        if value:
            return value if value.startswith("http") else f"https://www.instagram.com/{value}"
    return None


class BusinessDiscoveryProvider(ABC):
    """Abstraction over "where do candidate businesses come from" (spec
    section 11). Concrete providers: OpenStreetMapProvider (primary, free,
    no key), GeoapifyProvider (optional automatic fallback when OSM's
    Overpass API is down -- free tier, no credit card, opt-in via an API
    key), CSVProvider, ManualProvider. No provider may scrape Google Maps
    or call a paid API."""

    @abstractmethod
    def discover(self, **kwargs) -> list[DiscoveredBusiness]:
        raise NotImplementedError
