import json
import uuid
from http import HTTPStatus
from typing import Any

import httpx
import pytest
from litestar.testing import TestClient

from onboarding_flow.observability import MAX_TRACE_ID_LENGTH
from onboarding_flow.schemas import ErrorCode
from onboarding_flow.upstream import EncoreUpstream
from tests.fakes import MemoryUpstream
from tests.shared import LIVE_PLATE, LIVE_VEHICLE, LIVE_VEHICLE_JSON, OpenClient


def _completed(json_logs: list[dict[str, Any]]) -> dict[str, Any]:
    [event] = [line for line in json_logs if line["message"] == "vehicle_lookup_completed"]
    return event


def _lookup(client: TestClient, plate: object, **kwargs: Any) -> httpx.Response:
    return client.post("/vehicle-info", json={"license_plate": plate}, **kwargs)


def test_lookup_returns_vehicle_in_assignment_shape(open_client: OpenClient) -> None:
    upstream = MemoryUpstream(LIVE_VEHICLE)
    with open_client(upstream) as client:
        response = _lookup(client, LIVE_PLATE)

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body == {
        "success": True,
        "data": LIVE_VEHICLE_JSON,
        "error_code": None,
        "message": None,
        "trace_id": body["trace_id"],
    }
    assert "טויוטה".encode() in response.content
    assert uuid.UUID(body["trace_id"]).version == 7
    assert response.headers["x-trace-id"] == body["trace_id"]
    assert upstream.plates == [LIVE_PLATE]


@pytest.mark.parametrize(
    ("typed", "sent"),
    [
        ("1234567", "1234567"),
        ("12-345-67", "1234567"),
        ("123-45-678", "12345678"),
        (" 123 45 678 ", "12345678"),
        ("12.345.67", "1234567"),
    ],
)
def test_formatted_plates_are_sent_upstream_as_digits(
    open_client: OpenClient, typed: str, sent: str
) -> None:
    upstream = MemoryUpstream(LIVE_VEHICLE)
    with open_client(upstream) as client:
        response = _lookup(client, typed)

    assert response.json()["success"] is True
    assert upstream.plates == [sent]


@pytest.mark.parametrize(
    "plate",
    # The last value is 1234567 in full-width digits, which str.isdigit() would accept.
    [
        "",
        "   ",
        "ABC",
        "123456",
        "123456789",
        "12_345_67",
        "12/345/67",
        "\uff11\uff12\uff13\uff14\uff15\uff16\uff17",
    ],
)
def test_plate_breaking_the_rule_returns_invalid_request_without_upstream_call(
    open_client: OpenClient, plate: str, json_logs: list[dict[str, Any]]
) -> None:
    upstream = MemoryUpstream(LIVE_VEHICLE)
    with open_client(upstream) as client:
        response = _lookup(client, plate)

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error_code"] == "INVALID_REQUEST"
    assert body["message"] == (
        "That plate number doesn't look right. Israeli plates have 7 or 8 digits."
    )
    assert upstream.plates == []
    event = _completed(json_logs)
    assert event["error_code"] == "INVALID_REQUEST"
    assert "plate_mask" not in event


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {"content": b"not json", "headers": {"content-type": "application/json"}},
        {"json": {}},
        {"json": {"license_plate": 12345678}},
        {"json": {"license_plate": None}},
        {"json": {"license_plate": "1" * 33}},
    ],
    ids=["malformed-json", "missing-field", "integer", "null", "over-length"],
)
def test_malformed_request_bodies_are_rejected_by_the_framework(
    open_client: OpenClient, request_kwargs: dict[str, Any], json_logs: list[dict[str, Any]]
) -> None:
    upstream = MemoryUpstream(LIVE_VEHICLE)
    with open_client(upstream) as client:
        response = client.post("/vehicle-info", **request_kwargs)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert upstream.plates == []
    assert not [line for line in json_logs if line["severity"] == "ERROR"]


@pytest.mark.parametrize("code", list(ErrorCode))
def test_every_error_code_has_a_message(open_client: OpenClient, code: ErrorCode) -> None:
    with open_client(MemoryUpstream(code)) as client:
        response = _lookup(client, LIVE_PLATE)

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error_code"] == code.value
    assert body["message"]
    assert LIVE_PLATE not in body["message"]


def test_completion_log_masks_plate_and_carries_client_trace_id(
    open_client: OpenClient, json_logs: list[dict[str, Any]]
) -> None:
    with open_client(MemoryUpstream(ErrorCode.VEHICLE_NOT_FOUND)) as client:
        response = _lookup(client, "123-45-678", headers={"X-Trace-ID": "client-trace-77"})

    assert response.headers["x-trace-id"] == "client-trace-77"
    assert response.json()["trace_id"] == "client-trace-77"
    event = _completed(json_logs)
    assert event["trace_id"] == "client-trace-77"
    assert event["plate_mask"] == "****5678"
    assert event["success"] is False
    assert event["error_code"] == "VEHICLE_NOT_FOUND"
    assert event["duration_ms"] >= 0
    logged = json.dumps(json_logs, ensure_ascii=False)
    assert "12345678" not in logged
    assert "123-45-678" not in logged


def test_input_breaking_the_plate_rule_never_reaches_the_logs(
    open_client: OpenClient, json_logs: list[dict[str, Any]]
) -> None:
    with open_client(MemoryUpstream(LIVE_VEHICLE)) as client:
        _lookup(client, "SECRET-99")

    assert json_logs
    assert "SECRET" not in json.dumps(json_logs, ensure_ascii=False)


@pytest.mark.parametrize(
    "header",
    [b"x" * (MAX_TRACE_ID_LENGTH + 1), b"a b", b"abc\tdef", "abcé".encode()],
    ids=["too-long", "space", "tab", "non-ascii"],
)
def test_invalid_trace_id_header_is_replaced(open_client: OpenClient, header: bytes) -> None:
    with open_client(MemoryUpstream(LIVE_VEHICLE)) as client:
        response = _lookup(client, LIVE_PLATE, headers={"X-Trace-ID": header})

    trace = response.json()["trace_id"]
    assert uuid.UUID(trace).version == 7
    assert response.headers.get_list("x-trace-id") == [trace]


def test_unhandled_adapter_error_returns_500_and_logs_trace_id(
    open_client: OpenClient, json_logs: list[dict[str, Any]]
) -> None:
    with open_client(MemoryUpstream(RuntimeError("adapter exploded"))) as client:
        response = _lookup(client, LIVE_PLATE, headers={"X-Trace-ID": "client-trace-500"})

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    [error] = [line for line in json_logs if line["severity"] == "ERROR"]
    assert error["message"] == "request_failed"
    assert error["trace_id"] == "client-trace-500"
    assert "RuntimeError: adapter exploded" in error["stack_trace"]
    assert LIVE_PLATE not in json.dumps(json_logs)


def test_hebrew_vehicle_round_trips_through_the_real_adapter(
    open_client: OpenClient, json_logs: list[dict[str, Any]]
) -> None:
    def registry(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": True, "data": LIVE_VEHICLE_JSON})

    client = httpx.AsyncClient(transport=httpx.MockTransport(registry))
    upstream = EncoreUpstream(client, "https://registry.test/vehicle-info", 5.0)
    with open_client(upstream) as api:
        response = _lookup(api, LIVE_PLATE)

    assert response.json()["data"] == LIVE_VEHICLE_JSON
    assert "קורולה".encode() in response.content
    # httpx's own INFO request line would leak outside the documented event catalogue.
    assert [line["message"] for line in json_logs] == [
        "app_started",
        "vehicle_lookup_completed",
        "app_stopping",
    ]
    assert LIVE_PLATE not in json.dumps(json_logs)
