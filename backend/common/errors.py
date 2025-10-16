"""Custom error types and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


class AppError(Exception):
    """Base application error with HTTP metadata."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str, *, status_code: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code

    def to_dict(self) -> Dict[str, Any]:
        return {"error": self.error_code, "message": str(self)}


class AuthenticationError(AppError):
    status_code = 401
    error_code = "authentication_failed"


class AuthorizationError(AppError):
    status_code = 403
    error_code = "forbidden"


class ValidationError(AppError):
    status_code = 400
    error_code = "validation_error"


@dataclass
class ErrorResponse:
    status_code: int
    payload: Dict[str, Any]


def as_error_response(exc: Exception) -> ErrorResponse:
    """Convert any exception into a standard error payload."""
    if isinstance(exc, AppError):
        return ErrorResponse(status_code=exc.status_code, payload=exc.to_dict())
    return ErrorResponse(status_code=500, payload={"error": "internal_error", "message": str(exc)})
