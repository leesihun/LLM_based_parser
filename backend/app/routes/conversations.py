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
        """Get conversation details (metadata only)."""
        session = memory.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({
            "conversation": {
                "id": session["id"],
                "user_id": session.get("user_id"),
                "created_at": session["created_at"],
                "last_activity": session["last_activity"],
                "title": session["metadata"]["title"],
                "total_messages": session["metadata"]["total_messages"]
            }
        })

    @bp.get("/<session_id>/history")
    @ctx.require_auth
    def fetch_conversation_history(session_id: str):
        """Get conversation history (messages)."""
        # Get query parameter for include_system (default: false)
        include_system = request.args.get("include_system", "false").lower() == "true"
        
        history = memory.get_conversation_history(session_id, include_system=include_system)
        if history is None or (not history and session_id not in memory.sessions):
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({
            "session_id": session_id,
            "history": history
        })

    @bp.delete("/<session_id>")
    @ctx.require_auth
    def remove_conversation(session_id: str):
        deleted = memory.delete_session(session_id)
        return jsonify({"deleted": deleted})

    return bp
