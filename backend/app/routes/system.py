"""System and health endpoints."""

from __future__ import annotations

import platform
from datetime import datetime

from flask import Blueprint, jsonify

from backend.app.routes.context import RouteContext


def create_blueprint(ctx: RouteContext) -> Blueprint:
    services = ctx.services

    bp = Blueprint("system", __name__)

    @bp.get("/health")
    def healthcheck():
        return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

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
