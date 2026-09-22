import json
import logging
import sys
from typing import Any

import pytest

from onboarding_flow.observability import TRACE_ID, JsonFormatter, TraceIdFilter, mask_plate

_logger = logging.getLogger("tests.observability")


def _record(
    message: str,
    *,
    level: int = logging.INFO,
    extra: dict[str, Any] | None = None,
    exc_info: Any = None,
) -> logging.LogRecord:
    return _logger.makeRecord(_logger.name, level, __file__, 1, message, (), exc_info, extra=extra)


def test_json_formatter_emits_cloud_logging_fields_and_non_null_extras() -> None:
    extra = {"plate_mask": "****5678", "count": 2}
    payload = json.loads(JsonFormatter().format(_record("hello", extra={**extra, "gone": None})))

    assert payload["severity"] == "INFO"
    assert payload["message"] == "hello"
    assert payload["logger"] == "tests.observability"
    assert payload["time"].endswith("+00:00")
    assert {key: payload[key] for key in extra} == extra
    assert "gone" not in payload


def _boom() -> None:
    msg = "boom"
    raise ValueError(msg)


def test_json_formatter_renders_exceptions_on_one_line() -> None:
    try:
        _boom()
    except ValueError:
        record = _record("failed", level=logging.ERROR, exc_info=sys.exc_info())

    line = JsonFormatter().format(record)

    assert "\n" not in line
    assert "ValueError: boom" in json.loads(line)["stack_trace"]


def test_trace_id_filter_copies_request_context_onto_records() -> None:
    token = TRACE_ID.set("ctx-trace")
    try:
        inside = _record("x")
        TraceIdFilter().filter(inside)
    finally:
        TRACE_ID.reset(token)
    outside = _record("x")
    TraceIdFilter().filter(outside)

    assert json.loads(JsonFormatter().format(inside))["trace_id"] == "ctx-trace"
    assert "trace_id" not in json.loads(JsonFormatter().format(outside))


@pytest.mark.parametrize(
    ("plate", "masked"),
    [("12345678", "****5678"), ("1234567", "***4567"), ("1234", "****")],
)
def test_mask_plate_keeps_only_the_last_four_characters(plate: str, masked: str) -> None:
    assert mask_plate(plate) == masked
