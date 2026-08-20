import re

from app.models.business import Business
from app.services.discovery.base import DiscoveredBusiness


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone)


def _normalize_website(website: str) -> str:
    website = website.lower().strip()
    website = re.sub(r"^https?://", "", website)
    website = re.sub(r"^www\.", "", website)
    return website.rstrip("/")


def _existing_keys(existing: list[Business]) -> tuple[set[str], set[str], set[tuple[str, str]]]:
    phones: set[str] = set()
    websites: set[str] = set()
    name_city: set[tuple[str, str]] = set()

    for business in existing:
        if business.phone:
            phones.add(_normalize_phone(business.phone))
        if business.website:
            websites.add(_normalize_website(business.website))
        name_city.add((_normalize_name(business.name), (business.city or "").lower().strip()))

    return phones, websites, name_city


def deduplicate_businesses(
    existing: list[Business], candidates: list[DiscoveredBusiness]
) -> list[DiscoveredBusiness]:
    """Filters `candidates` down to ones that don't already exist in
    `existing`, matching on (in priority order): normalized phone number,
    normalized website domain, or (normalized name, city) pair. Also drops
    duplicates within `candidates` itself using the same rules."""

    seen_phones, seen_websites, seen_name_city = _existing_keys(existing)
    unique: list[DiscoveredBusiness] = []

    for candidate in candidates:
        phone_key = _normalize_phone(candidate.phone) if candidate.phone else None
        website_key = _normalize_website(candidate.website) if candidate.website else None
        name_city_key = (_normalize_name(candidate.name), (candidate.city or "").lower().strip())

        if phone_key and phone_key in seen_phones:
            continue
        if website_key and website_key in seen_websites:
            continue
        if name_city_key in seen_name_city:
            continue

        unique.append(candidate)

        if phone_key:
            seen_phones.add(phone_key)
        if website_key:
            seen_websites.add(website_key)
        seen_name_city.add(name_city_key)

    return unique
