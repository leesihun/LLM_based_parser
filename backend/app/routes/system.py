"""System and health endpoints."""

from __future__ import annotations

import platform
import requests
from datetime import datetime

from flask import Blueprint, jsonify

from backend.app.routes.context import RouteContext


def create_blueprint(ctx: RouteContext) -> Blueprint:
    services = ctx.services

    bp = Blueprint("system", __name__)

    @bp.get("/health")
    def healthcheck():
        """Detailed health check for the entire system."""
        llm_client = services.llm_client
        web_search = services.web_search

        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "model": llm_client.model,
            "ollama_url": llm_client.ollama_url,
            "web_search_enabled": False,
            "keyword_extraction_enabled": False,
        }

        # Check Ollama connection
        try:
            response = requests.get(f"{llm_client.ollama_url}/api/tags", timeout=2)
            if response.ok:
                health_data["status"] = "healthy"
            else:
                health_data["status"] = "ollama_unreachable"
                health_data["error"] = "Ollama server responded with error"
        except requests.RequestException as e:
            health_data["status"] = "ollama_unreachable"
            health_data["error"] = str(e)

        # Check web search availability
        try:
            if hasattr(web_search, 'get_search_capabilities'):
                caps = web_search.get_search_capabilities()
                health_data["web_search_enabled"] = caps.get("selenium_available", False)
                health_data["keyword_extraction_enabled"] = caps.get("keyword_extraction_available", False)
        except Exception:
            pass

        return jsonify(health_data)

    @bp.get("/api/system/info")
    @ctx.require_admin
    def system_info():
        memory_stats = services.memory.get_session_stats()
        return jsonify(
            {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "llm": {
                    "model": services.llm_client.model,
                    "endpoint": services.llm_client.ollama_url,
                },
                "memory": memory_stats,
            }
        )

    return bp
