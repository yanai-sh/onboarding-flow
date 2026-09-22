"""Typed accessors for Litestar application and connection state bags."""

from typing import Protocol, cast

from onboarding_flow.schemas import TraceId
from onboarding_flow.upstream import UpstreamPort


class AppStateAttributes(Protocol):
    upstream: UpstreamPort


class RequestStateAttributes(Protocol):
    trace_id: TraceId


def upstream_from_app(state: object) -> UpstreamPort:
    """Return the configured upstream port from application state."""
    return cast(AppStateAttributes, state).upstream


def trace_id_from_state(state: object) -> TraceId:
    """Return the trace id bound on connection state, or raise if missing."""
    trace_id = getattr(state, "trace_id", None)
    if not trace_id:
        msg = "trace_id missing; TraceMiddleware must run before handlers"
        raise RuntimeError(msg)
    return cast(TraceId, trace_id)
