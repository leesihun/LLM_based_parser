"""Model configuration routes."""

from __future__ import annotations

import requests
from flask import Blueprint, jsonify, request

from backend.app.routes.context import RouteContext
from backend.common.errors import ValidationError


def create_blueprint(ctx: RouteContext) -> Blueprint:
    llm_client = ctx.services.llm_client
    config_path = llm_client.config_path

    bp = Blueprint("model_config", __name__)

    # GET /api/config - Get full configuration
    @bp.get("/api/config")
    def get_config():
        """Get current configuration."""
        return jsonify(llm_client.config)

    # POST /api/config - Update configuration (admin only)
    @bp.post("/api/config")
    @ctx.require_admin
    def update_config():
        """Update configuration settings."""
        payload = request.get_json(silent=True) or {}

        # Support updating model directly
        if "model" in payload:
            if "ollama" not in llm_client.config:
                llm_client.config["ollama"] = {}
            llm_client.config["ollama"]["model"] = payload["model"]
            llm_client.save_config(config_path)
            llm_client._initialize_client()
            return jsonify({"success": True, "model": payload["model"]})

        # Support updating ollama config
        if "ollama" in payload:
            llm_client.config["ollama"].update(payload["ollama"])
            llm_client.save_config(config_path)
            llm_client._initialize_client()
            return jsonify({"success": True, "ollama": llm_client.config.get("ollama", {})})

        raise ValidationError("No valid configuration provided")

    # GET /api/models - List available models
    @bp.get("/api/models")
    def list_models():
        """List available Ollama models."""
        try:
            ollama_url = llm_client.ollama_url
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)

            if response.ok:
                data = response.json()
                models = []
                for model in data.get("models", []):
                    models.append({
                        "name": model.get("name"),
                        "size": format_bytes(model.get("size", 0)),
                        "modified_at": model.get("modified_at")
                    })
                return jsonify({"models": models})
            else:
                return jsonify({"models": [], "error": "Failed to fetch models"}), 500
        except Exception as e:
            return jsonify({"models": [], "error": str(e)}), 500

    # Legacy endpoints for backward compatibility
    @bp.get("/api/config/model")
    @ctx.require_auth
    def get_model_config():
        return jsonify({"ollama": llm_client.config.get("ollama", {})})

    @bp.post("/api/config/model")
    @ctx.require_admin
    def update_model_config():
        payload = request.get_json(silent=True) or {}
        ollama_cfg = payload.get("ollama")
        if not isinstance(ollama_cfg, dict):
            raise ValidationError("Missing ollama configuration")

        llm_client.config["ollama"].update(ollama_cfg)
        llm_client.save_config(config_path)
        llm_client._initialize_client()
        return jsonify({"ollama": llm_client.config.get("ollama", {})})

    return bp


def format_bytes(size: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"
