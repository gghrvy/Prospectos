from app.services.crawler.fetcher import FetchedPage

DEFAULT_TIMEOUT_MS = 15000
USER_AGENT = "ProspectOSBot/0.1 (+internal audit tool; conservative crawl, respects robots.txt)"


class PlaywrightFetcher:
    """Real page fetcher backed by headless Chromium via Playwright.
    Conservative by design: one page at a time, short timeout, and a single
    failed page is recorded as an error rather than raising and aborting
    the whole crawl. Never attempts to solve CAPTCHAs, bypass logins, or
    evade anti-bot protections (spec section 13)."""

    def __init__(self, timeout_ms: int = DEFAULT_TIMEOUT_MS):
        from playwright.sync_api import sync_playwright  # imported lazily so tests don't need the browser installed

        self._timeout_ms = timeout_ms
        self._playwright = sync_playwright().start()
        # channel="chromium" forces the full Chromium build (new headless
        # mode) instead of the separate "chromium-headless-shell" binary,
        # which some environments fail to download independently.
        self._browser = self._playwright.chromium.launch(headless=True, channel="chromium")
        self._context = self._browser.new_context(user_agent=USER_AGENT)

    def fetch(self, url: str) -> FetchedPage:
        page = self._context.new_page()
        try:
            response = page.goto(url, timeout=self._timeout_ms, wait_until="domcontentloaded")
            html = page.content()
            status = response.status if response else None
            return FetchedPage(url=url, final_url=page.url, status_code=status, html=html)
        except Exception as exc:  # noqa: BLE001 - one bad page must not abort the crawl
            return FetchedPage(url=url, final_url=url, status_code=None, html=None, error=str(exc))
        finally:
            page.close()

    def close(self) -> None:
        self._context.close()
        self._browser.close()
        self._playwright.stop()
