from dataclasses import dataclass
from typing import Protocol


@dataclass
class FetchedPage:
    url: str
    final_url: str
    status_code: int | None
    html: str | None
    error: str | None = None


class PageFetcher(Protocol):
    """Anything that can fetch one page's rendered HTML. PlaywrightFetcher
    is the real implementation; tests inject a fake so crawler/analyzer
    logic can be verified without a browser or network access."""

    def fetch(self, url: str) -> FetchedPage: ...

    def close(self) -> None: ...
