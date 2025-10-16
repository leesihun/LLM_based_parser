"""Settings helpers for the web search subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class ProviderToggle:
    enabled: bool = True


@dataclass
class SearxngSettings:
    url: str = ""
    json_mode: bool = False


@dataclass
class BingSettings:
    api_key: str = ""


@dataclass
class SearchSettings:
    """Normalised search configuration loaded from config.json."""

    enabled: bool = True
    default_provider: str = "searxng"
    total_results: int = 5
    simple_mode: bool = False
    visit_specific_website: bool = True
    request_timeout: int = 15
    user_agent: str = DEFAULT_USER_AGENT
    auto_restart_searxng: bool = False
    restart_on_failure: bool = False
    searxng: SearxngSettings = field(default_factory=SearxngSettings)
    bing: BingSettings = field(default_factory=BingSettings)
    provider_toggles: Dict[str, ProviderToggle] = field(default_factory=dict)
    result_filtering: Dict = field(default_factory=dict)
    cache_ttl: Optional[int] = None


    @classmethod
    def from_config(cls, config: Optional[Dict]) -> "SearchSettings":
        config = config or {}
        providers_cfg = config.get("providers", {})

        toggles: Dict[str, ProviderToggle] = {}
        for name in (
            "searxng",
            "duckduckgo",
            "brave",
            "bing",
            "startpage",
            "exa",
            "firecrawl",
            "ollama-search",
            "tavily-api",
        ):
            toggle_cfg = providers_cfg.get(name, {})
            toggles[name] = ProviderToggle(enabled=toggle_cfg.get("enabled", True))

        search_method = config.get("default_provider") or config.get(
            "search_provider"
        ) or config.get("search_method", "searxng")

        total_results = config.get("total_results") or config.get("max_results", 5)

        searxng_settings = SearxngSettings(
            url=config.get("searxng_url", ""),
            json_mode=config.get("searxng_json_mode", False),
        )

        bing_settings = BingSettings(
            api_key=config.get("bing_api_key", ""),
        )

        result_filtering_settings = config.get("result_filtering", {})
        cache_ttl = config.get("cache_ttl")

        return cls(
            enabled=config.get("enabled", True),
            default_provider=search_method,
            total_results=total_results,
            simple_mode=config.get("simple_mode", False),
            visit_specific_website=config.get("visit_specific_website", True),
            request_timeout=config.get("timeout", 15),
            user_agent=config.get("user_agent", DEFAULT_USER_AGENT),
            auto_restart_searxng=config.get("auto_restart_searxng", False),
            restart_on_failure=config.get("restart_on_search_failure", False),
            searxng=searxng_settings,
            bing=bing_settings,
            provider_toggles=toggles,
            result_filtering=result_filtering_settings,
            cache_ttl=cache_ttl,
        )
