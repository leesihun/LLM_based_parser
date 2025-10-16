"""Conversation history routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.app.routes.context import RouteContext


def create_blueprint(ctx: RouteContext) -> Blueprint:
    memory = ctx.services.memory

    bp = Blueprint("conversations", __name__, url_prefix="/api/conversations")

    @bp.get("/")
    @ctx.require_auth
    def list_conversations():
        user = getattr(request, "user", {})
        sessions = memory.list_sessions(user_id=user.get("user_id"))
        return jsonify({"sessions": sessions})

    @bp.get("/<session_id>")
    @ctx.require_auth
    def fetch_conversation(session_id: str):
        history = memory.get_conversation_history(session_id, include_system=True)
        return jsonify({"session_id": session_id, "history": history})

    @bp.delete("/<session_id>")
    @ctx.require_auth
    def remove_conversation(session_id: str):
        deleted = memory.delete_session(session_id)
        return jsonify({"deleted": deleted})

    return bp
