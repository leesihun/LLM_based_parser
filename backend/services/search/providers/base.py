"""Abstract interface for a search provider."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..types import SearchResult


class SearchProvider(ABC):
    """Defines the minimal interface a search provider must implement."""

    name: str

    @abstractmethod
    def search(self, query: str, max_results: int) -> List[SearchResult]:
        """Return a list of normalised search results."""
