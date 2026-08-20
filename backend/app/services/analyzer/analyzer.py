import re
from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.models.enums import QualityCategory
from app.services.crawler.crawler import CrawlResult, PageResult

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(\+?\d[\d\-.\s()]{7,}\d)")

# Domains that show up in crawled HTML from trackers, page builders, and
# boilerplate (not the business's own contact address) -- filtered out so
# "discovered email" never surfaces noise like a Sentry error-reporting
# address or a WordPress theme's example.com placeholder.
_EMAIL_DOMAIN_DENYLIST = (
    "sentry.io", "wixpress.com", "example.com", "example.org", "godaddy.com",
    "w3.org", "schema.org", "wordpress.org", "gstatic.com", "google.com",
    "googleapis.com", "cloudflare.com", "sentry-next.wixpress.com",
)

_LIVE_CHAT_SIGNALS = ["tawk.to", "intercom", "drift.com", "crisp.chat", "zendesk", "livechatinc", "tidio"]
_AI_CHATBOT_SIGNALS = ["chatbase", "voiceflow", "chatbot", "ai assistant", "aichat", "botpress", "landbot"]
_BOOKING_SIGNALS = ["calendly", "book now", "schedule an appointment", "acuityscheduling", "book online", "bookings"]
_FAQ_SIGNALS = ["faq", "frequently asked questions"]
_ANALYTICS_SIGNALS = ["google-analytics.com", "googletagmanager.com", "gtag(", "plausible.io"]
_SOCIAL_DOMAINS = ["facebook.com", "instagram.com", "twitter.com", "x.com", "linkedin.com", "tiktok.com"]


@dataclass
class AnalysisFindings:
    url: str
    http_status: int | None = None
    https_enabled: bool = False
    title: str | None = None
    meta_description: str | None = None
    page_count: int = 0
    crawl_depth: int = 0

    has_viewport: bool = False
    has_contact_form: bool = False
    has_email: bool = False
    has_phone: bool = False
    has_booking: bool = False
    has_faq: bool = False
    has_live_chat: bool = False
    has_ai_chatbot: bool = False
    has_whatsapp: bool = False
    has_social_links: bool = False
    has_analytics: bool = False

    # The actual email address found on the site (mailto: link or plain
    # text), if any -- never guessed, only what's literally on the page.
    discovered_email: str | None = None

    broken_link_count: int = 0

    mobile_score: int = 0
    design_score: int = 0
    technical_score: int = 0
    content_score: int = 0
    conversion_score: int = 0
    customer_experience_score: int = 0
    website_quality_score: int = 0


def _page_has_form(page: PageResult) -> bool:
    if not page.html:
        return False
    return BeautifulSoup(page.html, "html.parser").find("form") is not None


def _looks_like_real_email(email: str) -> bool:
    domain = email.rsplit("@", 1)[-1].lower()
    return not any(domain == d or domain.endswith("." + d) for d in _EMAIL_DOMAIN_DENYLIST)


def _extract_email(pages: list[PageResult]) -> str | None:
    """Best-effort real email extraction: mailto: links first (highest
    confidence), then a plain regex scan of visible text, checking a
    contact/about page before the rest if one was crawled. Only ever
    returns what's literally present on a crawled page -- never guessed
    or fabricated (spec section 11)."""
    ordered = sorted(
        pages,
        key=lambda p: 0 if p.url and any(k in p.url.lower() for k in ("contact", "about")) else 1,
    )

    for page in ordered:
        if not page.html:
            continue
        soup = BeautifulSoup(page.html, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if not href.lower().startswith("mailto:"):
                continue
            candidate = href[len("mailto:"):].split("?")[0].strip()
            match = EMAIL_RE.search(candidate)
            if match and _looks_like_real_email(match.group(0)):
                return match.group(0).lower()

    for page in ordered:
        if not page.html:
            continue
        text = BeautifulSoup(page.html, "html.parser").get_text(" ", strip=True)
        for match in EMAIL_RE.finditer(text):
            if _looks_like_real_email(match.group(0)):
                return match.group(0).lower()

    return None


def analyze_crawl(crawl_result: CrawlResult) -> AnalysisFindings:
    """Turns raw crawled HTML into the scored/flagged fields WebsiteAudit
    needs. Every flag is derived from something actually observed in the
    HTML — never guessed (spec sections 14-15)."""

    findings = AnalysisFindings(url=crawl_result.start_url)
    findings.page_count = crawl_result.page_count
    findings.crawl_depth = crawl_result.crawl_depth
    findings.broken_link_count = crawl_result.broken_link_count
    findings.https_enabled = urlparse(crawl_result.start_url).scheme == "https"

    homepage = crawl_result.homepage
    if homepage is None or not homepage.html:
        findings.http_status = homepage.status_code if homepage else None
        return findings  # unreachable site: every score stays 0 -> CRITICAL

    findings.http_status = homepage.status_code

    combined_html_lower = ""
    combined_text_lower = ""
    for page in crawl_result.pages:
        if not page.html:
            continue
        combined_html_lower += page.html.lower()
        combined_text_lower += " " + BeautifulSoup(page.html, "html.parser").get_text(" ", strip=True).lower()

    home_soup = BeautifulSoup(homepage.html, "html.parser")

    title_tag = home_soup.find("title")
    findings.title = title_tag.get_text(strip=True) if title_tag else None

    meta_desc = home_soup.find("meta", attrs={"name": "description"})
    findings.meta_description = meta_desc.get("content") if meta_desc else None

    findings.has_viewport = home_soup.find("meta", attrs={"name": "viewport"}) is not None
    findings.has_contact_form = any(_page_has_form(p) for p in crawl_result.pages)

    findings.discovered_email = _extract_email(crawl_result.pages)
    findings.has_email = findings.discovered_email is not None or bool(EMAIL_RE.search(combined_text_lower)) or "mailto:" in combined_html_lower
    findings.has_phone = "tel:" in combined_html_lower or bool(PHONE_RE.search(combined_text_lower))

    findings.has_booking = any(sig in combined_html_lower for sig in _BOOKING_SIGNALS)
    findings.has_faq = any(sig in combined_text_lower for sig in _FAQ_SIGNALS)
    findings.has_live_chat = any(sig in combined_html_lower for sig in _LIVE_CHAT_SIGNALS)
    findings.has_ai_chatbot = any(sig in combined_html_lower for sig in _AI_CHATBOT_SIGNALS)
    findings.has_whatsapp = "wa.me/" in combined_html_lower or "api.whatsapp.com" in combined_html_lower
    findings.has_social_links = any(domain in combined_html_lower for domain in _SOCIAL_DOMAINS)
    findings.has_analytics = any(sig in combined_html_lower for sig in _ANALYTICS_SIGNALS)

    findings.mobile_score = _score_mobile(findings)
    findings.technical_score = _score_technical(findings)
    findings.design_score = _score_design(findings, home_soup)
    findings.content_score = _score_content(findings)
    findings.conversion_score = _score_conversion(findings)
    findings.customer_experience_score = _score_customer_experience(findings)

    findings.website_quality_score = round(
        0.20 * findings.mobile_score
        + 0.20 * findings.technical_score
        + 0.20 * findings.design_score
        + 0.15 * findings.content_score
        + 0.15 * findings.conversion_score
        + 0.10 * findings.customer_experience_score
    )

    return findings


def _score_mobile(f: AnalysisFindings) -> int:
    score = 40 if f.has_viewport else 0
    score += 30 if f.https_enabled else 0
    score += max(0, 30 - f.broken_link_count * 10)
    return min(100, score)


def _score_technical(f: AnalysisFindings) -> int:
    score = 40 if f.https_enabled else 0
    score += 30 if (f.http_status is not None and f.http_status < 400) else 0
    score += max(0, 30 - f.broken_link_count * 10)
    return min(100, score)


def _score_design(f: AnalysisFindings, home_soup: BeautifulSoup) -> int:
    score = 25 if f.title else 0
    score += 25 if f.meta_description else 0
    score += 25 if home_soup.find("img") is not None else 0
    score += 25 if f.has_social_links else 0
    return min(100, score)


def _score_content(f: AnalysisFindings) -> int:
    score = 30 if f.title else 0
    score += 30 if f.meta_description else 0
    score += 20 if f.has_faq else 0
    score += 20 if f.page_count > 1 else 0
    return min(100, score)


def _score_conversion(f: AnalysisFindings) -> int:
    score = 30 if f.has_contact_form else 0
    score += 20 if f.has_phone else 0
    score += 20 if f.has_email else 0
    score += 15 if f.has_booking else 0
    score += 15 if f.has_whatsapp else 0
    return min(100, score)


def _score_customer_experience(f: AnalysisFindings) -> int:
    score = 30 if f.has_live_chat else 0
    score += 30 if f.has_ai_chatbot else 0
    score += 20 if f.has_faq else 0
    score += 20 if f.has_booking else 0
    return min(100, score)


# Configurable thresholds (spec section 15): quality category by
# website_quality_score. Kept as a plain function (not a class) so it's
# trivial to override in one place if the business wants different bands.
def quality_category_for_score(score: int) -> str:
    if score >= 90:
        return QualityCategory.EXCELLENT.value
    if score >= 75:
        return QualityCategory.GOOD.value
    if score >= 60:
        return QualityCategory.AVERAGE.value
    if score >= 40:
        return QualityCategory.WEAK.value
    if score >= 20:
        return QualityCategory.POOR.value
    return QualityCategory.CRITICAL.value
