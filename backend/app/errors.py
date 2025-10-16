"""Flask error handlers."""

from __future__ import annotations

from flask import Flask, jsonify, request

from backend.common.errors import AppError, as_error_response


def register_error_handlers(app: Flask) -> None:
    """Attach global error handlers."""

    @app.errorhandler(AppError)
    def _handle_app_error(exc: AppError):  # type: ignore[override]
        response = as_error_response(exc)
        return jsonify(response.payload), response.status_code

    @app.errorhandler(Exception)
    def _handle_unexpected(exc: Exception):  # type: ignore[override]
        response = as_error_response(exc)
        app.logger.exception("Unhandled exception", exc_info=exc, extra={"path": request.path})
        return jsonify(response.payload), response.status_code
