"""Diagnostic script to investigate why the web search integration is failing."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Ensure UTF-8 output on Windows terminals.
if isinstance(sys.stdout, TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
else:
    sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding="utf-8")  # type: ignore[attr-defined]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

BASE_DIR = Path(__file__).resolve().parent
TS_DIR = BASE_DIR / "websearch_ts"
CONFIG_CANDIDATES = (
    BASE_DIR / "backend" / "config" / "config.json",
    BASE_DIR / "config" / "config.json",
)


def section(title: str) -> None:
    border = "=" * 80
    print(f"\n{border}\n{title}\n{border}")


def kv(label: str, value: Any) -> None:
    print(f"{label:<28}: {value}")


def load_web_search_config() -> Tuple[Optional[Path], Dict[str, Any]]:
    for path in CONFIG_CANDIDATES:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                section("Configuration Error")
                kv("Config path", path)
                kv("JSON error", exc)
                return path, {}
            if "web_search" in data:
                return path, data["web_search"]
            return path, data
    return None, {}


def check_python_environment() -> None:
    section("Python Environment")
    kv("Python executable", sys.executable)
    kv("Python version", sys.version.replace("\n", " "))
    kv("Working directory", BASE_DIR)
    kv("PATH contains node?", "node" in os.environ.get("PATH", ""))


def run_command(command: list[str], cwd: Optional[Path] = None, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(cwd) if cwd else None,
        shell=False,
    )


def check_node_installation() -> None:
    section("Node.js Runtime")
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    kv("node path", node_path or "NOT FOUND")
    kv("npm path", npm_path or "NOT FOUND")

    if node_path:
        try:
            node_version = run_command(["node", "--version"])
            kv("node --version exit", node_version.returncode)
            kv("node version", node_version.stdout.strip() or node_version.stderr.strip() or "(no output)")
        except Exception as exc:  # pragma: no cover - defensive
            kv("node --version error", exc)
    else:
        print("Node.js is missing from PATH. Install Node >= 18 to enable the TypeScript bridge.")

    if npm_path:
        try:
            npm_version = run_command(["npm", "--version"])
            kv("npm --version exit", npm_version.returncode)
            kv("npm version", npm_version.stdout.strip() or npm_version.stderr.strip() or "(no output)")
        except Exception as exc:  # pragma: no cover - defensive
            kv("npm --version error", exc)
    else:
        print("npm is missing from PATH. Install Node.js which bundles npm.")


def check_typescript_assets() -> None:
    section("TypeScript Bridge Assets")
    kv("Bridge directory", TS_DIR)
    if not TS_DIR.exists():
        print("The websearch_ts directory is missing. The TypeScript bridge cannot run.")
        return

    search_js = TS_DIR / "search.js"
    package_json = TS_DIR / "package.json"
    node_modules = TS_DIR / "node_modules"

    kv("search.js present", search_js.exists())
    kv("package.json present", package_json.exists())
    kv("node_modules present", node_modules.exists())

    if package_json.exists():
        try:
            package_data = json.loads(package_json.read_text(encoding="utf-8"))
            dependencies = package_data.get("dependencies", {})
            kv("dependencies", ", ".join(sorted(dependencies)) or "(none)")
        except json.JSONDecodeError as exc:
            kv("package.json invalid", exc)

    if node_modules.exists():
        try:
            entries = [p.name for p in node_modules.iterdir() if not p.name.startswith(".")]
            kv("installed packages", ", ".join(sorted(entries[:5])) + (" ..." if len(entries) > 5 else ""))
        except Exception as exc:  # pragma: no cover - defensive
            kv("node_modules scan failed", exc)
    else:
        print("Run 'npm install' in websearch_ts to install TypeScript dependencies.")


def show_web_search_settings(config: Dict[str, Any], config_path: Optional[Path]) -> None:
    section("Web Search Configuration")
    if config_path:
        kv("Config loaded from", config_path)
    else:
        print("No config file found. Falling back to SearchManager defaults.")

    if not config:
        print("Web search configuration is empty. Confirm config.json contains the web_search section.")
        return

    kv("enabled", config.get("enabled"))
    kv("default_provider", config.get("default_provider"))
    kv("use_typescript_search", config.get("use_typescript_search"))
    kv("total_results", config.get("total_results"))
    kv("simple_mode", config.get("simple_mode"))
    kv("visit_specific_website", config.get("visit_specific_website"))
    kv("disable_fallbacks", config.get("disable_fallbacks"))

    blank_keys = [key for key in ("bing_api_key", "brave_api_key", "tavily_api_key", "exa_api_key") if not config.get(key)]
    if blank_keys:
        kv("missing API keys", ", ".join(blank_keys))


def run_search_probe(config: Dict[str, Any], query: str, provider_override: Optional[str], max_results: int) -> None:
    section("SearchManager Probe")
    try:
        from backend.services.search.manager import SearchManager
    except ImportError as exc:
        print(f"Failed to import SearchManager: {exc}")
        return

    try:
        manager = SearchManager(config)
    except Exception as exc:
        print(f"SearchManager failed during initialisation: {exc}")
        return

    ts_bridge = getattr(manager, "ts_bridge", None)
    if ts_bridge:

        kv("search.js path", ts_bridge.node_script)
        try:
            # Re-run checks to capture explicit booleans.
            node_ok = ts_bridge._check_node()  # type: ignore[attr-defined]
            deps_ok = ts_bridge._check_dependencies()  # type: ignore[attr-defined]
            kv("node available", node_ok)
            kv("dependencies installed", deps_ok)
        except Exception as exc:  # pragma: no cover - defensive
            kv("bridge self-check failed", exc)

    print("\nTriggering a live search via the TypeScript bridge...")
    if provider_override:
        kv("provider override", provider_override)
    kv("requested results", max_results)
    kv("query", query)
    try:
        execution = manager.search(query, max_results=max_results, provider_override=provider_override)
    except Exception as exc:
        print(f"SearchManager.search raised an exception: {exc}")
        return

    kv("provider", execution.provider)
    kv("success", execution.success)
    kv("result count", len(execution.results))
    kv("error", execution.error or "(no error)")

    if execution.results:
        print("\nTop results:")
        for idx, item in enumerate(execution.results, start=1):
            kv(f"Result {idx} title", getattr(item, "title", "(no title)"))
            kv(f"Result {idx} url", getattr(item, "url", "(no url)"))
            snippet = (getattr(item, "snippet", "") or "")[:140].replace("\n", " ").strip()
            kv(f"Result {idx} snippet", snippet or "(empty)")
    else:
        print("\nNo results returned. Inspect the error message above and review server logs.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Web search diagnostic helper")
    parser.add_argument(
        "--query",
        default="diagnostic web search probe",
        help="Query to send through the TypeScript bridge",
    )
    parser.add_argument(
        "--provider",
        help="Force a specific provider (e.g. google, brave_api, tavily_api)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=3,
        help="Maximum results to request from the provider",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("Web Search Diagnostic Utility")
    print("=" * 80)

    check_python_environment()
    check_node_installation()
    check_typescript_assets()
    config_path, web_search_config = load_web_search_config()
    show_web_search_settings(web_search_config, config_path)
    run_search_probe(web_search_config, args.query, args.provider, args.max_results)

    print("\nDiagnostics complete. Review the sections above to identify missing prerequisites.")


if __name__ == "__main__":
    main()
