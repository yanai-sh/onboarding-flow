"""Test-only literals and types shared across pytest modules."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any

from litestar.testing import TestClient

from onboarding_flow.schemas import VehicleData
from onboarding_flow.upstream import UpstreamPort

type OpenClient = Callable[[UpstreamPort], AbstractContextManager[TestClient]]

# Recorded from the live upstream (2026-09-22): vehicle text comes back in Hebrew.
LIVE_PLATE = "12345678"
LIVE_VEHICLE_JSON: dict[str, Any] = {
    "license_plate": LIVE_PLATE,
    "manufacturer": "טויוטה",
    "model": "קורולה",
    "year": 2020,
    "color": "לבן",
}
LIVE_VEHICLE = VehicleData.model_validate(LIVE_VEHICLE_JSON)
