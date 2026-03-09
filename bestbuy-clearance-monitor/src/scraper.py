"""HTTP scraping utilities."""

from __future__ import annotations

import logging
import time
from typing import Iterable, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Scraper:
    """Requests-based scraper with retry and backoff."""

    def __init__(
        self,
        timeout_sec: int,
        max_retries: int,
        backoff_factor: float,
        user_agent: str,
    ) -> None:
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept-Language": "en-CA,en;q=0.9",
            }
        )

    def get(self, url: str) -> str:
        """GET URL with retry logic and exponential backoff."""
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout_sec)
                response.raise_for_status()
                return response.text
            except requests.RequestException as exc:
                last_error = exc
                wait = self.backoff_factor ** (attempt - 1)
                logger.warning(
                    "Request failed (attempt %s/%s): %s %s",
                    attempt,
                    self.max_retries,
                    url,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(wait)
        raise RuntimeError(f"Failed to fetch {url} after retries") from last_error

    def collect_product_links(self, category_url: str) -> list[str]:
        """Collect and deduplicate product URLs from category page HTML."""
        html = self.get(category_url)
        soup = BeautifulSoup(html, "html.parser")
        links: list[str] = []
        seen: set[str] = set()

        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "")
            if "/en-ca/product/" not in href:
                continue
            absolute = urljoin("https://www.bestbuy.ca", href.split("?")[0])
            if absolute not in seen:
                seen.add(absolute)
                links.append(absolute)

        logger.info("Collected %s unique product links", len(links))
        return links

    def fetch_product_pages(self, urls: Iterable[str]) -> dict[str, str]:
        """Download product pages indexed by URL."""
        pages: dict[str, str] = {}
        for idx, url in enumerate(urls, start=1):
            logger.info("Fetching product %s: %s", idx, url)
            try:
                pages[url] = self.get(url)
            except Exception:
                logger.exception("Failed to fetch product URL: %s", url)
        return pages
