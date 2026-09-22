"""ASGI application assembly for the onboarding flow service."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from litestar import Litestar, get
from litestar.openapi.config import OpenAPIConfig

from onboarding_flow.config import get_settings
from onboarding_flow.encore_upstream import EncoreUpstream
from onboarding_flow.logging_config import configure_logging
from onboarding_flow.observability import TraceMiddleware
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


@get("/health", tags=["Health"], summary="Liveness probe")
async def health() -> dict[str, str]:
    """Return the service liveness status."""
    return {"status": "ok"}


def create_app(*, upstream: UpstreamPort | None = None) -> Litestar:
    """Return the configured application for tests and ASGI servers."""
    configure_logging()
    injected_upstream = upstream

    @asynccontextmanager
    async def lifespan(app: Litestar) -> AsyncGenerator[None]:
        if injected_upstream is not None:
            app.state.upstream = injected_upstream
            yield
            return

        settings = get_settings()
        session = httpx.AsyncClient()
        try:
            app.state.upstream = EncoreUpstream(
                session,
                settings.upstream_url,
                settings.upstream_timeout_seconds,
            )
            yield
        finally:
            await session.aclose()

    return Litestar(
        route_handlers=[health, VehicleController],
        lifespan=[lifespan],
        middleware=[TraceMiddleware()],
        openapi_config=OPENAPI_CONFIG,
    )


app = create_app()
