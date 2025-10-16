"""Authentication decorators for route modules."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from flask import jsonify, request

from backend.common.errors import AuthenticationError, AuthorizationError
from backend.core.user_management import UserManager

F = TypeVar("F", bound=Callable[..., Any])


def build_auth_decorators(user_manager: UserManager):
    """Create authentication decorators bound to the provided user manager."""

    def require_auth(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise AuthenticationError("Authentication required")

            token = auth_header.split(" ", 1)[1]
            session_data = user_manager.validate_session(token)
            if not session_data:
                raise AuthenticationError("Invalid or expired session")

            request.user = session_data  # type: ignore[attr-defined]
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    def require_admin(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = getattr(request, "user", None)
            if not user or user.get("role") != "admin":
                raise AuthorizationError("Admin privileges required")
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return require_auth, require_admin
