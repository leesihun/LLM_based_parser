"""Admin routes for user management."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.app.routes.context import RouteContext
from backend.common.errors import ValidationError


def create_blueprint(ctx: RouteContext) -> Blueprint:
    user_manager = ctx.services.user_manager

    bp = Blueprint("admin", __name__, url_prefix="/api/admin")

    @bp.get("/users")
    @ctx.require_admin
    def list_users():
        """List all users (admin only)."""
        users = []
        for username, user_data in user_manager.users.items():
            users.append({
                "username": user_data.get("username"),
                "user_id": user_data.get("user_id"),
                "email": user_data.get("email"),
                "role": user_data.get("role"),
                "display_name": user_data.get("display_name"),
                "is_active": user_data.get("is_active", True),
                "created_at": user_data.get("created_at"),
                "last_login": user_data.get("last_login")
            })
        return jsonify({"users": users})

    @bp.post("/users")
    @ctx.require_admin
    def create_user():
        """Create a new user (admin only)."""
        payload = request.get_json(silent=True) or {}

        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""
        email = (payload.get("email") or "").strip()
        role = payload.get("role", "user")
        display_name = payload.get("display_name") or username

        if not username or not password:
            raise ValidationError("Username and password are required")

        if not email:
            raise ValidationError("Email is required")

        # Create the user
        success = user_manager.create_user(
            username=username,
            password=password,
            email=email,
            role=role,
            display_name=display_name
        )

        if not success:
            raise ValidationError("User already exists or creation failed")

        return jsonify({
            "success": True,
            "message": f"User '{username}' created successfully",
            "user": {
                "username": username,
                "email": email,
                "role": role,
                "display_name": display_name
            }
        }), 201

    @bp.delete("/users/<username>")
    @ctx.require_admin
    def delete_user(username: str):
        """Delete a user (admin only)."""
        if username == "admin":
            raise ValidationError("Cannot delete admin user")

        if username not in user_manager.users:
            raise ValidationError(f"User '{username}' not found")

        success = user_manager.delete_user(username)

        if success:
            return jsonify({
                "success": True,
                "message": f"User '{username}' deleted successfully"
            })
        else:
            raise ValidationError("Failed to delete user")

    @bp.put("/users/<username>")
    @ctx.require_admin
    def update_user(username: str):
        """Update user details (admin only)."""
        if username not in user_manager.users:
            raise ValidationError(f"User '{username}' not found")

        payload = request.get_json(silent=True) or {}

        user_data = user_manager.users[username]

        # Update allowed fields
        if "email" in payload:
            user_data["email"] = payload["email"]
        if "role" in payload:
            user_data["role"] = payload["role"]
        if "display_name" in payload:
            user_data["display_name"] = payload["display_name"]
        if "is_active" in payload:
            user_data["is_active"] = payload["is_active"]

        # Save changes
        user_manager._save_users()

        return jsonify({
            "success": True,
            "message": f"User '{username}' updated successfully",
            "user": {
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "role": user_data.get("role"),
                "display_name": user_data.get("display_name"),
                "is_active": user_data.get("is_active", True)
            }
        })

    @bp.post("/users/<username>/reset-password")
    @ctx.require_admin
    def reset_user_password(username: str):
        """Reset user password (admin only)."""
        if username not in user_manager.users:
            raise ValidationError(f"User '{username}' not found")

        payload = request.get_json(silent=True) or {}
        new_password = payload.get("new_password") or ""

        if not new_password:
            raise ValidationError("New password is required")

        # Update password
        user_data = user_manager.users[username]
        salt = user_manager._generate_salt()
        password_hash = user_manager._hash_password(new_password, salt)

        user_data["password_hash"] = password_hash
        user_data["salt"] = salt

        user_manager._save_users()

        return jsonify({
            "success": True,
            "message": f"Password for user '{username}' reset successfully"
        })

    return bp
