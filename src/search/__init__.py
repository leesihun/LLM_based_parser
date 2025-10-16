"""
Search package
==============

Provides a modular web-search orchestration layer that mirrors the Page Assist
architecture.  High-level entry point is :class:`SearchManager`, which exposes
provider selection, simple vs. enriched modes, and structured prompt materialisation.
"""

from .manager import SearchManager  # noqa: F401
from .settings import SearchSettings  # noqa: F401
