"""Shared pytest fixtures."""

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from litestar.testing import TestClient

from onboarding_flow.app import create_app
from onboarding_flow.config import get_settings
from onboarding_flow.observability import JsonFormatter, TraceIdFilter
from onboarding_flow.upstream import UpstreamPort
from tests.shared import OpenClient


class _JsonLineHandler(logging.Handler):
    """Collects the exact JSON lines production would write to stdout."""

    def __init__(self, lines: list[dict[str, Any]]) -> None:
        super().__init__()
        self._lines = lines

    def emit(self, record: logging.LogRecord) -> None:
        self._lines.append(json.loads(self.format(record)))


@pytest.fixture
def json_logs() -> Iterator[list[dict[str, Any]]]:
    """Parsed JSON log lines emitted during the test via the production filter and formatter."""
    lines: list[dict[str, Any]] = []
    handler = _JsonLineHandler(lines)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(TraceIdFilter())
    root = logging.getLogger()
    previous_level = root.level
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    try:
        yield lines
    finally:
        root.removeHandler(handler)
        root.setLevel(previous_level)


@pytest.fixture(autouse=True)
def _reset_settings_cache_between_tests() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def open_client() -> OpenClient:
    """Open a ``TestClient`` for an app wired to the given upstream port."""

    @contextmanager
    def _open(upstream: UpstreamPort) -> Iterator[TestClient]:
        app = create_app(upstream=upstream)
        with TestClient(app=app, raise_server_exceptions=False) as client:
            yield client

    return _open
