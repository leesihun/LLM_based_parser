"""RAG (Retrieval Augmented Generation) routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.app.routes.context import RouteContext
from backend.common.errors import ValidationError


def create_blueprint(ctx: RouteContext) -> Blueprint:
    services = ctx.services
    rag_system = services.rag_system

    bp = Blueprint("rag", __name__, url_prefix="/api/rag")

    @bp.get("/stats")
    @ctx.require_auth
    def get_rag_stats():
        """Get RAG system statistics."""
        try:
            # Check if it's the NullRAGSystem
            if hasattr(rag_system, 'get_stats'):
                stats = rag_system.get_stats()
            else:
                # Fallback for NullRAGSystem
                stats = {
                    "document_count": 0,
                    "total_chunks": 0,
                    "status": "unavailable"
                }

            return jsonify({
                "stats": stats,
                "available": hasattr(rag_system, 'search')
            })
        except Exception as e:
            return jsonify({
                "stats": {
                    "document_count": 0,
                    "total_chunks": 0,
                    "status": "error",
                    "error": str(e)
                },
                "available": False
            })

    @bp.post("/search")
    @ctx.require_auth
    def search_rag():
        """Search the RAG knowledge base."""
        payload = request.get_json(silent=True) or {}
        query = payload.get("query", "")
        n_results = payload.get("n_results", 5)

        if not query:
            raise ValidationError("Query is required")

        try:
            results = rag_system.search(query, n_results=n_results)
            return jsonify({
                "results": results,
                "query": query
            })
        except Exception as e:
            raise ValidationError(f"RAG search failed: {str(e)}")

    @bp.get("/context")
    @ctx.require_auth
    def get_context():
        """Get context for a query from RAG system."""
        query = request.args.get("query", "")
        max_length = request.args.get("max_length", type=int)

        if not query:
            raise ValidationError("Query parameter is required")

        try:
            context = rag_system.get_context_for_query(query, max_context_length=max_length)
            return jsonify({
                "context": context,
                "query": query
            })
        except Exception as e:
            raise ValidationError(f"Failed to get context: {str(e)}")

    return bp
