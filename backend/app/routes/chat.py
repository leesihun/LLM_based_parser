"""Chat and conversation routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.app.routes.context import RouteContext
from backend.common.errors import ValidationError


def create_blueprint(ctx: RouteContext) -> Blueprint:
    services = ctx.services
    llm_client = services.llm_client
    memory = services.memory
    rag_system = services.rag_system

    bp = Blueprint("chat", __name__, url_prefix="/api/chat")

    @bp.post("/messages")
    @ctx.require_auth
    def send_message():
        payload = request.get_json(silent=True) or {}
        message = (payload.get("message") or "").strip()
        if not message:
            raise ValidationError("Message is required")

        session_id = payload.get("session_id") or memory.create_session(
            getattr(request, "user", {}).get("user_id")
        )
        use_rag = bool(payload.get("use_rag", False))
        temperature = payload.get("temperature")
        max_tokens = payload.get("max_tokens")

        # Store user message first
        memory.add_message(session_id, "user", message)

        messages = memory.get_context_for_llm(session_id)

        # Inject RAG context when requested
        if use_rag:
            rag_context = rag_system.get_context_for_query(message)
            if rag_context:
                messages.insert(0, {"role": "system", "content": rag_context})

        result = llm_client.chat_completion(messages, temperature=temperature, max_tokens=max_tokens)
        assistant_reply = result.get("content", "")
        memory.add_message(session_id, "assistant", assistant_reply, metadata={"source": "llm"})

        return jsonify(
            {
                "session_id": session_id,
                "message": assistant_reply,
                "raw": result,
                "history": memory.get_conversation_history(session_id, include_system=True),
            }
        )

    @bp.get("/sessions")
    @ctx.require_auth
    def list_sessions():
        user = getattr(request, "user", {})
        sessions = memory.list_sessions(user_id=user.get("user_id"))
        return jsonify({"sessions": sessions})

    @bp.get("/sessions/<session_id>")
    @ctx.require_auth
    def get_session(session_id: str):
        history = memory.get_conversation_history(session_id, include_system=True)
        if not history:
            return jsonify({"session_id": session_id, "history": []}), 404
        return jsonify({"session_id": session_id, "history": history})

    @bp.delete("/sessions/<session_id>")
    @ctx.require_auth
    def delete_session(session_id: str):
        removed = memory.delete_session(session_id)
        return jsonify({"deleted": removed})

    return bp
