"""Lightweight web page loader used to enrich search results."""

from __future__ import annotations

import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup


class ContentLoader:
    """Fetches and sanitises remote web pages for downstream processing."""

    def __init__(self, user_agent: str, timeout: int = 15):
        self.logger = logging.getLogger(__name__)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.8",
                "Connection": "keep-alive",
            }
        )

    def fetch(self, url: str) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            self.logger.debug("Content fetch failed for %s: %s", url, exc)
            return None

    def extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer"]):
            tag.decompose()
        text = soup.get_text("\n")
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())

    def load(self, url: str) -> Optional[str]:
        html = self.fetch(url)
        if not html:
            return None
        return self.extract_text(html)
