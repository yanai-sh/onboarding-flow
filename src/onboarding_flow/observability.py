"""Request trace correlation and PII-safe logging helpers."""

import logging
from typing import TYPE_CHECKING, override

from litestar.enums import ScopeType
from litestar.exceptions import HTTPException
from litestar.middleware.base import ASGIMiddleware
from litestar.types import ASGIApp, Message, Receive, Scope, Send

from onboarding_flow.logging_config import TRACE_ID
from onboarding_flow.schemas import LicensePlate, TraceId, parse_trace_id
from onboarding_flow.state import trace_id_from_state

if TYPE_CHECKING:
    from litestar import Request

TRACE_HEADER = "X-Trace-ID"

logger = logging.getLogger(__name__)


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

        encoded_trace = trace_id.encode()

        async def send_wrapper(message: Message) -> None:
            match message:
                case {"type": "http.response.start"}:
                    headers = list(message.get("headers", []))
                    if not any(header[0].lower() == b"x-trace-id" for header in headers):
                        headers.append((b"x-trace-id", encoded_trace))
                    message["headers"] = headers
                    await send(message)
                case _:
                    await send(message)

        token = TRACE_ID.set(trace_id)
        try:
            await next_app(scope, receive, send_wrapper)
        finally:
            TRACE_ID.reset(token)


async def log_unhandled_exception(exc: Exception, scope: Scope) -> None:
    """Litestar ``after_exception`` hook: record 5xx causes with the request trace id.

    Client errors (4xx, including validation) are expected traffic and stay silent.
    """
    if isinstance(exc, HTTPException) and exc.status_code < 500:
        return
    logger.error(
        "request_failed",
        exc_info=exc,
        extra={"method": scope.get("method"), "path": scope.get("path")},
    )


def trace_id_from_request(request: Request) -> TraceId:
    """Return the trace id bound by TraceMiddleware; do not mint a new id here."""
    return trace_id_from_state(request.state)


def trace_id_for_request(request: Request) -> TraceId:
    """Alias documented in ARCHITECTURE.md."""
    return trace_id_from_request(request)
