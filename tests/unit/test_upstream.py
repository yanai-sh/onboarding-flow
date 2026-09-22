import asyncio
import json
import time
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from onboarding_flow.schemas import ErrorCode
from onboarding_flow.upstream import EncoreUpstream
from tests.shared import LIVE_PLATE, LIVE_VEHICLE, LIVE_VEHICLE_JSON

URL = "https://registry.test/vehicle-info"

type Handler = Callable[[httpx.Request], Any]


def _adapter(handler: Handler, *, timeout_seconds: float = 5.0) -> EncoreUpstream:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return EncoreUpstream(client, URL, timeout_seconds)


def _responding(status_code: int, body: object = None, *, content: bytes | None = None) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        if content is not None:
            return httpx.Response(status_code, content=content)
        return httpx.Response(status_code, json=body)

    return handler


def _warnings(json_logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [line for line in json_logs if line["message"] == "upstream_request_failed"]


async def test_posts_digits_as_json_and_parses_the_hebrew_vehicle(
    json_logs: list[dict[str, Any]],
) -> None:
    sent: list[httpx.Request] = []

    def registry(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, json={"success": True, "data": LIVE_VEHICLE_JSON})

    outcome = await _adapter(registry).fetch_vehicle(LIVE_PLATE)

    assert outcome == LIVE_VEHICLE
    [request] = sent
    assert request.method == "POST"
    assert str(request.url) == URL
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {"license_plate": LIVE_PLATE}
    assert not _warnings(json_logs)


async def test_upstream_vehicle_fields_are_normalized() -> None:
    data = {**LIVE_VEHICLE_JSON, "license_plate": "123-45-678", "manufacturer": "  טויוטה  "}
    outcome = await _adapter(_responding(200, {"success": True, "data": data})).fetch_vehicle(
        LIVE_PLATE
    )

    assert outcome == LIVE_VEHICLE


LIVE_NOT_FOUND = {"detail": {"success": False, "error": "רכב עם מספר 00000000 לא נמצא במאגר"}}
LIVE_REJECTED = {"detail": [{"msg": "מספר רישוי חייב להכיל 7 או 8 ספרות"}]}


@pytest.mark.parametrize(
    ("handler", "expected", "warned_status"),
    [
        (_responding(404, LIVE_NOT_FOUND), ErrorCode.VEHICLE_NOT_FOUND, None),
        (_responding(200, {"success": False}), ErrorCode.VEHICLE_NOT_FOUND, None),
        (_responding(404, {"detail": "Not Found"}), ErrorCode.UPSTREAM_UNAVAILABLE, 404),
        (_responding(404, content=b"<html>"), ErrorCode.UPSTREAM_UNAVAILABLE, 404),
        (_responding(400, {"detail": "bad plate"}), ErrorCode.INVALID_REQUEST, 400),
        (_responding(422, LIVE_REJECTED), ErrorCode.INVALID_REQUEST, 422),
        (_responding(429), ErrorCode.UPSTREAM_UNAVAILABLE, 429),
        (_responding(503), ErrorCode.UPSTREAM_UNAVAILABLE, 503),
        (_responding(200, content=b"<html>"), ErrorCode.UPSTREAM_INVALID_RESPONSE, 200),
        (_responding(200, {"vehicle": "?"}), ErrorCode.UPSTREAM_INVALID_RESPONSE, 200),
        (
            _responding(200, {"success": True, "data": {**LIVE_VEHICLE_JSON, "year": 0}}),
            ErrorCode.UPSTREAM_INVALID_RESPONSE,
            200,
        ),
        (
            _responding(200, {"success": True, "data": {**LIVE_VEHICLE_JSON, "model": " "}}),
            ErrorCode.UPSTREAM_INVALID_RESPONSE,
            200,
        ),
        (
            _responding(
                200, {"success": True, "data": {**LIVE_VEHICLE_JSON, "license_plate": "ABC"}}
            ),
            ErrorCode.UPSTREAM_INVALID_RESPONSE,
            200,
        ),
    ],
    ids=[
        "404-live-not-found",
        "200-success-false",
        "404-generic",
        "404-html",
        "400",
        "422-live",
        "429",
        "503",
        "200-not-json",
        "200-unknown-shape",
        "200-bad-year",
        "200-blank-model",
        "200-bad-plate",
    ],
)
async def test_maps_upstream_responses(
    handler: Handler,
    expected: ErrorCode,
    warned_status: int | None,
    json_logs: list[dict[str, Any]],
) -> None:
    outcome = await _adapter(handler).fetch_vehicle(LIVE_PLATE)

    assert outcome == expected
    warnings = _warnings(json_logs)
    if warned_status is None:
        assert not warnings
    else:
        [warning] = warnings
        assert warning["severity"] == "WARNING"
        assert warning["error_code"] == expected.value
        assert warning["status_code"] == warned_status
        assert "exception" not in warning
    assert LIVE_PLATE not in json.dumps(json_logs)


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (httpx.ReadTimeout("slow"), ErrorCode.UPSTREAM_TIMEOUT),
        (httpx.ConnectTimeout("slow"), ErrorCode.UPSTREAM_TIMEOUT),
        (httpx.ConnectError("refused"), ErrorCode.UPSTREAM_UNAVAILABLE),
        (httpx.RemoteProtocolError("closed"), ErrorCode.UPSTREAM_UNAVAILABLE),
        # RequestError subclasses that are not TransportError must still stay inside the envelope.
        (httpx.DecodingError("bad content-encoding"), ErrorCode.UPSTREAM_UNAVAILABLE),
        (httpx.TooManyRedirects("loop"), ErrorCode.UPSTREAM_UNAVAILABLE),
    ],
)
async def test_maps_request_errors(
    exc: httpx.RequestError, expected: ErrorCode, json_logs: list[dict[str, Any]]
) -> None:
    def failing(request: httpx.Request) -> httpx.Response:
        raise exc

    outcome = await _adapter(failing).fetch_vehicle(LIVE_PLATE)

    assert outcome == expected
    [warning] = _warnings(json_logs)
    assert warning["error_code"] == expected.value
    assert warning["exception"] == type(exc).__name__
    assert "status_code" not in warning
    assert LIVE_PLATE not in json.dumps(json_logs)


async def test_timeout_bounds_the_whole_exchange(json_logs: list[dict[str, Any]]) -> None:
    async def slow(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(2)
        return httpx.Response(200, json={"success": True, "data": LIVE_VEHICLE_JSON})

    started = time.perf_counter()
    outcome = await _adapter(slow, timeout_seconds=0.05).fetch_vehicle(LIVE_PLATE)

    assert outcome == ErrorCode.UPSTREAM_TIMEOUT
    assert time.perf_counter() - started < 1
    [warning] = _warnings(json_logs)
    assert warning["exception"] == "TimeoutError"
