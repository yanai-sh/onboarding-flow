from types import SimpleNamespace

import pytest

from onboarding_flow.memory_upstream import success_upstream
from onboarding_flow.state import trace_id_from_state, upstream_from_app
from tests.shared import ASSIGNMENT_SAMPLE_VEHICLE


def test_upstream_from_app_reads_configured_port() -> None:
    upstream = success_upstream(ASSIGNMENT_SAMPLE_VEHICLE)
    state = SimpleNamespace(upstream=upstream)
    assert upstream_from_app(state) is upstream


def test_trace_id_from_state_requires_bound_value() -> None:
    with pytest.raises(RuntimeError, match="TraceMiddleware"):
        trace_id_from_state(SimpleNamespace())


def test_trace_id_from_state_returns_bound_value() -> None:
    assert trace_id_from_state(SimpleNamespace(trace_id="bound-trace")) == "bound-trace"
