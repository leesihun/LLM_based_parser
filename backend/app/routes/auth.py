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

    @bp.post("/change-password")
    @ctx.require_auth
    def change_password():
        """Change user password."""
        payload = request.get_json(silent=True) or {}
        old_password = payload.get("old_password", "")
        new_password = payload.get("new_password", "")

        if not old_password or not new_password:
            raise ValidationError("Old password and new password are required")

        # Get current user
        user = getattr(request, "user", None)
        if not user:
            raise AuthenticationError("User not authenticated")

        username = user.get("username")

        # Verify old password
        user_data = user_manager.authenticate_user(username, old_password)
        if not user_data:
            raise AuthenticationError("Current password is incorrect")

        # Update password
        success = user_manager.change_password(username, old_password, new_password)
        if not success:
            raise ValidationError("Failed to change password")

        return jsonify({"success": True, "message": "Password changed successfully"})

    return bp
