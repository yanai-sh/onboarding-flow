"""Request trace correlation and PII-safe logging helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import structlog
from litestar.enums import ScopeType
from litestar.middleware.base import ASGIMiddleware
from litestar.types import ASGIApp, Message, Receive, Scope, Send

from onboarding_flow.schemas import LicensePlate, TraceId, parse_trace_id

if TYPE_CHECKING:
    from litestar import Request

TRACE_HEADER = "X-Trace-ID"


def mask_plate(license_plate: LicensePlate) -> str:
    """Return a deterministic partial mask; never log the full plate."""
    if len(license_plate) <= 4:
        return "****"
    return f"{'*' * (len(license_plate) - 4)}{license_plate[-4:]}"


class TraceMiddleware(ASGIMiddleware):
    scopes = (ScopeType.HTTP,)

    @override
    async def handle(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        next_app: ASGIApp,
    ) -> None:
        if scope["type"] != ScopeType.HTTP:
            await next_app(scope, receive, send)
            return

        from litestar import Request

        request = Request(scope=scope, receive=receive)
        trace_id = parse_trace_id(request.headers.get(TRACE_HEADER))
        scope.setdefault("state", {})
        scope["state"]["trace_id"] = trace_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(trace_id=trace_id)
        encoded_trace = trace_id.encode()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                start = message
                headers = list(start.get("headers", []))
                if not any(header[0].lower() == b"x-trace-id" for header in headers):
                    headers.append((b"x-trace-id", encoded_trace))
                start["headers"] = headers
                await send(start)
                return
            await send(message)

        try:
            await next_app(scope, receive, send_wrapper)
        finally:
            structlog.contextvars.clear_contextvars()


def trace_id_from_request(request: Request) -> TraceId:
    """Return the trace id bound by TraceMiddleware; do not mint a new id here."""
    trace_id = getattr(request.state, "trace_id", None)
    if not trace_id:
        msg = "trace_id missing; TraceMiddleware must run before handlers"
        raise RuntimeError(msg)
    return trace_id


def trace_id_for_request(request: Request) -> TraceId:
    """Alias documented in ARCHITECTURE.md."""
    return trace_id_from_request(request)
