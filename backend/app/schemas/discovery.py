from pydantic import BaseModel, model_validator

from app.services.discovery.base import DiscoveredBusiness


class OSMSearchRequest(BaseModel):
    # Optional: map mode (an exact pinned point + radius) can search with no
    # category at all -- a broad sweep of business-relevant tags -- since
    # requiring a specific term defeats the point of "show me what's here".
    # City mode still enforces one in the frontend, where a vaguer, larger
    # search area makes an unfiltered sweep less useful.
    category: str | None = None
    city: str | None = None
    country: str | None = None
    radius_km: float = 5.0
    limit: int = 50
    save: bool = False
    # Map-based search: an exact clicked point, skipping city geocoding.
    latitude: float | None = None
    longitude: float | None = None

    @model_validator(mode="after")
    def _require_city_or_coordinates(self) -> "OSMSearchRequest":
        has_coordinates = self.latitude is not None and self.longitude is not None
        if not self.city and not has_coordinates:
            raise ValueError("Either city or latitude/longitude must be provided.")
        return self


class GeocodeRequest(BaseModel):
    place: str


class GeocodeResult(BaseModel):
    latitude: float
    longitude: float
    display_name: str


class SaveBusinessesRequest(BaseModel):
    """Saves a specific set of already-fetched search results (e.g. the
    rows a user checked in Discover) without re-running discovery -- so
    picking a few prospects out of a batch doesn't cost a second Overpass/
    Geoapify call just to persist them."""

    businesses: list[DiscoveredBusiness]
