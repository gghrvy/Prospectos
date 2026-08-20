from app.services.crawler.crawler import crawl_website
from app.services.crawler.fetcher import FetchedPage


class FakeFetcher:
    """In-memory site graph keyed by URL, standing in for a real browser."""

    def __init__(self, pages: dict[str, FetchedPage]):
        self._pages = pages
        self.fetched_urls: list[str] = []

    def fetch(self, url: str) -> FetchedPage:
        self.fetched_urls.append(url)
        return self._pages.get(url, FetchedPage(url=url, final_url=url, status_code=404, html=None))

    def close(self) -> None:
        pass


def _page(url: str, links: list[str], status: int = 200) -> FetchedPage:
    html = "<html><body>" + "".join(f'<a href="{link}">link</a>' for link in links) + "</body></html>"
    return FetchedPage(url=url, final_url=url, status_code=status, html=html)


def test_crawl_follows_same_domain_links_breadth_first():
    site = {
        "https://example.com": _page("https://example.com", ["https://example.com/about", "https://external.com/x"]),
        "https://example.com/about": _page("https://example.com/about", ["https://example.com/contact"]),
        "https://example.com/contact": _page("https://example.com/contact", []),
    }
    fetcher = FakeFetcher(site)

    result = crawl_website("https://example.com", fetcher, max_pages=10, max_depth=2)

    urls_crawled = {p.url for p in result.pages}
    assert urls_crawled == {"https://example.com", "https://example.com/about", "https://example.com/contact"}
    assert "https://external.com/x" not in fetcher.fetched_urls


def test_crawl_respects_max_pages():
    site = {f"https://example.com/p{i}": _page(f"https://example.com/p{i}", [f"https://example.com/p{i+1}"]) for i in range(20)}
    site["https://example.com"] = _page("https://example.com", ["https://example.com/p0"])
    fetcher = FakeFetcher(site)

    result = crawl_website("https://example.com", fetcher, max_pages=5, max_depth=10)

    assert result.page_count == 5


def test_crawl_respects_max_depth():
    site = {
        "https://example.com": _page("https://example.com", ["https://example.com/d1"]),
        "https://example.com/d1": _page("https://example.com/d1", ["https://example.com/d2"]),
        "https://example.com/d2": _page("https://example.com/d2", ["https://example.com/d3"]),
    }
    fetcher = FakeFetcher(site)

    result = crawl_website("https://example.com", fetcher, max_pages=10, max_depth=1)

    urls_crawled = {p.url for p in result.pages}
    assert urls_crawled == {"https://example.com", "https://example.com/d1"}
    assert result.crawl_depth == 1


def test_crawl_respects_robots_disallow():
    fetcher = FakeFetcher({"https://example.com": _page("https://example.com", [])})
    robots_text = "User-agent: *\nDisallow: /"

    result = crawl_website("https://example.com", fetcher, robots_text=robots_text)

    assert result.blocked_by_robots is True
    assert result.page_count == 0
    assert fetcher.fetched_urls == []


def test_crawl_counts_broken_links():
    site = {
        "https://example.com": _page("https://example.com", ["https://example.com/broken"]),
        "https://example.com/broken": FetchedPage(
            url="https://example.com/broken", final_url="https://example.com/broken", status_code=404, html=None
        ),
    }
    fetcher = FakeFetcher(site)

    result = crawl_website("https://example.com", fetcher)

    assert result.broken_link_count == 1
