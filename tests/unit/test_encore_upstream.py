import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from onboarding_flow.encore_upstream import EncoreUpstream
from onboarding_flow.upstream import UpstreamFailure, UpstreamFailureKind, UpstreamSuccess

PLATE = "12345678"
URL = "https://example.test/vehicle-info"
SUCCESS_DATA: dict[str, Any] = {
    "license_plate": PLATE,
    "manufacturer": "Toyota",
    "model": "Corolla",
    "year": 2020,
    "color": "White",
}
SUCCESS_BODY: dict[str, Any] = {"success": True, "data": SUCCESS_DATA}


def _client_returning(status_code: int, body: object = None, *, raw: str | None = None) -> Any:
    client = MagicMock()
    response = MagicMock()
    response.status_code = status_code
    if raw is not None:
        response.json.side_effect = json.JSONDecodeError("bad", raw, 0)
    else:
        response.json.return_value = body
    client.post = AsyncMock(return_value=response)
    return client


def _client_raising(exc: Exception) -> Any:
    client = MagicMock()
    client.post = AsyncMock(side_effect=exc)
    return client


def _failure_warnings(json_logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [line for line in json_logs if line["message"] == "upstream_request_failed"]


def _assert_upstream_failure(outcome: object, kind: UpstreamFailureKind) -> None:
    match outcome:
        case UpstreamFailure(kind=outcome_kind):
            assert outcome_kind == kind
        case _:
            pytest.fail(f"expected UpstreamFailure({kind!r}), got {outcome!r}")


def _assert_upstream_success(outcome: object) -> Any:
    match outcome:
        case UpstreamSuccess(vehicle=vehicle):
            return vehicle
        case _:
            pytest.fail(f"expected UpstreamSuccess, got {outcome!r}")


@pytest.mark.asyncio
async def test_encore_upstream_parses_success_payload() -> None:
    adapter = EncoreUpstream(_client_returning(200, SUCCESS_BODY), URL, 5.0)
    vehicle = _assert_upstream_success(await adapter.fetch_vehicle(PLATE))

    assert vehicle.manufacturer == "Toyota"


@pytest.mark.asyncio
async def test_encore_upstream_normalizes_vehicle_fields_from_payload() -> None:
    data = {**SUCCESS_DATA, "license_plate": "  ab12cd34  ", "manufacturer": "  Toyota  "}
    adapter = EncoreUpstream(_client_returning(200, {"success": True, "data": data}), URL, 5.0)
    vehicle = _assert_upstream_success(await adapter.fetch_vehicle("AB12CD34"))

    assert vehicle.license_plate == "AB12CD34"
    assert vehicle.manufacturer == "Toyota"


@pytest.mark.asyncio
async def test_encore_upstream_maps_http_404() -> None:
    adapter = EncoreUpstream(_client_returning(404), URL, 5.0)
    _assert_upstream_failure(await adapter.fetch_vehicle(PLATE), UpstreamFailureKind.NOT_FOUND)


@pytest.mark.asyncio
async def test_encore_upstream_maps_timeout() -> None:
    adapter = EncoreUpstream(_client_raising(httpx.ReadTimeout("upstream slow")), URL, 5.0)
    _assert_upstream_failure(await adapter.fetch_vehicle(PLATE), UpstreamFailureKind.TIMEOUT)


@pytest.mark.parametrize(
    "exc",
    [
        httpx.ConnectError("refused"),
        httpx.RemoteProtocolError("connection closed"),
        # RequestError subclasses that are not TransportError must still stay inside the envelope.
        httpx.DecodingError("bad content-encoding"),
        httpx.TooManyRedirects("loop"),
    ],
)
@pytest.mark.asyncio
async def test_encore_upstream_maps_request_errors_to_unavailable(exc: httpx.RequestError) -> None:
    adapter = EncoreUpstream(_client_raising(exc), URL, 5.0)
    _assert_upstream_failure(await adapter.fetch_vehicle(PLATE), UpstreamFailureKind.UNAVAILABLE)


@pytest.mark.asyncio
async def test_encore_upstream_maps_http_5xx() -> None:
    adapter = EncoreUpstream(_client_returning(503), URL, 5.0)
    _assert_upstream_failure(await adapter.fetch_vehicle(PLATE), UpstreamFailureKind.UNAVAILABLE)


@pytest.mark.parametrize(
    "data_override",
    [
        {"license_plate": "bad-plate"},
        {"year": 0},
    ],
)
@pytest.mark.asyncio
async def test_encore_upstream_invalid_success_payload(data_override: dict[str, Any]) -> None:
    body = {"success": True, "data": {**SUCCESS_DATA, **data_override}}
    adapter = EncoreUpstream(_client_returning(200, body), URL, 5.0)
    _assert_upstream_failure(
        await adapter.fetch_vehicle(PLATE), UpstreamFailureKind.INVALID_RESPONSE
    )


@pytest.mark.asyncio
async def test_encore_upstream_warns_on_timeout_with_exception_class(
    json_logs: list[dict[str, Any]],
) -> None:
    adapter = EncoreUpstream(_client_raising(httpx.ReadTimeout("slow")), URL, 5.0)
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
    adapter = EncoreUpstream(_client_returning(503), URL, 5.0)
    await adapter.fetch_vehicle(PLATE)

    [warning] = _failure_warnings(json_logs)
    assert warning["kind"] == "unavailable"
    assert warning["status_code"] == 503
    assert "exception" not in warning


@pytest.mark.asyncio
async def test_encore_upstream_warns_on_malformed_json(
    json_logs: list[dict[str, Any]],
) -> None:
    adapter = EncoreUpstream(_client_returning(200, raw="<html>"), URL, 5.0)
    outcome = await adapter.fetch_vehicle(PLATE)

    _assert_upstream_failure(outcome, UpstreamFailureKind.INVALID_RESPONSE)
    [warning] = _failure_warnings(json_logs)
    assert warning["kind"] == "invalid_response"
    assert warning["status_code"] == 200


@pytest.mark.asyncio
async def test_encore_upstream_not_found_is_not_a_warning(
    json_logs: list[dict[str, Any]],
) -> None:
    adapter = EncoreUpstream(_client_returning(200, {"success": False}), URL, 5.0)
    outcome = await adapter.fetch_vehicle(PLATE)

    _assert_upstream_failure(outcome, UpstreamFailureKind.NOT_FOUND)
    assert not [line for line in json_logs if line["severity"] == "WARNING"]


@pytest.mark.parametrize(
    "client",
    [
        _client_returning(200, SUCCESS_BODY),
        _client_raising(httpx.ReadTimeout("slow")),
        _client_raising(httpx.ConnectError("refused")),
        _client_raising(httpx.DecodingError("bad encoding")),
        _client_returning(503),
        _client_returning(404),
        _client_returning(200, raw="<html>"),
        _client_returning(200, {"success": True, "data": {"license_plate": PLATE, "year": 0}}),
    ],
)
@pytest.mark.asyncio
async def test_encore_upstream_never_logs_raw_plate(
    client: Any,
    json_logs: list[dict[str, Any]],
) -> None:
    adapter = EncoreUpstream(client, URL, 5.0)
    await adapter.fetch_vehicle(PLATE)

    assert PLATE not in json.dumps(json_logs)
