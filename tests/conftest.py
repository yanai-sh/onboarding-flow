"""Shared pytest fixtures for unit and integration tests."""

import json
import logging
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import TYPE_CHECKING, Any

import pytest
from litestar.testing import TestClient

from onboarding_flow.app import create_app
from onboarding_flow.config import reset_settings_cache
from onboarding_flow.logging_config import JsonFormatter, TraceIdFilter
from onboarding_flow.memory_upstream import MemoryUpstream, success_upstream
from onboarding_flow.schemas import VehicleData
from tests.shared import ASSIGNMENT_SAMPLE_VEHICLE

if TYPE_CHECKING:
    from onboarding_flow.upstream import UpstreamPort


class _JsonLineHandler(logging.Handler):
    """Collects the exact JSON lines production would write to stdout."""

    def __init__(self, lines: list[dict[str, Any]]) -> None:
        super().__init__()
        self._lines = lines

    def emit(self, record: logging.LogRecord) -> None:
        self._lines.append(json.loads(self.format(record)))


@pytest.fixture
def json_logs() -> Iterator[list[dict[str, Any]]]:
    """Parsed JSON log lines emitted during the test via the production filter and formatter."""
    lines: list[dict[str, Any]] = []
    handler = _JsonLineHandler(lines)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(TraceIdFilter())
    root = logging.getLogger()
    previous_level = root.level
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    try:
        yield lines
    finally:
        root.removeHandler(handler)
        root.setLevel(previous_level)


@pytest.fixture(autouse=True)
def _reset_settings_cache_between_tests() -> Iterator[None]:
    reset_settings_cache()
    yield
    reset_settings_cache()


@pytest.fixture
def assignment_vehicle() -> VehicleData:
    return ASSIGNMENT_SAMPLE_VEHICLE


@pytest.fixture
def assignment_plate(assignment_vehicle: VehicleData) -> str:
    return assignment_vehicle.license_plate


@pytest.fixture
def success_memory_upstream(assignment_vehicle: VehicleData) -> MemoryUpstream:
    return success_upstream(assignment_vehicle)


@pytest.fixture
def api_client(success_memory_upstream: MemoryUpstream) -> Iterator[TestClient]:
    with TestClient(app=create_app(upstream=success_memory_upstream)) as client:
        yield client


@pytest.fixture
def open_api_client() -> Callable[[UpstreamPort], AbstractContextManager[TestClient]]:
    @contextmanager
    def _open(upstream: UpstreamPort) -> Iterator[TestClient]:
        with TestClient(app=create_app(upstream=upstream)) as client:
            yield client

    return _open
