from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from onboarding_flow.encore_upstream import EncoreUpstream
from onboarding_flow.upstream import UpstreamFailure, UpstreamFailureKind, UpstreamSuccess


def _assert_upstream_failure(outcome: object, kind: UpstreamFailureKind) -> None:
    match outcome:
        case UpstreamFailure(kind=outcome_kind):
            assert outcome_kind == kind
        case _:
            pytest.fail(f"expected UpstreamFailure({kind!r}), got {outcome!r}")


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

    match outcome:
        case UpstreamSuccess(vehicle=vehicle):
            assert vehicle.manufacturer == "Toyota"
        case _:
            pytest.fail(f"expected UpstreamSuccess, got {outcome!r}")


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

    match outcome:
        case UpstreamSuccess(vehicle=vehicle):
            assert vehicle.license_plate == "AB12CD34"
            assert vehicle.manufacturer == "Toyota"
        case _:
            pytest.fail(f"expected UpstreamSuccess, got {outcome!r}")


@pytest.mark.asyncio
async def test_encore_upstream_maps_http_404() -> None:
    session = MagicMock()
    response = MagicMock()
    response.status_code = 404
    session.post = AsyncMock(return_value=response)

    adapter = EncoreUpstream(session, "https://example.test/vehicle-info", 5.0)
    outcome = await adapter.fetch_vehicle("12345678")

    _assert_upstream_failure(outcome, UpstreamFailureKind.NOT_FOUND)


@pytest.mark.asyncio
async def test_encore_upstream_maps_timeout() -> None:
    session = MagicMock()
    session.post = AsyncMock(side_effect=httpx.ReadTimeout("upstream slow"))

    adapter = EncoreUpstream(session, "https://example.test/vehicle-info", 5.0)
    outcome = await adapter.fetch_vehicle("12345678")

    _assert_upstream_failure(outcome, UpstreamFailureKind.TIMEOUT)


@pytest.mark.parametrize(
    "exc",
    [
        httpx.ConnectError("refused"),
        httpx.RemoteProtocolError("connection closed"),
    ],
)
@pytest.mark.asyncio
async def test_encore_upstream_maps_transport_errors(exc: httpx.TransportError) -> None:
    session = MagicMock()
    session.post = AsyncMock(side_effect=exc)

    adapter = EncoreUpstream(session, "https://example.test/vehicle-info", 5.0)
    outcome = await adapter.fetch_vehicle("12345678")

    _assert_upstream_failure(outcome, UpstreamFailureKind.UNAVAILABLE)


@pytest.mark.asyncio
async def test_encore_upstream_maps_http_5xx() -> None:
    session = MagicMock()
    response = MagicMock()
    response.status_code = 503
    session.post = AsyncMock(return_value=response)

    adapter = EncoreUpstream(session, "https://example.test/vehicle-info", 5.0)
    outcome = await adapter.fetch_vehicle("12345678")

    _assert_upstream_failure(outcome, UpstreamFailureKind.UNAVAILABLE)


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

    _assert_upstream_failure(outcome, UpstreamFailureKind.INVALID_RESPONSE)


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

    _assert_upstream_failure(outcome, UpstreamFailureKind.INVALID_RESPONSE)
