"""Short-lived in-memory cache for discovery search results.

Purpose: during real usage (and especially a live demo) it's common to
re-run essentially the same search a few times in a row -- re-clicking
"Search this area", re-loading a page, narrating the same query twice.
When that repeat search would otherwise cost a metered Geoapify call, this
cache answers it for free instead. It's intentionally simple (in-process
dict, no persistence) since ProspectOS runs as a single local backend
process; it does not need to survive a restart.
"""

from __future__ import annotations

import time

DEFAULT_TTL_SECONDS = 3600  # 1 hour: long enough to absorb demo-style
# re-clicking, short enough that stale results never linger for long.


class SearchCache:
    def __init__(self, ttl_seconds: float = DEFAULT_TTL_SECONDS):
        self._ttl = ttl_seconds
        self._store: dict[tuple, tuple[float, list]] = {}

    @staticmethod
    def make_key(
        provider: str,
        category: str,
        city: str | None,
        country: str | None,
        latitude: float | None,
        longitude: float | None,
        radius_km: float,
        limit: int,
    ) -> tuple:
        # Coordinates rounded to 3 decimal places (~110m precision) so a
        # pixel-level drag of the map pin still hits the same cache entry
        # instead of missing on a near-identical search.
        return (
            provider,
            category.lower().strip(),
            (city or "").lower().strip(),
            (country or "").lower().strip(),
            round(latitude, 3) if latitude is not None else None,
            round(longitude, 3) if longitude is not None else None,
            round(radius_km, 2),
            limit,
        )

    def get(self, key: tuple) -> list | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        cached_at, results = entry
        if time.monotonic() - cached_at >= self._ttl:
            del self._store[key]
            return None
        return results

    def set(self, key: tuple, results: list) -> None:
        self._store[key] = (time.monotonic(), results)

    def clear(self) -> None:
        self._store.clear()


# Module-level singleton -- shared across requests within this process.
search_cache = SearchCache()
