from http import HTTPStatus
from typing import Any

import pytest
from litestar.testing import TestClient

from onboarding_flow.app import app, create_app
from onboarding_flow.config import reset_settings_cache
from onboarding_flow.memory_upstream import MemoryUpstream

UPSTREAM_TIMEOUT_SECONDS = 2.5


def test_health_endpoint() -> None:
    with TestClient(app=app) as client:
        response = client.get("/health")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


def test_lifecycle_logs_startup_and_shutdown_with_injected_upstream(
    success_memory_upstream: MemoryUpstream,
    json_logs: list[dict[str, Any]],
) -> None:
    with TestClient(app=create_app(upstream=success_memory_upstream)):
        pass

    [started] = [line for line in json_logs if line["message"] == "app_started"]
    assert started["upstream_adapter"] == "MemoryUpstream"
    assert started["version"] == "0.1.0"
    assert [line["message"] for line in json_logs][-1] == "app_stopping"


def test_startup_logs_upstream_host_and_timeout_for_real_adapter(
    monkeypatch: pytest.MonkeyPatch,
    json_logs: list[dict[str, Any]],
) -> None:
    monkeypatch.setenv("UPSTREAM_URL", "https://registry.example.test/vehicle-info")
    monkeypatch.setenv("UPSTREAM_TIMEOUT_SECONDS", str(UPSTREAM_TIMEOUT_SECONDS))
    reset_settings_cache()

    with TestClient(app=create_app()):
        pass

    [started] = [line for line in json_logs if line["message"] == "app_started"]
    assert started["upstream_adapter"] == "EncoreUpstream"
    assert started["upstream_host"] == "registry.example.test"
    assert started["upstream_timeout_seconds"] == UPSTREAM_TIMEOUT_SECONDS
    assert "/vehicle-info" not in started["upstream_host"]
