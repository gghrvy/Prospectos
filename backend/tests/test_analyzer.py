from app.services.analyzer.analyzer import analyze_crawl, quality_category_for_score
from app.services.crawler.crawler import CrawlResult, PageResult

GOOD_HOME_HTML = """
<html><head>
<title>Acme Plumbing - 24/7 Emergency Service</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Trusted local plumbing since 1990.">
<script src="https://www.googletagmanager.com/gtag/js"></script>
<script src="https://embed.tawk.to/widget.js"></script>
</head>
<body>
<img src="/logo.png">
<form><input name="email"><button>Submit</button></form>
<p>Call us at (555) 123-4567 or email info@acmeplumbing.com</p>
<p>Check our FAQ / Frequently Asked Questions below.</p>
<a href="https://calendly.com/acme">Book Now</a>
<a href="https://wa.me/15551234567">WhatsApp us</a>
<a href="https://facebook.com/acmeplumbing">Facebook</a>
<a href="/about">About</a>
</body></html>
"""

GOOD_ABOUT_HTML = "<html><head><title>About</title></head><body><p>We serve Houston.</p></body></html>"

BAD_HOME_HTML = """
<html><head><title>Home</title></head>
<body><p>Welcome to our site.</p></body></html>
"""


def _good_crawl_result() -> CrawlResult:
    result = CrawlResult(start_url="https://acmeplumbing.com")
    result.pages = [
        PageResult(url="https://acmeplumbing.com", status_code=200, html=GOOD_HOME_HTML, depth=0),
        PageResult(url="https://acmeplumbing.com/about", status_code=200, html=GOOD_ABOUT_HTML, depth=1),
    ]
    result.broken_link_count = 0
    return result


def _bad_crawl_result() -> CrawlResult:
    result = CrawlResult(start_url="http://joesplumbing-old.com")
    result.pages = [PageResult(url="http://joesplumbing-old.com", status_code=200, html=BAD_HOME_HTML, depth=0)]
    result.broken_link_count = 2
    return result


def test_good_site_scores_high_quality_and_has_all_flags():
    findings = analyze_crawl(_good_crawl_result())

    assert findings.has_viewport is True
    assert findings.has_contact_form is True
    assert findings.has_phone is True
    assert findings.has_email is True
    assert findings.has_faq is True
    assert findings.has_booking is True
    assert findings.has_whatsapp is True
    assert findings.has_live_chat is True
    assert findings.has_social_links is True
    assert findings.has_analytics is True
    assert findings.discovered_email == "info@acmeplumbing.com"
    assert findings.website_quality_score >= 75
    assert quality_category_for_score(findings.website_quality_score) in ("GOOD", "EXCELLENT")


def test_bad_site_scores_low_quality_and_missing_most_flags():
    findings = analyze_crawl(_bad_crawl_result())

    assert findings.has_viewport is False
    assert findings.has_contact_form is False
    assert findings.has_booking is False
    assert findings.has_ai_chatbot is False
    assert findings.website_quality_score < 40
    assert quality_category_for_score(findings.website_quality_score) in ("WEAK", "POOR", "CRITICAL")


def test_unreachable_site_returns_zeroed_findings():
    result = CrawlResult(start_url="https://down-site.com")
    result.pages = [PageResult(url="https://down-site.com", status_code=None, html=None, depth=0)]

    findings = analyze_crawl(result)

    assert findings.website_quality_score == 0
    assert findings.title is None


def test_discovered_email_prefers_mailto_and_contact_page_over_plain_text():
    home_html = "<html><body><p>Reach us: hello@example.com</p></body></html>"
    contact_html = '<html><body><a href="mailto:owner@realbiz.com?subject=Hi">Email us</a></body></html>'
    result = CrawlResult(start_url="https://realbiz.com")
    result.pages = [
        PageResult(url="https://realbiz.com", status_code=200, html=home_html, depth=0),
        PageResult(url="https://realbiz.com/contact", status_code=200, html=contact_html, depth=1),
    ]

    findings = analyze_crawl(result)

    # mailto: on the contact page wins over plain text on the homepage --
    # example.com is also denylisted boilerplate, so it wouldn't count anyway.
    assert findings.discovered_email == "owner@realbiz.com"


def test_discovered_email_filters_denylisted_boilerplate_domains():
    html = '<html><body><a href="mailto:noreply@sentry.io">error reporting</a></body></html>'
    result = CrawlResult(start_url="https://realbiz.com")
    result.pages = [PageResult(url="https://realbiz.com", status_code=200, html=html, depth=0)]

    findings = analyze_crawl(result)

    assert findings.discovered_email is None


def test_detects_semantic_live_chat_widget_text():
    html = "<html><body><div>Recent Conversations</div><p>We'll respond as soon as we can.</p></body></html>"
    result = CrawlResult(start_url="https://realbiz.com")
    result.pages = [PageResult(url="https://realbiz.com", status_code=200, html=html, depth=0)]

    assert analyze_crawl(result).has_live_chat is True


def test_quality_category_thresholds():
    assert quality_category_for_score(95) == "EXCELLENT"
    assert quality_category_for_score(80) == "GOOD"
    assert quality_category_for_score(65) == "AVERAGE"
    assert quality_category_for_score(45) == "WEAK"
    assert quality_category_for_score(25) == "POOR"
    assert quality_category_for_score(5) == "CRITICAL"


def _crawl(url: str, *pages: tuple[str, str]) -> CrawlResult:
    result = CrawlResult(start_url=url)
    result.pages = [PageResult(url=u, status_code=200, html=h, depth=i) for i, (u, h) in enumerate(pages)]
    return result


def test_email_ranking_prefers_business_domain_and_skips_junk():
    html = """<html><head><style>/* font by impallari@gmail.com */</style></head><body>
    <p>Designed by rwilson@agencymedia.com</p>
    <p>Example: johndoe@email.com</p>
    <img src="logo@2x.png">
    <p>Owner: bob@coolairhvac.com</p>
    <a href="mailto:info@coolairhvac.com">Email us</a>
    </body></html>"""
    findings = analyze_crawl(_crawl("https://www.coolairhvac.com", ("https://www.coolairhvac.com", html)))

    assert findings.discovered_email == "info@coolairhvac.com"
    assert findings.candidate_emails[:2] == ["info@coolairhvac.com", "bob@coolairhvac.com"]
    assert "impallari@gmail.com" not in findings.candidate_emails
    assert "johndoe@email.com" not in findings.candidate_emails
    assert findings.candidate_emails[-1] == "rwilson@agencymedia.com"


def test_free_mail_owner_address_beats_agency_address():
    html = "<p>Site by web@agency.io</p><p>Call or email camshvac1@gmail.com</p>"
    findings = analyze_crawl(_crawl("https://camsac.com", ("https://camsac.com", html)))
    assert findings.discovered_email == "camshvac1@gmail.com"


def test_detects_field_service_booking_and_podium_chat():
    html = '<script src="https://static.servicetitan.com/webscheduler.js"></script><script src="https://connect.podium.com/widget.js"></script>'
    findings = analyze_crawl(_crawl("https://x.com", ("https://x.com", f"<html><body>{html}</body></html>")))
    assert findings.has_booking is True
    assert findings.has_live_chat is True


def test_detects_template_placeholders_and_copyright_year():
    html = "<html><body><p>Your [dr_type] in [city].</p><footer>© Copyright 2021 Dental Company Name.</footer></body></html>"
    findings = analyze_crawl(_crawl("https://westside.com", ("https://westside.com", html)))
    assert "[dr_type]" in findings.template_placeholders
    assert "Dental Company Name" in findings.template_placeholders
    assert findings.copyright_year == 2021


def test_detects_parked_host_page_but_not_normal_homepage():
    parked = "<html><head><title>iPage</title></head><body>Web hosting provided by iPage.com</body></html>"
    assert analyze_crawl(_crawl("http://c2h.com", ("http://c2h.com", parked))).is_parked_or_placeholder is True
    normal = "<html><body><a href='/'>Homepage</a><p>New location coming soon to Tampa!</p>" + "x" * 20000 + "</body></html>"
    assert analyze_crawl(_crawl("https://ok.com", ("https://ok.com", normal))).is_parked_or_placeholder is False
