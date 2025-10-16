"""Route registration helpers."""

from __future__ import annotations

from flask import Flask

from backend.app.container import ServiceContainer
from backend.app.routes import admin, auth, chat, conversations, files, model_config, rag, search, system
from backend.app.routes.context import RouteContext
from backend.app.routes.decorators import build_auth_decorators

_BLUEPRINT_FACTORIES = (
    admin.create_blueprint,
    auth.create_blueprint,
    chat.create_blueprint,
    conversations.create_blueprint,
    files.create_blueprint,
    model_config.create_blueprint,
    rag.create_blueprint,
    search.create_blueprint,
    system.create_blueprint,
)


def register_blueprints(app: Flask, services: ServiceContainer) -> None:
    """Register all application blueprints."""
    require_auth, require_admin = build_auth_decorators(services.user_manager)
    context = RouteContext(services=services, require_auth=require_auth, require_admin=require_admin)

    for factory in _BLUEPRINT_FACTORIES:
        blueprint = factory(context)
        app.register_blueprint(blueprint)
