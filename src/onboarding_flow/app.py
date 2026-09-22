"""ASGI application assembly for the onboarding flow service."""

from litestar import Litestar, get


@get("/health")
async def health() -> dict[str, str]:
    """Return the service liveness status."""
    return {"status": "ok"}


def create_app() -> Litestar:
    """Return the configured application for tests and ASGI servers."""
    return Litestar(route_handlers=[health])


app = create_app()
