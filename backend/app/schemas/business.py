from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BusinessBase(BaseModel):
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
    social_url: str | None = None
    source: str | None = None
    source_url: str | None = None
    google_maps_url: str | None = None
    rating: float | None = None
    review_count: int | None = None
    website_status: str | None = None


class BusinessCreate(BusinessBase):
    """Used for manual entry (spec section 11: ManualProvider)."""


class BusinessUpdate(BaseModel):
    """All fields optional — PATCH semantics."""

    name: str | None = None
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
    social_url: str | None = None
    website_status: str | None = None


class BusinessRead(BusinessBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class BusinessListItem(BusinessRead):
    """List-endpoint row: the business plus a few fields pulled from its
    latest audit/status-history row, so the prospect table can show
    opportunity score and pipeline stage without a second round trip per
    row."""

    latest_opportunity_score: int | None = None
    latest_quality_category: str | None = None
    current_status: str | None = None
