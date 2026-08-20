import os

SCREENSHOT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "screenshots")
)

DESKTOP_VIEWPORT = {"width": 1440, "height": 900}
MOBILE_VIEWPORT = {"width": 390, "height": 844}
SCREENSHOT_TIMEOUT_MS = 15000


def capture_screenshots(url: str, business_id: str) -> tuple[str | None, str | None]:
    """Captures a desktop and mobile screenshot of `url`'s homepage using a
    short-lived headless Chromium session. Never raises — a capture failure
    just means both paths come back None, which is fine since the audit
    isn't blocked on screenshots (spec section 16)."""
    from playwright.sync_api import sync_playwright  # imported lazily so tests don't need the browser installed

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    desktop_path = os.path.join(SCREENSHOT_DIR, f"{business_id}_desktop.png")
    mobile_path = os.path.join(SCREENSHOT_DIR, f"{business_id}_mobile.png")

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, channel="chromium")
            try:
                desktop_page = browser.new_page(viewport=DESKTOP_VIEWPORT)
                desktop_page.goto(url, timeout=SCREENSHOT_TIMEOUT_MS, wait_until="domcontentloaded")
                desktop_page.screenshot(path=desktop_path)
                desktop_page.close()

                mobile_page = browser.new_page(viewport=MOBILE_VIEWPORT, is_mobile=True)
                mobile_page.goto(url, timeout=SCREENSHOT_TIMEOUT_MS, wait_until="domcontentloaded")
                mobile_page.screenshot(path=mobile_path)
                mobile_page.close()
            finally:
                browser.close()
        return desktop_path, mobile_path
    except Exception:  # noqa: BLE001 - screenshots are best-effort, never fail the audit
        return None, None
