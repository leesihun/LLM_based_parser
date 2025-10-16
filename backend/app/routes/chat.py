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
    web_search = services.web_search

    bp = Blueprint("chat", __name__, url_prefix="/api/chat")

    # Legacy endpoint for old frontend - /api/chat
    @bp.post("")
    @ctx.require_auth
    def send_chat_message():
        """Send a normal chat message (old frontend compatibility)."""
        payload = request.get_json(silent=True) or {}
        message = (payload.get("message") or "").strip()
        if not message:
            raise ValidationError("Message is required")

        session_id = payload.get("session_id") or memory.create_session(
            getattr(request, "user", {}).get("user_id")
        )

        memory.add_message(session_id, "user", message)
        messages = memory.get_context_for_llm(session_id)
        result = llm_client.chat_completion(messages)
        assistant_reply = result.get("content", "")
        memory.add_message(session_id, "assistant", assistant_reply)

        return jsonify({
            "session_id": session_id,
            "response": assistant_reply  # Old frontend expects 'response' not 'message'
        })

    # Legacy endpoint for RAG - /api/chat/rag
    @bp.post("/rag")
    @ctx.require_auth
    def send_rag_message():
        """Send a RAG-enabled chat message (old frontend compatibility)."""
        payload = request.get_json(silent=True) or {}
        message = (payload.get("message") or "").strip()
        if not message:
            raise ValidationError("Message is required")

        session_id = payload.get("session_id") or memory.create_session(
            getattr(request, "user", {}).get("user_id")
        )

        memory.add_message(session_id, "user", message)
        messages = memory.get_context_for_llm(session_id)

        # Add RAG context
        rag_context = rag_system.get_context_for_query(message)
        if rag_context:
            messages.insert(0, {"role": "system", "content": rag_context})

        result = llm_client.chat_completion(messages)
        assistant_reply = result.get("content", "")
        memory.add_message(session_id, "assistant", assistant_reply)

        return jsonify({
            "session_id": session_id,
            "response": assistant_reply  # Old frontend expects 'response'
        })

    # Legacy endpoint for web search - /api/chat/web-search
    @bp.post("/web-search")
    @ctx.require_auth
    def send_web_search_message():
        """Send a web search-enabled chat message (old frontend compatibility)."""
        payload = request.get_json(silent=True) or {}
        message = (payload.get("message") or "").strip()
        if not message:
            raise ValidationError("Message is required")

        session_id = payload.get("session_id") or memory.create_session(
            getattr(request, "user", {}).get("user_id")
        )

        memory.add_message(session_id, "user", message)

        # Perform web search
        search_result = web_search.search_and_chat(message, session_id=session_id)

        # Store assistant response
        assistant_reply = search_result.get("response", "")
        memory.add_message(session_id, "assistant", assistant_reply)

        return jsonify({
            "session_id": session_id,
            "response": assistant_reply,
            "keyword_extraction_used": search_result.get("keyword_extraction_used", False),
            "optimized_queries": search_result.get("optimized_queries", []),
            "successful_query": search_result.get("successful_query", ""),
            "search_results": search_result.get("search_results", [])
        })

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
