"""Model configuration routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.app.routes.context import RouteContext
from backend.common.errors import ValidationError


def create_blueprint(ctx: RouteContext) -> Blueprint:
    llm_client = ctx.services.llm_client
    config_path = llm_client.config_path

    bp = Blueprint("model_config", __name__, url_prefix="/api/config")

    @bp.get("/model")
    @ctx.require_auth
    def get_model_config():
        return jsonify({"ollama": llm_client.config.get("ollama", {})})

    @bp.post("/model")
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
