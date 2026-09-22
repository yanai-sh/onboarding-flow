import json
import logging
import sys
from typing import Any

from onboarding_flow.logging_config import TRACE_ID, JsonFormatter, TraceIdFilter

_logger = logging.getLogger("tests.logging_config")


def _record(
    message: str,
    *,
    level: int = logging.INFO,
    extra: dict[str, Any] | None = None,
    exc_info: Any = None,
) -> logging.LogRecord:
    return _logger.makeRecord(
        _logger.name,
        level,
        __file__,
        1,
        message,
        (),
        exc_info,
        extra=extra,
    )


def test_json_formatter_emits_cloud_logging_fields_and_extras() -> None:
    line = JsonFormatter().format(_record("hello", extra={"plate_mask": "****5678", "count": 2}))

    payload = json.loads(line)
    assert payload["severity"] == "INFO"
    assert payload["message"] == "hello"
    assert payload["logger"] == "tests.logging_config"
    assert payload["plate_mask"] == "****5678"
    assert payload["count"] == 2
    assert payload["time"].endswith("+00:00")


def test_json_formatter_omits_none_values() -> None:
    payload = json.loads(JsonFormatter().format(_record("x", extra={"error_code": None})))
    assert "error_code" not in payload


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
    payload = json.loads(line)
    assert payload["severity"] == "ERROR"
    assert "ValueError: boom" in payload["stack_trace"]


def test_trace_id_filter_applies_request_context() -> None:
    token = TRACE_ID.set("ctx-trace")
    try:
        record = _record("x")
        assert TraceIdFilter().filter(record) is True
    finally:
        TRACE_ID.reset(token)

    assert json.loads(JsonFormatter().format(record))["trace_id"] == "ctx-trace"


def test_trace_id_filter_keeps_explicit_trace_id() -> None:
    token = TRACE_ID.set("ctx-trace")
    try:
        record = _record("x", extra={"trace_id": "explicit"})
        TraceIdFilter().filter(record)
    finally:
        TRACE_ID.reset(token)

    assert json.loads(JsonFormatter().format(record))["trace_id"] == "explicit"


def test_trace_id_filter_outside_request_leaves_trace_id_absent() -> None:
    record = _record("x")
    TraceIdFilter().filter(record)

    assert "trace_id" not in json.loads(JsonFormatter().format(record))
