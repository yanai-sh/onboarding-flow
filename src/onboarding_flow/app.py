"""ASGI application assembly for the onboarding flow service."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from litestar import Litestar, get
from litestar.openapi.config import OpenAPIConfig

from onboarding_flow.config import get_settings
from onboarding_flow.encore_upstream import EncoreUpstream
from onboarding_flow.logging_config import configure_logging
from onboarding_flow.observability import TraceMiddleware, log_unhandled_exception
from onboarding_flow.upstream import UpstreamPort
from onboarding_flow.vehicle import VehicleController

OPENAPI_CONFIG = OpenAPIConfig(
    title="Onboarding Flow Vehicle Proxy",
    version="0.1.0",
    description=(
        "Resilient proxy for the Encore vehicle-info endpoint. "
        "OpenAPI documents the Insait integration contract."
    ),
    path="/schema",
)

logger = logging.getLogger(__name__)


@get("/health", tags=["Health"], summary="Liveness probe")
async def health() -> dict[str, str]:
    """Return the service liveness status."""
    return {"status": "ok"}


def create_app(*, upstream: UpstreamPort | None = None) -> Litestar:
    """Return the configured application for tests and ASGI servers."""
    configure_logging(get_settings().log_level)
    injected_upstream = upstream

    @asynccontextmanager
    async def lifespan(app: Litestar) -> AsyncGenerator[None]:
        client: httpx.AsyncClient | None = None
        upstream_details: dict[str, object] = {}
        if injected_upstream is not None:
            upstream_port: UpstreamPort = injected_upstream
        else:
            settings = get_settings()
            client = httpx.AsyncClient()
            upstream_port = EncoreUpstream(
                client,
                settings.upstream_url,
                settings.upstream_timeout_seconds,
            )
            upstream_details = {
                "upstream_host": settings.upstream_url.host,
                "upstream_timeout_seconds": settings.upstream_timeout_seconds,
            }

        app.state.upstream = upstream_port
        logger.info(
            "app_started",
            extra={
                "upstream_adapter": type(upstream_port).__name__,
                "version": OPENAPI_CONFIG.version,
                **upstream_details,
            },
        )
        try:
            yield
        finally:
            logger.info("app_stopping")
            if client is not None:
                await client.aclose()

    return Litestar(
        route_handlers=[health, VehicleController],
        lifespan=[lifespan],
        middleware=[TraceMiddleware()],
        openapi_config=OPENAPI_CONFIG,
        # Litestar's default LoggingConfig would install its own handlers;
        # unhandled exceptions are logged through our JSON pipeline instead.
        logging_config=None,
        after_exception=[log_unhandled_exception],
    )


app = create_app()
