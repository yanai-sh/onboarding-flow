from unittest.mock import AsyncMock, MagicMock

import pytest

from onboarding_flow.encore_upstream import EncoreUpstream
from onboarding_flow.upstream import UpstreamFailure, UpstreamFailureKind, UpstreamSuccess


@pytest.mark.asyncio
async def test_encore_upstream_parses_success_payload() -> None:
    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": {
            "license_plate": "12345678",
            "manufacturer": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "color": "White",
        },
    }
    session.post = AsyncMock(return_value=response)

    adapter = EncoreUpstream(session, "https://example.test/vehicle-info", 5.0)
    outcome = await adapter.fetch_vehicle("12345678")

    assert isinstance(outcome, UpstreamSuccess)
    assert outcome.vehicle.manufacturer == "Toyota"


@pytest.mark.asyncio
async def test_encore_upstream_normalizes_vehicle_fields_from_payload() -> None:
    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": {
            "license_plate": "  ab12cd34  ",
            "manufacturer": "  Toyota  ",
            "model": "Corolla",
            "year": 2020,
            "color": "White",
        },
    }
    session.post = AsyncMock(return_value=response)

    adapter = EncoreUpstream(session, "https://example.test/vehicle-info", 5.0)
    outcome = await adapter.fetch_vehicle("AB12CD34")

    assert isinstance(outcome, UpstreamSuccess)
    assert outcome.vehicle.license_plate == "AB12CD34"
    assert outcome.vehicle.manufacturer == "Toyota"


@pytest.mark.asyncio
async def test_encore_upstream_maps_http_404() -> None:
    session = MagicMock()
    response = MagicMock()
    response.status_code = 404
    session.post = AsyncMock(return_value=response)

    adapter = EncoreUpstream(session, "https://example.test/vehicle-info", 5.0)
    outcome = await adapter.fetch_vehicle("12345678")

    assert isinstance(outcome, UpstreamFailure)
    assert outcome.kind == UpstreamFailureKind.NOT_FOUND


@pytest.mark.asyncio
async def test_encore_upstream_invalid_plate_in_success_payload() -> None:
    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": {
            "license_plate": "bad-plate",
            "manufacturer": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "color": "White",
        },
    }
    session.post = AsyncMock(return_value=response)

    adapter = EncoreUpstream(session, "https://example.test/vehicle-info", 5.0)
    outcome = await adapter.fetch_vehicle("12345678")

    assert isinstance(outcome, UpstreamFailure)
    assert outcome.kind == UpstreamFailureKind.INVALID_RESPONSE


@pytest.mark.asyncio
async def test_encore_upstream_invalid_year_in_success_payload() -> None:
    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": {
            "license_plate": "12345678",
            "manufacturer": "Toyota",
            "model": "Corolla",
            "year": 0,
            "color": "White",
        },
    }
    session.post = AsyncMock(return_value=response)

    adapter = EncoreUpstream(session, "https://example.test/vehicle-info", 5.0)
    outcome = await adapter.fetch_vehicle("12345678")

    assert isinstance(outcome, UpstreamFailure)
    assert outcome.kind == UpstreamFailureKind.INVALID_RESPONSE
