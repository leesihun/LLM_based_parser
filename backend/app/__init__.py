"""Flask application factory for the backend."""

from __future__ import annotations

from pathlib import Path

from flask import Flask
from flask_cors import CORS

from backend.app.container import ServiceContainer
from backend.app.errors import register_error_handlers
from backend.app.routes import register_blueprints


DEFAULT_CONFIG = str(Path(__file__).resolve().parents[2] / "config.json")


def create_app(config_path: str | None = None) -> Flask:
    """Build and configure the Flask application (API only, no frontend)."""
    services = ServiceContainer.build(config_path or DEFAULT_CONFIG)

    app = Flask(__name__)

    # Configure CORS to allow requests from frontend
    # In production, replace '*' with specific frontend URL
    CORS(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    app.secret_key = "he_team_llm_assistant_secret_key"  # TODO: externalise secret

    # Attach services for easy access inside routes
    app.config["services"] = services

    register_error_handlers(app)
    register_blueprints(app, services)

    # Simple root endpoint for API status
    @app.route("/")
    def index():
        return {
            "status": "running",
            "message": "HE Team LLM Assistant - Backend API",
            "version": "2.1.1",
            "endpoints": {
                "health": "/health",
                "chat": "/api/chat",
                "rag": "/api/chat/rag",
                "web_search": "/api/chat/web-search",
                "files": "/api/files",
                "auth": "/api/auth"
            }
        }

    return app
