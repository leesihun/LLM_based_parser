#!/usr/bin/env python3
"""Backend API server - provides REST API endpoints."""

from __future__ import annotations

import os
import socket

from backend.app import create_app


def _local_ip() -> str:
    """Get the local IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main() -> None:
    """Run the backend API server."""
    # Create Flask app (API only, no static file serving)
    app = create_app()
    services = app.config["services"]
    config = services.llm_client.config

    # Get host and port from environment variables or config
    host = os.environ.get('BACKEND_HOST', config.get("server", {}).get("host", "0.0.0.0"))
    port = int(os.environ.get('BACKEND_PORT', config.get("server", {}).get("port", 8000)))

    print("=" * 60)
    print("HE Team LLM Assistant - Backend API Server")
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
    print("API Endpoints:")
    print(f"  Health:  http://localhost:{port}/health")
    print(f"  Chat:    http://localhost:{port}/api/chat")
    print(f"  RAG:     http://localhost:{port}/api/chat/rag")
    print(f"  Search:  http://localhost:{port}/api/chat/web-search")
    print()
    print("NOTE: Frontend should be run separately!")
    print("      Run 'python run_frontend.py' in another terminal")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)

    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
