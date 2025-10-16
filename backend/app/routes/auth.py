"""Authentication routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.app.routes.context import RouteContext
from backend.common.errors import AuthenticationError, ValidationError


def create_blueprint(ctx: RouteContext) -> Blueprint:
    services = ctx.services
    user_manager = services.user_manager

    bp = Blueprint("auth", __name__, url_prefix="/api/auth")

    @bp.post("/login")
    def login():
        payload = request.get_json(silent=True) or {}
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""

        if not username or not password:
            raise ValidationError("Username and password are required")

        user_data = user_manager.authenticate_user(username, password)
        if not user_data:
            raise AuthenticationError("Invalid username or password")

        session_token = user_manager.create_session(user_data)
        return jsonify({"session_token": session_token, "user": user_data, "message": "Login successful"})

    @bp.post("/logout")
    @ctx.require_auth
    def logout():
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            user_manager.logout_session(token)
        return jsonify({"message": "Logout successful"})

    @bp.get("/me")
    @ctx.require_auth
    def current_user():
        user = getattr(request, "user", None)
        return jsonify({"user": user})

    return bp
