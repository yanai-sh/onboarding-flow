"""JSON logging on stdout for Cloud Run."""

import json
import logging
import logging.config
from typing import Any

_CONFIGURED = False

_LOG_RECORD_FIELDS = frozenset(
    {
        "trace_id",
        "success",
        "error_code",
        "plate_mask",
    }
)


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        for key in _LOG_RECORD_FIELDS:
            if hasattr(record, key):
                value = getattr(record, key)
                if value is not None:
                    payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure application logging once (safe to call from tests)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = logging.INFO
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                },
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "handlers": ["stdout"],
                "level": level,
            },
        }
    )
    _CONFIGURED = True
