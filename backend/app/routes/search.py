"""Web search routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.app.routes.context import RouteContext
from backend.common.errors import ValidationError


def create_blueprint(ctx: RouteContext) -> Blueprint:
    web_search = ctx.services.web_search

    bp = Blueprint("search", __name__, url_prefix="/api/search")

    @bp.post("/web")
    @ctx.require_auth
    def web_search_endpoint():
        payload = request.get_json(silent=True) or {}
        query = (payload.get("query") or "").strip()
        if not query:
            raise ValidationError("Query is required")

        max_results = int(payload.get("max_results", 5))
        result = web_search.search_web(query, max_results=max_results, format_for_llm=False)
        return jsonify(result)

    @bp.post("/extract-keywords")
    @ctx.require_auth
    def extract_keywords():
        payload = request.get_json(silent=True) or {}
        text = (payload.get("text") or "").strip()
        if not text:
            raise ValidationError("Text is required")
        extraction = web_search.keyword_extractor.extract_keywords(text)
        return jsonify({"success": True, **extraction})

    @bp.get("/status")
    @ctx.require_auth
    def search_status():
        capabilities = web_search.get_search_capabilities()
        return jsonify({
            "enabled": web_search.enabled,
            "keyword_extraction_enabled": web_search.use_keyword_extraction,
            "capabilities": capabilities,
        })

    @bp.post("/keyword-extraction/enable")
    @ctx.require_admin
    def enable_keyword_extraction():
        web_search.enable_keyword_extraction()
        return jsonify({"success": True, "enabled": True})

    @bp.post("/keyword-extraction/disable")
    @ctx.require_admin
    def disable_keyword_extraction():
        web_search.disable_keyword_extraction()
        return jsonify({"success": True, "enabled": False})

    return bp
