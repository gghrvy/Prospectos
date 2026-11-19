"""Google Maps discovery through Apify's Google Maps Scraper
(compass/crawler-google-places), run with the user's own Apify token.

Why it exists: OpenStreetMap rarely carries emails or even complete
business lists for trades. Google Maps does, and the actor's contact
enrichment reads each business's own website for its public email.

Spending guard (the account owner asked to never spend real money):
  1. Before every run, the account's usage this month is read from the
     Apify API. If it can't be read, the run is refused (fail closed).
  2. If usage plus this run's worst case would reach the monthly budget
     (default $4.50, under the free plan's $5 credit), the run is refused.
  3. Every run is started with maxTotalChargeUsd, so Apify itself stops
     the run at that amount even if something else goes wrong.
  4. Each run is capped at APIFY_MAX_RESULTS places (default 50).
With no payment method on the Apify account, usage past the free credit
can't be billed anyway; these checks keep searches from failing midway
and leave a buffer.
"""

from __future__ import annotations

import httpx

from app.services.discovery.base import BusinessDiscoveryProvider, DiscoveredBusiness

API_BASE = "https://api.apify.com/v2"
ACTOR_ID = "compass~crawler-google-places"

# Worst-case cost per place on the free plan: place scrape (~$0.004) plus
# contact-details enrichment. Rounded up on purpose so the pre-run check
# is conservative.
WORST_CASE_USD_PER_PLACE = 0.008
RUN_TIMEOUT_SECONDS = 290
# Apify rejects maxTotalChargeUsd below this (observed error
# "max-total-charge-usd-below-minimum"), so every run is capped at least here.
MIN_RUN_CHARGE_CAP_USD = 0.50


class ApifyBudgetError(ValueError):
    """The run would go over the monthly budget, or usage couldn't be read."""


def read_monthly_usage(token: str, client: httpx.Client | None = None) -> dict:
    """Returns {"used_usd", "plan_limit_usd"} for the current billing month.
    Raises ApifyBudgetError if Apify can't be reached or the shape is
    unexpected: no usage figure means no run."""
    owns = client is None
    client = client or httpx.Client(timeout=20)
    try:
        response = client.get(f"{API_BASE}/users/me/limits", params={"token": token})
    except httpx.HTTPError as exc:
        raise ApifyBudgetError(f"Couldn't check Apify usage ({exc}); search not run.") from exc
    finally:
        if owns:
            client.close()
    if response.status_code == 401:
        raise ApifyBudgetError("Apify rejected the token. Check APIFY_TOKEN in backend/.env.")
    if response.status_code >= 400:
        raise ApifyBudgetError(f"Couldn't check Apify usage (HTTP {response.status_code}); search not run.")
    data = (response.json() or {}).get("data") or {}
    used = (data.get("current") or {}).get("monthlyUsageUsd")
    limit = (data.get("limits") or {}).get("maxMonthlyUsageUsd")
    if not isinstance(used, (int, float)):
        raise ApifyBudgetError("Apify didn't report this month's usage; search not run.")
    return {"used_usd": round(float(used), 4), "plan_limit_usd": limit}


def _location_query(city: str | None, country: str | None) -> str:
    return ", ".join(part for part in (city, country) if part)


def _first(values) -> str | None:
    if isinstance(values, list):
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def map_place(item: dict, category: str | None) -> DiscoveredBusiness | None:
    """One actor output row -> DiscoveredBusiness. Missing fields stay None."""
    name = (item.get("title") or "").strip()
    if not name or item.get("permanentlyClosed"):
        return None
    location = item.get("location") or {}
    emails = [e.strip().lower() for e in (item.get("emails") or []) if isinstance(e, str) and "@" in e]
    return DiscoveredBusiness(
        name=name,
        category=category or item.get("categoryName"),
        address=item.get("address") or item.get("street"),
        city=item.get("city"),
        state=item.get("state"),
        country=item.get("countryCode"),
        latitude=location.get("lat"),
        longitude=location.get("lng"),
        phone=item.get("phone") or item.get("phoneUnformatted"),
        email=emails[0] if emails else None,
        website=item.get("website"),
        social_url=_first(item.get("facebooks")) or _first(item.get("instagrams")),
        source="apify_google_maps",
        source_url=item.get("url"),
        google_maps_url=item.get("url"),
        rating=item.get("totalScore"),
        review_count=item.get("reviewsCount"),
    )


class ApifyGoogleMapsProvider(BusinessDiscoveryProvider):
    def __init__(self, token: str, monthly_budget_usd: float = 4.5, max_results: int = 50,
                 client: httpx.Client | None = None):
        if not token:
            raise ValueError("APIFY_TOKEN is not set in backend/.env.")
        self.token = token
        self.monthly_budget_usd = monthly_budget_usd
        self.max_results = max_results
        self._client = client

    def _http(self) -> httpx.Client:
        return self._client or httpx.Client(timeout=RUN_TIMEOUT_SECONDS + 30)

    def check_budget(self, places: int) -> dict:
        client = self._http()
        try:
            usage = read_monthly_usage(self.token, client)
        finally:
            if self._client is None:
                client.close()
        run_cap = max(MIN_RUN_CHARGE_CAP_USD, round(places * WORST_CASE_USD_PER_PLACE, 2))
        remaining = round(self.monthly_budget_usd - usage["used_usd"], 4)
        if run_cap > remaining:
            raise ApifyBudgetError(
                f"Apify budget guard: ${usage['used_usd']:.2f} used this month, budget ${self.monthly_budget_usd:.2f}. "
                f"This search could cost up to ${run_cap:.2f}, more than the ${max(remaining, 0):.2f} left. "
                "Search not run; try a smaller limit or wait for next month's free credit."
            )
        return {**usage, "budget_usd": self.monthly_budget_usd, "remaining_usd": remaining, "run_cap_usd": run_cap}

    def discover(self, category: str | None = None, city: str | None = None, country: str | None = None,
                 limit: int = 25, **_ignored) -> list[DiscoveredBusiness]:
        if not category:
            raise ValueError("Google Maps search needs a category (e.g. 'plumber').")
        if not city:
            raise ValueError("Google Maps search needs a city.")
        places = max(1, min(int(limit or 25), self.max_results))
        budget = self.check_budget(places)

        run_input = {
            "searchStringsArray": [term.strip() for term in category.split(",") if term.strip()],
            "locationQuery": _location_query(city, country),
            "maxCrawledPlacesPerSearch": places,
            "scrapeContacts": True,
            "skipClosedPlaces": True,
            "language": "en",
        }
        client = self._http()
        try:
            response = client.post(
                f"{API_BASE}/acts/{ACTOR_ID}/run-sync-get-dataset-items",
                params={
                    "token": self.token,
                    "timeout": RUN_TIMEOUT_SECONDS,
                    "maxTotalChargeUsd": budget["run_cap_usd"],
                    "maxItems": places,
                },
                json=run_input,
            )
        except httpx.HTTPError as exc:
            raise ValueError(f"Apify run failed ({exc}).") from exc
        finally:
            if self._client is None:
                client.close()
        if response.status_code >= 400:
            raise ValueError(f"Apify run failed (HTTP {response.status_code}): {response.text[:300]}")
        items = response.json()
        if not isinstance(items, list):
            raise ValueError("Apify returned an unexpected response.")
        results = [b for b in (map_place(item, category) for item in items) if b is not None]
        return results[:places]
