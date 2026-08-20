from urllib.parse import urlparse

import httpx

from app.models.business import Business
from app.services.analyzer.analyzer import analyze_crawl, quality_category_for_score
from app.services.crawler.crawler import crawl_website
from app.services.crawler.fetcher import PageFetcher
from app.services.crawler.playwright_fetcher import PlaywrightFetcher
from app.services.crawler.screenshot import capture_screenshots
from app.services.scoring.scoring import score_no_website, score_website

ROBOTS_TIMEOUT_SECONDS = 10.0


def _fetch_robots_txt(website_url: str) -> str | None:
    parsed = urlparse(website_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = httpx.get(
            robots_url, timeout=ROBOTS_TIMEOUT_SECONDS, headers={"User-Agent": "ProspectOSBot/0.1"}
        )
        if response.status_code == 200:
            return response.text
    except httpx.HTTPError:
        pass
    return None


def run_audit(business: Business, fetcher: PageFetcher | None = None) -> dict:
    """Orchestrates crawl -> analyze -> score for one business and returns
    a dict of WebsiteAudit field values (never mutates/overwrites a prior
    audit — the caller inserts this as a new row, per spec section 36).

    `fetcher` can be injected (tests pass a fake); when omitted a real
    PlaywrightFetcher is created and closed here."""

    if not business.website:
        result = score_no_website()
        return {
            "url": None,
            "quality_category": result.quality_category,
            "opportunity_types": result.opportunity_types,
            "opportunity_reasons": result.opportunity_reasons,
            "ai_opportunity_score": result.ai_opportunity_score,
            "redesign_opportunity_score": result.redesign_opportunity_score,
            "overall_opportunity_score": result.overall_opportunity_score,
            "audit_summary": "No website found — the strongest possible opportunity: a first website from scratch.",
        }

    owns_fetcher = fetcher is None
    fetcher = fetcher or PlaywrightFetcher()
    try:
        robots_text = _fetch_robots_txt(business.website)
        crawl_result = crawl_website(business.website, fetcher, robots_text=robots_text)
    finally:
        if owns_fetcher:
            fetcher.close()

    desktop_screenshot, mobile_screenshot = (
        capture_screenshots(business.website, business.id) if owns_fetcher else (None, None)
    )

    findings = analyze_crawl(crawl_result)
    quality_category = quality_category_for_score(findings.website_quality_score)
    scoring_result = score_website(findings, quality_category)

    summary = (
        f"{quality_category} website scoring {findings.website_quality_score}/100 overall, "
        f"with {len(scoring_result.opportunity_types)} opportunity area(s) identified."
        if crawl_result.homepage and crawl_result.homepage.html
        else "Website could not be reached during the crawl."
    )

    return {
        "url": business.website,
        "http_status": findings.http_status,
        "https_enabled": findings.https_enabled,
        "title": findings.title,
        "meta_description": findings.meta_description,
        "page_count": findings.page_count,
        "crawl_depth": findings.crawl_depth,
        "has_viewport": findings.has_viewport,
        "has_contact_form": findings.has_contact_form,
        "has_email": findings.has_email,
        "has_phone": findings.has_phone,
        "has_booking": findings.has_booking,
        "has_faq": findings.has_faq,
        "has_live_chat": findings.has_live_chat,
        "has_ai_chatbot": findings.has_ai_chatbot,
        "has_whatsapp": findings.has_whatsapp,
        "has_social_links": findings.has_social_links,
        "discovered_email": findings.discovered_email,
        "broken_link_count": findings.broken_link_count,
        "mobile_score": findings.mobile_score,
        "design_score": findings.design_score,
        "technical_score": findings.technical_score,
        "content_score": findings.content_score,
        "conversion_score": findings.conversion_score,
        "customer_experience_score": findings.customer_experience_score,
        "website_quality_score": findings.website_quality_score,
        "quality_category": quality_category,
        "ai_opportunity_score": scoring_result.ai_opportunity_score,
        "redesign_opportunity_score": scoring_result.redesign_opportunity_score,
        "overall_opportunity_score": scoring_result.overall_opportunity_score,
        "opportunity_types": scoring_result.opportunity_types,
        "opportunity_reasons": scoring_result.opportunity_reasons,
        "audit_summary": summary,
        "screenshot_desktop_path": desktop_screenshot,
        "screenshot_mobile_path": mobile_screenshot,
    }
