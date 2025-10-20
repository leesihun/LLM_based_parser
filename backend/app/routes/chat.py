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
        # Force low temperature for factual accuracy (allow override but default to 0.0)
        temperature = payload.get("temperature", 0.0)
        max_tokens = payload.get("max_tokens", 2000)

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

            # Generate numeric summary to ground the model on extrema
            numeric_summary = _generate_numeric_summary(json_data)

            # Format JSON for context
            json_formatted = json_lib.dumps(json_data, indent=2, ensure_ascii=False)

            # Limit JSON size to avoid token overflow
            max_json_length = 50000  # Reasonable limit for most JSON data
            if len(json_formatted) > max_json_length:
                json_formatted = json_formatted[:max_json_length] + "\n... (truncated)"

            # Create context message
            context_parts = []
            if numeric_summary:
                context_parts.append(numeric_summary)
            context_parts.append(f"JSON Data Context:\n```json\n{json_formatted}\n```")
            context = "\n\n".join(context_parts)

            # Store ONLY the user query in memory (not the full JSON to prevent trimming)
            memory.add_message(session_id, "user", f"[Analyzing JSON data] {message}")

            # Create isolated message context (no conversation history for accuracy)
            # This prevents previous conversations from contaminating JSON analysis
            system_prompt = (
                "Answer based solely on the JSON data provided. "
                "Cite JSON paths when referencing information. "
                "For numeric questions, use exact values from the data. "
                "Never guess or hallucinate. "
                "If information is missing from the data, state so explicitly.\n\n"
                "IMPORTANT: Show your step-by-step reasoning:\n"
                "1. Identify the relevant JSON path(s)\n"
                "2. Extract the exact values\n"
                "3. Perform any calculations (if needed)\n"
                "4. State your final answer"
            )

            user_message_with_context = f"{context}\n\n---\n\nQuery: {message}"

            # Use isolated context (no history) for maximum accuracy
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message_with_context}
            ]

            result = llm_client.chat_completion(messages, temperature=temperature, max_tokens=max_tokens)
            assistant_reply = result.get("content", "")

            # Validate response against numeric summary if available
            validation_notes = _validate_response(assistant_reply, numeric_summary, message)

            # Store assistant response
            memory.add_message(session_id, "assistant", assistant_reply, metadata={"source": "json_chat"})

            return jsonify({
                "context": context,
                "numeric_summary": numeric_summary,
                "validation_notes": validation_notes,
                "memory": memory.get_conversation_history(session_id, include_system=True),
                "message": messages,
                "response": assistant_reply,
                "session_id": session_id,
            })

        except json_lib.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON data: {str(e)}")
        except Exception as e:
            raise ValidationError(f"Error processing JSON: {str(e)}")

    def _generate_numeric_summary(data, max_sections: int = 12, max_child_items: int = 25) -> str:
        """Create a lightweight numeric summary (min/max/mean/median/sum) to reduce hallucinations."""
        from collections import deque
        import statistics

        def _is_number(value) -> bool:
            return isinstance(value, (int, float)) and not isinstance(value, bool)

        def _format_number(value):
            if isinstance(value, float):
                return f"{value:.6g}"
            return str(value)

        stats = []
        seen_paths = set()
        queue = deque([(data, "$")])
        visited = 0
        max_iterations = 10000

        def add_stat(path: str, entries):
            if not entries or len(stats) >= max_sections:
                return
            canonical_path = path or "$"
            if canonical_path in seen_paths:
                return
            values = [entry["value"] for entry in entries]
            min_entry = min(entries, key=lambda entry: entry["value"])
            max_entry = max(entries, key=lambda entry: entry["value"])
            sorted_values = sorted(values)

            entry = {
                "path": canonical_path,
                "count": len(values),
                "min": min_entry["value"],
                "max": max_entry["value"],
                "min_path": min_entry.get("path"),
                "max_path": max_entry.get("path"),
                "min_id": min_entry.get("id"),
                "max_id": max_entry.get("id"),
                "sum": sum(values),
                "mean": statistics.mean(values),
                "median": statistics.median(sorted_values) if len(sorted_values) > 1 else sorted_values[0],
            }
            stats.append(entry)
            seen_paths.add(canonical_path)

        while queue and len(stats) < max_sections and visited < max_iterations:
            current, path = queue.popleft()
            visited += 1

            if _is_number(current):
                # Avoid redundant stats for individual list indices when aggregate exists
                if "[]." not in path and "[" in path and path.endswith("]"):
                    continue
                add_stat(path, [{"value": current, "path": path, "id": None}])
                continue

            if isinstance(current, dict):
                for key, value in current.items():
                    child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
                    queue.append((value, child_path))
            elif isinstance(current, list):
                numeric_entries = [
                    {"value": item, "path": f"{path}[{idx}]", "id": None}
                    for idx, item in enumerate(current)
                    if _is_number(item)
                ]
                add_stat(path, numeric_entries)

                if any(isinstance(item, dict) for item in current):
                    keys = []
                    for item in current[:max_child_items]:
                        if isinstance(item, dict):
                            for key in item.keys():
                                if key not in keys:
                                    keys.append(key)
                    identifier_keys = ("id", "ID", "Id", "identifier", "name", "key", "title")
                    for key in keys:
                        numeric_entries = []
                        for idx, item in enumerate(current):
                            if not isinstance(item, dict):
                                continue
                            value = item.get(key)
                            if not _is_number(value):
                                continue
                            identifier = None
                            for identifier_key in identifier_keys:
                                if identifier_key in item and _is_number(item[identifier_key]):
                                    identifier = _format_number(item[identifier_key])
                                    break
                                if identifier_key in item and isinstance(item[identifier_key], str):
                                    identifier = item[identifier_key]
                                    break
                            numeric_entries.append({
                                "value": value,
                                "path": f"{path}[{idx}].{key}",
                                "id": identifier,
                            })
                        child_path = f"{path}[].{key}" if path != "$" else f"$[].{key}"
                        add_stat(child_path, numeric_entries)
                        if len(stats) >= max_sections:
                            break

                for idx, value in enumerate(current[:max_child_items]):
                    queue.append((value, f"{path}[{idx}]"))

        if not stats:
            return ""

        lines = ["Numeric Summary (auto-generated):"]
        for stat in stats[:max_sections]:
            # Build min/max location strings
            min_loc = ""
            if stat.get("min_id") is not None:
                min_loc = f" @id={stat['min_id']}"
            elif stat.get("min_path"):
                # Simplify path display - show only the index/key part
                path_parts = stat['min_path'].split('[')
                if len(path_parts) > 1:
                    min_loc = f" @[{path_parts[-1]}"

            max_loc = ""
            if stat.get("max_id") is not None:
                max_loc = f" @id={stat['max_id']}"
            elif stat.get("max_path"):
                # Simplify path display - show only the index/key part
                path_parts = stat['max_path'].split('[')
                if len(path_parts) > 1:
                    max_loc = f" @[{path_parts[-1]}"

            # Build the summary line
            line = (
                f"- {stat['path']}: "
                f"n={stat['count']}, "
                f"sum={_format_number(stat['sum'])}, "
                f"min={_format_number(stat['min'])}{min_loc}, "
                f"max={_format_number(stat['max'])}{max_loc}, "
                f"mean={_format_number(stat['mean'])}, "
                f"median={_format_number(stat['median'])}"
            )
            lines.append(line)
        return "\n".join(lines)

    def _validate_response(response: str, numeric_summary: str, query: str) -> dict:
        """Validate LLM response against numeric summary for basic sanity checks."""
        import re

        validation = {
            "validated": False,
            "warnings": [],
            "info": []
        }

        if not numeric_summary or not response:
            validation["info"].append("No numeric summary available for validation")
            return validation

        # Extract numbers from the response
        response_numbers = re.findall(r'-?\d+\.?\d*', response)
        response_floats = [float(n) for n in response_numbers if n]

        if not response_floats:
            validation["info"].append("No numeric values found in response")
            return validation

        # Parse numeric summary to extract ranges
        summary_lines = numeric_summary.split('\n')[1:]  # Skip header

        # Check for common numeric query keywords
        query_lower = query.lower()
        is_numeric_query = any(keyword in query_lower for keyword in [
            'sum', 'total', 'max', 'min', 'average', 'mean', 'median',
            'highest', 'lowest', 'count', 'how many', 'number of'
        ])

        if is_numeric_query:
            validation["validated"] = True

            # Extract min/max from summary for validation
            for line in summary_lines:
                if not line.strip():
                    continue

                # Parse line: "- $.path: n=X, sum=Y, min=Z, max=W, ..."
                min_match = re.search(r'min=(-?\d+\.?\d*)', line)
                max_match = re.search(r'max=(-?\d+\.?\d*)', line)
                sum_match = re.search(r'sum=(-?\d+\.?\d*)', line)

                if min_match and max_match:
                    min_val = float(min_match.group(1))
                    max_val = float(max_match.group(1))

                    # Check if response numbers are within data range
                    for num in response_floats:
                        if num < min_val - 0.01 or num > max_val + 0.01:  # Small epsilon for float comparison
                            # Check if it could be a sum or aggregate
                            if sum_match:
                                sum_val = float(sum_match.group(1))
                                if abs(num - sum_val) < 0.01:
                                    continue  # It's a valid sum

                            validation["warnings"].append(
                                f"Value {num} in response appears outside data range [{min_val}, {max_val}]"
                            )

            if not validation["warnings"]:
                validation["info"].append("Response values appear consistent with data ranges")
        else:
            validation["info"].append("Non-numeric query - validation skipped")

        return validation

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
