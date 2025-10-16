"""Route context objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from backend.app.container import ServiceContainer


@dataclass(slots=True)
class RouteContext:
    services: ServiceContainer
    require_auth: Callable
    require_admin: Callable
