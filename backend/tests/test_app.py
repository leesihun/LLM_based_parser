"""Minimal smoke tests for the backend application."""

from __future__ import annotations

import pytest

from backend.app import create_app


@pytest.fixture(scope="session")
def app():
    return create_app()


def test_health_endpoint(app):
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"


def test_search_requires_auth(app):
    client = app.test_client()
    response = client.post("/api/search/web", json={"query": "python"})
    assert response.status_code == 401
