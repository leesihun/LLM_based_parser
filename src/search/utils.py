"""Utility helpers shared across the search modules."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse


URL_PATTERN = re.compile(
    r"(?P<url>(?:https?://|www\.)[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
    re.IGNORECASE,
)


def escape_for_prompt(value: str) -> str:
    """Escape text for inclusion inside the structured <result> prompt."""
    return html.escape(value, quote=False)


def hostname_from_url(url: str) -> str:
    """Extract the hostname component from a URL-safe string."""
    try:
        parsed = urlparse(url if re.match(r"^https?://", url) else f"https://{url}")
        return parsed.hostname or url
    except Exception:
        return url


@dataclass
class WebsiteDetection:
    urls: List[str]
    cleaned_query: str


def detect_urls_in_query(query: str) -> WebsiteDetection:
    """Identify URLs or bare domains inside a query and return cleaned text."""
    matches = list(URL_PATTERN.finditer(query))
    if not matches:
        return WebsiteDetection(urls=[], cleaned_query=query)

    urls = []
    cleaned = query
    for match in matches:
        raw = match.group("url")
        urls.append(_normalise_url(raw))
        cleaned = cleaned.replace(raw, "").strip()

    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return WebsiteDetection(urls=urls, cleaned_query=cleaned or query)


def _normalise_url(url: str) -> str:
    if not url:
        return url
    if re.match(r"^https?://", url, re.IGNORECASE):
        return url
    if url.startswith("www."):
        return f"https://{url}"
    return f"https://{url}"


def choose_relevant_snippet(text: str, query: str, limit: int = 800) -> str:
    """Pick a paragraph that best matches the query using a simple token overlap score."""
    paragraphs = [
        segment.strip()
        for segment in re.split(r"\n{2,}", text)
        if len(segment.strip()) > 40
    ]

    if not paragraphs:
        paragraphs = [text]

    query_terms = {
        token.lower()
        for token in re.findall(r"[a-zA-Z0-9]+", query)
        if len(token) > 2
    }

    def score(paragraph: str) -> int:
        tokens = {
            token.lower() for token in re.findall(r"[a-zA-Z0-9]+", paragraph)
        }
        return sum(1 for token in query_terms if token in tokens)

    best_paragraph = max(paragraphs, key=score)
    return best_paragraph[:limit]
