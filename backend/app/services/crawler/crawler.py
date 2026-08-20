from dataclasses import dataclass, field
from urllib import robotparser
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.crawler.fetcher import PageFetcher

MAX_PAGES = 10
MAX_DEPTH = 2


@dataclass
class PageResult:
    url: str
    status_code: int | None
    html: str | None
    depth: int


@dataclass
class CrawlResult:
    start_url: str
    pages: list[PageResult] = field(default_factory=list)
    broken_link_count: int = 0
    blocked_by_robots: bool = False

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def crawl_depth(self) -> int:
        return max((p.depth for p in self.pages), default=0)

    @property
    def homepage(self) -> PageResult | None:
        return self.pages[0] if self.pages else None


def _same_domain(base_netloc: str, candidate_url: str) -> bool:
    candidate_netloc = urlparse(candidate_url).netloc
    return candidate_netloc in ("", base_netloc)


def _build_robot_parser(robots_text: str | None) -> robotparser.RobotFileParser:
    rp = robotparser.RobotFileParser()
    rp.parse(robots_text.splitlines() if robots_text else [])
    return rp


def crawl_website(
    start_url: str,
    fetcher: PageFetcher,
    robots_text: str | None = None,
    max_pages: int = MAX_PAGES,
    max_depth: int = MAX_DEPTH,
) -> CrawlResult:
    """Conservative same-domain breadth-first crawl (spec section 13):
    at most `max_pages` pages, at most `max_depth` links deep, honors
    robots.txt Disallow rules, never bypasses CAPTCHA/auth/anti-bot
    measures. A page that fails to fetch counts toward broken_link_count
    but does not stop the crawl."""

    result = CrawlResult(start_url=start_url)
    base_netloc = urlparse(start_url).netloc
    robots = _build_robot_parser(robots_text)

    if not robots.can_fetch("*", start_url):
        result.blocked_by_robots = True
        return result

    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(start_url, 0)]

    while queue and len(result.pages) < max_pages:
        url, depth = queue.pop(0)
        normalized = url.split("#")[0].rstrip("/")
        if normalized in visited:
            continue
        visited.add(normalized)

        if not robots.can_fetch("*", url):
            continue

        fetched = fetcher.fetch(url)

        if fetched.status_code is None or fetched.status_code >= 400:
            result.broken_link_count += 1

        result.pages.append(
            PageResult(url=fetched.final_url or url, status_code=fetched.status_code, html=fetched.html, depth=depth)
        )

        if depth >= max_depth or not fetched.html:
            continue

        soup = BeautifulSoup(fetched.html, "html.parser")
        for link in soup.find_all("a", href=True):
            href = urljoin(fetched.final_url or url, link["href"])
            if not _same_domain(base_netloc, href):
                continue
            normalized_href = href.split("#")[0].rstrip("/")
            if normalized_href in visited:
                continue
            queue.append((href, depth + 1))

    return result
