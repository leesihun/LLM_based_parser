#!/usr/bin/env python3
"""Frontend server - serves static HTML/CSS/JS files."""

from __future__ import annotations

import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler


class FrontendHandler(SimpleHTTPRequestHandler):
    """Custom handler for serving frontend static files."""

    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        frontend_dir = Path(__file__).parent / "frontend" / "static"
        super().__init__(*args, directory=str(frontend_dir), **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_GET(self):
        # Serve index.html for root path
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()


def main() -> None:
    """Run the frontend server."""
    host = os.environ.get('FRONTEND_HOST', '0.0.0.0')
    port = int(os.environ.get('FRONTEND_PORT', '3000'))

    print("=" * 60)
    print("HE Team LLM Assistant - Frontend Server")
    print("=" * 60)
    print(f"Server Host: {host}")
    print(f"Server Port: {port}")
    print()
    print("Access URLs:")
    print(f"  Local:   http://localhost:{port}")
    print()
    print("NOTE: Make sure the backend API server is running!")
    print("      Run 'python run_backend.py' in another terminal")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)

    server = HTTPServer((host, port), FrontendHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down frontend server...")
        server.shutdown()


if __name__ == "__main__":
    main()
