"""JSON logging on stdout for Cloud Run with request-scoped trace ids."""

import json
import logging
import logging.config
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

TRACE_ID: ContextVar[str | None] = ContextVar("trace_id", default=None)

# Attributes every LogRecord carries; anything else came from ``extra``.
_STANDARD_ATTRS = frozenset(
    {*vars(logging.LogRecord("", logging.INFO, "", 0, "", None, None)), "message", "asctime"}
)


class TraceIdFilter(logging.Filter):
    """Attach the current request's trace id unless the record set one explicitly."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
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
            },
            "root": {"handlers": ["stdout"], "level": level},
        }
    )
