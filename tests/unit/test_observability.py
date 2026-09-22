from litestar import Litestar, Request, get
from litestar.testing import TestClient

from onboarding_flow.observability import TraceMiddleware, mask_plate, trace_id_for_request


def test_mask_plate_hides_prefix() -> None:
    assert mask_plate("12345678") == "****5678"


def test_mask_plate_short_values() -> None:
    assert mask_plate("AB") == "****"


@get("/trace")
async def trace_probe(request: Request) -> dict[str, str]:
    return {"trace_id": trace_id_for_request(request)}


def test_trace_middleware_echoes_provided_header() -> None:
    app = Litestar(route_handlers=[trace_probe], middleware=[TraceMiddleware()])
    with TestClient(app=app) as client:
        response = client.get("/trace", headers={"X-Trace-ID": "client-trace-42"})

    assert response.status_code == 200
    assert response.json()["trace_id"] == "client-trace-42"
    assert response.headers.get("x-trace-id") == "client-trace-42"


def test_trace_middleware_generates_id_when_header_missing() -> None:
    app = Litestar(route_handlers=[trace_probe], middleware=[TraceMiddleware()])
    with TestClient(app=app) as client:
        response = client.get("/trace")

    assert response.status_code == 200
    trace = response.json()["trace_id"]
    assert trace
    assert response.headers.get("x-trace-id") == trace
