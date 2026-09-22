"""JSON logging on stdout for Cloud Run, request trace ids, and PII-safe log helpers."""

import json
import logging
import logging.config
import re
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any, override

from litestar.datastructures import Headers
from litestar.enums import ScopeType
from litestar.exceptions import HTTPException
from litestar.middleware.base import ASGIMiddleware
from litestar.types import ASGIApp, Message, Receive, Scope, Send

TRACE_HEADER = "X-Trace-ID"
MAX_TRACE_ID_LENGTH = 128
# Printable ASCII only: the value is echoed into a response header and every log line.
_TRACE_ID_PATTERN = re.compile(rf"[\x21-\x7E]{{1,{MAX_TRACE_ID_LENGTH}}}")
# Trailing characters left visible by ``mask_plate``; enough to correlate, too few to identify.
PLATE_MASK_VISIBLE_CHARS = 4

TRACE_ID: ContextVar[str | None] = ContextVar("trace_id", default=None)

# Attributes every LogRecord carries; anything else came from ``extra``.
_STANDARD_ATTRS = frozenset(
    {*vars(logging.LogRecord("", logging.INFO, "", 0, "", None, None)), "message", "asctime"}
)

logger = logging.getLogger(__name__)


class TraceIdFilter(logging.Filter):
    """Attach the current request's trace id to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = TRACE_ID.get()
        return True


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per line using Cloud Logging field names."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "severity": record.levelname,
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "message": record.getMessage(),
            "logger": record.name,
        }
        payload.update(
            (key, value)
            for key, value in vars(record).items()
            if key not in _STANDARD_ATTRS and value is not None
        )
        if record.exc_info:
            payload["stack_trace"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Route application and Granian worker logs through the JSON handler.

    Granian configures stdlib logging before loading the app, so calling this at
    app construction lets the same handler own the ``_granian`` worker logger.
    Idempotent: a root handler already emitting JSON means the pipeline is in
    place, so ``dictConfig`` (which replaces root handlers) is not re-run.
    """
    if any(isinstance(h.formatter, JsonFormatter) for h in logging.getLogger().handlers):
        return

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"trace_id": {"()": TraceIdFilter}},
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "filters": ["trace_id"],
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "_granian": {"handlers": ["stdout"], "level": level, "propagate": False},
                # httpx logs every request at INFO, including the upstream URL; the
                # event catalogue in ARCHITECTURE.md is the whole log surface.
                "httpx": {"level": "WARNING"},
                "httpcore": {"level": "WARNING"},
            },
            "root": {"handlers": ["stdout"], "level": level},
        }
    )


def elapsed_ms(started: float) -> float:
    """Milliseconds since a ``time.perf_counter()`` reading, rounded for log fields."""
    return round((time.perf_counter() - started) * 1000, 1)


def mask_plate(license_plate: str) -> str:
    """Return a deterministic partial mask; never log the full plate."""
    hidden = len(license_plate) - PLATE_MASK_VISIBLE_CHARS
    if hidden <= 0:
        return "*" * PLATE_MASK_VISIBLE_CHARS
    return f"{'*' * hidden}{license_plate[-PLATE_MASK_VISIBLE_CHARS:]}"


def parse_trace_id(header_value: str | None) -> str:
    """Accept a well-formed client ``X-Trace-ID``; otherwise mint a UUIDv7."""
    candidate = (header_value or "").strip()
    if _TRACE_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid.uuid7())


class TraceMiddleware(ASGIMiddleware):
    """Bind one trace id per request to request state, the log context, and the response."""

    scopes = (ScopeType.HTTP,)

    @override
    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        trace_id = parse_trace_id(Headers.from_scope(scope).get(TRACE_HEADER))
        scope.setdefault("state", {})["trace_id"] = trace_id
        trace_header = (TRACE_HEADER.lower().encode(), trace_id.encode())

        async def send_with_trace_header(message: Message) -> None:
            if message["type"] == "http.response.start":
                message["headers"] = [*message.get("headers", []), trace_header]
            await send(message)

        token = TRACE_ID.set(trace_id)
        try:
            await next_app(scope, receive, send_with_trace_header)
        finally:
            TRACE_ID.reset(token)


async def log_unhandled_exception(exc: Exception, scope: Scope) -> None:
    """Litestar ``after_exception`` hook: record 5xx causes with the request trace id.

    Client errors (4xx, including validation) are expected traffic and stay silent.
    """
    if isinstance(exc, HTTPException) and exc.status_code < HTTPStatus.INTERNAL_SERVER_ERROR:
        return
    logger.error(
        "request_failed",
        exc_info=exc,
        extra={"method": scope.get("method"), "path": scope.get("path")},
    )
