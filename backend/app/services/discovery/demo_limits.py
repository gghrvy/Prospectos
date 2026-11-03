"""Guards for the one live integration the public demo exposes: discovery search.

Anyone can reach the demo, and OpenStreetMap's Overpass service throttles
servers that query it too often. So demo searches are capped in size, limited
per visitor and in total, and repeats are answered from a short-lived cache.
In-process state only: the demo runs as a single backend process.
"""

from __future__ import annotations

import time
from collections import deque

from app.services.discovery.search_cache import SearchCache

DEMO_MAX_RESULTS = 25
DEMO_MAX_RADIUS_KM = 10.0
PER_VISITOR_LIMIT = 6
# Place lookups run as the visitor types a city, so they get more room.
GEOCODE_PER_VISITOR_LIMIT = 20
PER_VISITOR_WINDOW_SECONDS = 60.0
GLOBAL_LIMIT = 120  # searches and place lookups together
GLOBAL_WINDOW_SECONDS = 3600.0
CACHE_MAX_ENTRIES = 500
MAX_CATEGORY_LENGTH = 80
MAX_CATEGORY_TERMS = 3
MAX_PLACE_LENGTH = 200


class DemoSearchLimiter:
    def __init__(self) -> None:
        self._visitors: dict[str, deque[float]] = {}
        self._all: deque[float] = deque()
        self.cache = SearchCache()

    def allow(self, visitor: str, limit: int = PER_VISITOR_LIMIT) -> bool:
        """Records the search and returns True, or returns False when the
        visitor or the demo as a whole is over its limit."""
        now = time.monotonic()
        hits = self._visitors.get(visitor, deque())
        _drop_older_than(hits, now - PER_VISITOR_WINDOW_SECONDS)
        _drop_older_than(self._all, now - GLOBAL_WINDOW_SECONDS)
        if len(hits) >= limit or len(self._all) >= GLOBAL_LIMIT:
            return False
        hits.append(now)
        self._visitors[visitor] = hits
        self._all.append(now)
        # Forget visitors whose window has emptied so the dict can't grow forever.
        for key in [key for key, value in self._visitors.items() if not value]:
            del self._visitors[key]
        return True

    def remember(self, key: tuple, results: list) -> None:
        # The shared cache only evicts on read; cap it so a public demo can't
        # grow it without bound.
        if len(self.cache._store) >= CACHE_MAX_ENTRIES:
            self.cache.clear()
        self.cache.set(key, results)

    def reset(self) -> None:
        self._visitors.clear()
        self._all.clear()
        self.cache.clear()


def _drop_older_than(hits: deque[float], cutoff: float) -> None:
    while hits and hits[0] <= cutoff:
        hits.popleft()


demo_search_limiter = DemoSearchLimiter()
