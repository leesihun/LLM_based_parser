#!/usr/bin/env python3
"""Entry point for the HE team backend API server."""

from __future__ import annotations

import socket

from backend.app import create_app

app = create_app()


def _local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main() -> None:
    services = app.config["services"]
    config = services.llm_client.config
    host = config.get("server", {}).get("host", "0.0.0.0")
    port = config.get("server", {}).get("port", 8000)

    print("=" * 60)
    print("HE team LLM assistant - Backend API")
    print("=" * 60)
    print(f"Server Host: {host}")
    print(f"Server Port: {port}")
    print(f"Ollama URL: {services.llm_client.ollama_url}")
    print(f"Model: {services.llm_client.model}")
    print()
    print("Access URLs:")
    print(f"  Local:   http://localhost:{port}")
    network_ip = _local_ip()
    if network_ip and network_ip != "127.0.0.1":
        print(f"  Network: http://{network_ip}:{port}")
    print()
    print("Frontend expected at /frontend (run separately).")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
