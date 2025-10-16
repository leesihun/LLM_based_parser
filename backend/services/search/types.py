"""Common data structures for the search orchestration layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SearchResult:
    """Container describing a single search hit."""

    title: str
    url: str
    snippet: str
    source: Optional[str] = None
    content: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Serialise to a dict compatible with existing response payloads."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "content": self.content,
        }


@dataclass
class SearchExecution:
    """Represents the outcome of executing a search query."""

    query: str
    provider: str
    success: bool
    results: List[SearchResult] = field(default_factory=list)
    prompt: str = ""
    sources: List[Dict[str, str]] = field(default_factory=list)
    answer: Optional[str] = None
    error: Optional[str] = None

    @property
    def result_count(self) -> int:
        return len(self.results)
