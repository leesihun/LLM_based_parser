#!/usr/bin/env python3
"""
Self-contained diagnostic for a SearXNG instance.

The script probes the configured base URL (default: http://192.168.219.113:8080),
runs a JSON search request, validates the response shape, and prints a concise
summary. It exits with status code 0 on success and 1 on failure, making it
convenient for CI or quick smoke-tests.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from urllib import error, parse, request

DEFAULT_BASE_URL = "http://192.168.219.113:8080"
DEFAULT_QUERY = "python programming trends 2025"


@dataclass
class ProbeResult:
    ok: bool
    message: str
    status: Optional[int] = None
    elapsed_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


def _make_request(url: str, timeout: int = 10) -> Tuple[int, str, float]:
    """Issue a GET request and return status code, body text, and latency in ms."""
    req = request.Request(
        url,
        headers={
            "User-Agent": "searxng-smoketest/1.0 (+https://github.com/searxng/searxng)",
            "Accept": "application/json, text/html;q=0.2",
        },
        method="GET",
    )
    start = time.perf_counter()
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        elapsed = (time.perf_counter() - start) * 1000
        return resp.status, body, elapsed


def ping_base(base_url: str, timeout: int) -> ProbeResult:
    """Check whether the base URL responds with HTTP 200."""
    url = base_url.rstrip("/") + "/"
    try:
        status, _, elapsed = _make_request(url, timeout=timeout)
        if status == 200:
            return ProbeResult(True, f"Base endpoint reachable ({status})", status, elapsed)
        return ProbeResult(False, f"Unexpected status from base endpoint ({status})", status, elapsed)
    except error.URLError as exc:
        return ProbeResult(False, f"Failed to reach base endpoint: {exc.reason}")
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(False, f"Unexpected error probing base: {exc}")


def run_search(base_url: str, query: str, max_results: int, timeout: int) -> ProbeResult:
    """Execute a JSON search request and validate the shape of the response."""
    endpoint = base_url.rstrip("/") + "/search"
    params = {"q": query, "format": "json", "language": "en", "safesearch": 0}
    url = f"{endpoint}?{parse.urlencode(params)}"

    try:
        status, body, elapsed = _make_request(url, timeout=timeout)
    except error.HTTPError as exc:
        return ProbeResult(False, f"HTTP error from search endpoint: {exc}", exc.code)
    except error.URLError as exc:
        return ProbeResult(False, f"Failed to reach search endpoint: {exc.reason}")
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(False, f"Unexpected error executing search: {exc}")

    if status != 200:
        return ProbeResult(False, f"Search endpoint returned status {status}", status, elapsed)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        snippet = body[:200].replace("\n", " ")
        return ProbeResult(False, f"Invalid JSON from search endpoint: {exc}; body={snippet}", status, elapsed)

    results = payload.get("results", [])
    if not isinstance(results, list):
        return ProbeResult(
            False,
            "Search payload missing 'results' list",
            status,
            elapsed,
            details={"keys": list(payload)[:10]},
        )

    limited = results[:max_results]
    details = {
        "result_count": len(results),
        "sample": [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "engine": r.get("engine"),
            }
            for r in limited
        ],
    }

    if len(limited) == 0:
        return ProbeResult(
            False,
            "Search succeeded but returned zero results",
            status,
            elapsed,
            details=details,
        )

    return ProbeResult(
        True,
        f"Search succeeded with {len(results)} results",
        status,
        elapsed,
        details=details,
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test a SearXNG search endpoint.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL of the SearXNG instance")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Search query to execute")
    parser.add_argument(
        "--timeout",
        type=int,
        default=100,
        help="Timeout (seconds) for HTTP requests",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Number of results to validate in the sample summary",
    )
    return parser


def print_result(label: str, result: ProbeResult) -> None:
    """Format probe results for human-friendly output."""
    status = "OK" if result.ok else "FAIL"
    latency = f"{result.elapsed_ms:.1f} ms" if result.elapsed_ms is not None else "n/a"
    print(f"[{status}] {label}: {result.message} (status={result.status or 'n/a'}, latency={latency})")

    if result.details:
        print("  Details:", json.dumps(result.details, indent=2, ensure_ascii=False))


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    base_url = args.base_url.rstrip("/")

    print("SearXNG Smoke Test")
    print("==================")
    print(f"Base URL : {base_url}")
    print(f"Query    : {args.query}")
    print(f"Timeout  : {args.timeout}s")
    print("")

    probes = [
        ("Base endpoint", ping_base(base_url, timeout=args.timeout)),
        ("Search endpoint", run_search(base_url, args.query, args.max_results, timeout=args.timeout)),
    ]

    success = all(result.ok for _, result in probes)
    for label, result in probes:
        print_result(label, result)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

