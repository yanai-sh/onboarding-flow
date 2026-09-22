import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from onboarding_flow.encore_upstream import EncoreUpstream
from onboarding_flow.upstream import UpstreamFailure, UpstreamFailureKind, UpstreamSuccess

PLATE = "12345678"


def _session_returning(status_code: int, body: object = None, *, raw: str | None = None) -> Any:
    session = MagicMock()
    response = MagicMock()
    response.status_code = status_code
    if raw is not None:
        response.json.side_effect = json.JSONDecodeError("bad", raw, 0)
    else:
        response.json.return_value = body
    session.post = AsyncMock(return_value=response)
    return session


def _session_raising(exc: Exception) -> Any:
    session = MagicMock()
    session.post = AsyncMock(side_effect=exc)
    return session


def _failure_warnings(json_logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [line for line in json_logs if line["message"] == "upstream_request_failed"]


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
async def test_encore_upstream_warns_on_timeout_with_exception_class(
    json_logs: list[dict[str, Any]],
) -> None:
    adapter = EncoreUpstream(
        _session_raising(httpx.ReadTimeout("slow")), "https://example.test/vehicle-info", 5.0
    )
    await adapter.fetch_vehicle(PLATE)

    [warning] = _failure_warnings(json_logs)
    assert warning["severity"] == "WARNING"
    assert warning["kind"] == "timeout"
    assert warning["exception"] == "ReadTimeout"
    assert "status_code" not in warning
    assert isinstance(warning["duration_ms"], int | float)


@pytest.mark.asyncio
async def test_encore_upstream_warns_on_5xx_with_status_code(
    json_logs: list[dict[str, Any]],
) -> None:
    adapter = EncoreUpstream(_session_returning(503), "https://example.test/vehicle-info", 5.0)
    await adapter.fetch_vehicle(PLATE)

    [warning] = _failure_warnings(json_logs)
    assert warning["kind"] == "unavailable"
    assert warning["status_code"] == 503
    assert "exception" not in warning


@pytest.mark.asyncio
async def test_encore_upstream_warns_on_malformed_json(
    json_logs: list[dict[str, Any]],
) -> None:
    adapter = EncoreUpstream(
        _session_returning(200, raw="<html>"), "https://example.test/vehicle-info", 5.0
    )
    outcome = await adapter.fetch_vehicle(PLATE)

    _assert_upstream_failure(outcome, UpstreamFailureKind.INVALID_RESPONSE)
    [warning] = _failure_warnings(json_logs)
    assert warning["kind"] == "invalid_response"
    assert warning["status_code"] == 200


@pytest.mark.asyncio
async def test_encore_upstream_not_found_is_not_a_warning(
    json_logs: list[dict[str, Any]],
) -> None:
    adapter = EncoreUpstream(
        _session_returning(200, {"success": False}), "https://example.test/vehicle-info", 5.0
    )
    outcome = await adapter.fetch_vehicle(PLATE)

    _assert_upstream_failure(outcome, UpstreamFailureKind.NOT_FOUND)
    assert not _failure_warnings(json_logs)
    assert not [line for line in json_logs if line["severity"] == "WARNING"]


@pytest.mark.parametrize(
    "session",
    [
        _session_raising(httpx.ReadTimeout("slow")),
        _session_raising(httpx.ConnectError("refused")),
        _session_returning(503),
        _session_returning(404),
        _session_returning(200, raw="<html>"),
        _session_returning(200, {"success": True, "data": {"license_plate": PLATE, "year": 0}}),
    ],
)
@pytest.mark.asyncio
async def test_encore_upstream_never_logs_raw_plate(
    session: Any,
    json_logs: list[dict[str, Any]],
) -> None:
    adapter = EncoreUpstream(session, "https://example.test/vehicle-info", 5.0)
    await adapter.fetch_vehicle(PLATE)

    assert PLATE not in json.dumps(json_logs)


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
