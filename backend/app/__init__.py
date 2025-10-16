"""Flask application factory for the backend."""

from __future__ import annotations

from pathlib import Path

from flask import Flask
from flask_cors import CORS

from backend.app.container import ServiceContainer
from backend.app.errors import register_error_handlers
from backend.app.routes import register_blueprints


DEFAULT_CONFIG = str(Path(__file__).resolve().parents[1] / "config" / "config.json")


def create_app(config_path: str | None = None) -> Flask:
    """Build and configure the Flask application."""
    services = ServiceContainer.build(config_path or DEFAULT_CONFIG)

    app = Flask(
        __name__,
        static_folder=str(Path(__file__).resolve().parents[2] / "frontend" / "static"),
        static_url_path="/",
    )
    CORS(app, supports_credentials=True)
    app.secret_key = "he_team_llm_assistant_secret_key"  # TODO: externalise secret

    # Attach services for easy access inside routes
    app.config["services"] = services

    register_error_handlers(app)
    register_blueprints(app, services)

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.route("/login.html")
    def login_page():
        return app.send_static_file("login.html")

    return app
