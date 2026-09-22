import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from onboarding_flow.observability import mask_plate, parse_trace_id, trace_id_from_request

UUID_VERSION_7 = 7


def _assert_uuid7(trace: str) -> None:
    assert uuid.UUID(trace).version == UUID_VERSION_7


def test_mask_plate_hides_prefix() -> None:
    assert mask_plate("12345678") == "****5678"


def test_mask_plate_short_values() -> None:
    assert mask_plate("AB") == "****"


def test_parse_trace_id_generates_uuid7_when_header_missing() -> None:
    trace = parse_trace_id(None)
    _assert_uuid7(trace)


def test_parse_trace_id_generates_uuid7_when_header_blank() -> None:
    trace = parse_trace_id("   ")
    _assert_uuid7(trace)


def test_parse_trace_id_accepts_valid_client_value() -> None:
    assert parse_trace_id("client-trace-99") == "client-trace-99"


def test_parse_trace_id_replaces_invalid_header_with_uuid7() -> None:
    invalid = "x" * 200
    trace = parse_trace_id(invalid)
    assert trace != invalid
    _assert_uuid7(trace)


def test_trace_id_from_request_requires_middleware_state() -> None:
    request = MagicMock()
    request.state = SimpleNamespace()
    with pytest.raises(RuntimeError, match="TraceMiddleware"):
        trace_id_from_request(request)


def test_trace_id_from_request_returns_bound_value() -> None:
    request = MagicMock()
    request.state = SimpleNamespace(trace_id="bound-trace")
    assert trace_id_from_request(request) == "bound-trace"
