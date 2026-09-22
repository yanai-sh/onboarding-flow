"""Shared pytest fixtures for unit and integration tests."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import TYPE_CHECKING

import pytest
from litestar.testing import TestClient

from onboarding_flow.app import create_app
from onboarding_flow.config import reset_settings_cache
from onboarding_flow.memory_upstream import MemoryUpstream, success_upstream
from onboarding_flow.schemas import VehicleData
from tests.shared import ASSIGNMENT_SAMPLE_VEHICLE

if TYPE_CHECKING:
    from onboarding_flow.upstream import UpstreamPort


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
