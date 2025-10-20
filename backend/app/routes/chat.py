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
            "response": assistant_reply
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
                "response": result,
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

    @bp.post("/with-json")
    @ctx.require_auth
    def chat_with_json():
        """Chat with JSON context injection."""
        import json as json_lib

        payload = request.get_json(silent=True) or {}
        message = (payload.get("message") or "").strip()

        if not message:
            raise ValidationError("Message is required")

        # Get JSON data - either inline or from file reference
        json_data = payload.get("json_data")
        file_id = payload.get("file_id")
        json_path = payload.get("json_path")  # Optional: query specific path

        if not json_data and not file_id:
            raise ValidationError("Either json_data or file_id is required")

        # Get session
        session_id = payload.get("session_id") or memory.create_session(
            getattr(request, "user", {}).get("user_id")
        )
        temperature = payload.get("temperature")
        max_tokens = payload.get("max_tokens")

        try:
            # Load JSON data
            if file_id:
                # Load from uploaded file
                user = getattr(request, "user", {})
                user_id = user.get("user_id", "unknown")
                from pathlib import Path

                upload_folder = Path(__file__).resolve().parents[3] / "uploads" / user_id
                file_path = None
                for f in upload_folder.iterdir():
                    if f.stem == file_id and f.suffix.lower() == '.json':
                        file_path = f
                        break

                if not file_path:
                    raise ValidationError(f"JSON file not found: {file_id}")

                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json_lib.load(f)
            else:
                # Use inline JSON data
                if isinstance(json_data, str):
                    json_data = json_lib.loads(json_data)

            # Extract specific path if provided
            if json_path:
                json_data = _extract_json_path(json_data, json_path)

            # Format JSON for context
            json_formatted = json_lib.dumps(json_data, indent=2, ensure_ascii=False)

            # Limit JSON size to avoid token overflow
            max_json_length = 8000000000000000
            if len(json_formatted) > max_json_length:
                json_formatted = json_formatted[:max_json_length] + "\n... (truncated)"

            # Create context message
            context = f"JSON Data Context:\n```json\n{json_formatted}\n```\n\n"

            # Store user message WITH JSON context reference
            user_message_with_context = f"{context}User Query: {message}"
            memory.add_message(session_id, "user", user_message_with_context)

            # Get LLM response with JSON context
            messages = memory.get_context_for_llm(session_id)
            # Insert system instruction at the beginning
            messages.insert(0, {
                "role": "system",
                "content": "You are analyzing data provided in JSON format. Answer the user's questions based on the JSON context they provide. Be specific and cite the relevant parts of the data structure."
            })

            result = llm_client.chat_completion(messages, temperature=temperature, max_tokens=max_tokens)
            assistant_reply = result.get("content", "")

            # Store assistant response
            memory.add_message(session_id, "assistant", assistant_reply, metadata={"source": "json_chat"})

            return jsonify({
                "session_id": session_id,
                "message": assistant_reply,
                "json_data_included": True,
                "json_path": json_path if json_path else "root",
                "json_data": json_data,
                "response": result
            })

        except json_lib.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON data: {str(e)}")
        except Exception as e:
            raise ValidationError(f"Error processing JSON: {str(e)}")

    def _extract_json_path(data, path: str):
        """Extract data from JSON using dot notation path (e.g., 'users.0.name')"""
        parts = path.split('.')
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError):
                    raise ValidationError(f"Invalid array index in path: {part}")
            else:
                raise ValidationError(f"Cannot navigate path '{path}' - not a dict or list")

            if current is None:
                raise ValidationError(f"Path '{path}' not found in JSON data")

        return current

    return bp
