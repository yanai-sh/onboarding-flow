from collections.abc import Callable
from contextlib import AbstractContextManager

from litestar.testing import TestClient

from onboarding_flow.envelope import ErrorCode
from onboarding_flow.memory_upstream import MemoryUpstream, failure_upstream
from onboarding_flow.schemas import VehicleData
from onboarding_flow.upstream import UpstreamFailureKind, UpstreamPort


def test_health_endpoint(api_client: TestClient) -> None:
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_vehicle_info_happy_path_matches_assignment_shape(
    api_client: TestClient,
    assignment_plate: str,
    assignment_vehicle: VehicleData,
    success_memory_upstream: MemoryUpstream,
) -> None:
    response = api_client.post("/vehicle-info", json={"license_plate": assignment_plate})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == assignment_vehicle.model_dump(mode="json")
    assert body["trace_id"]
    assert success_memory_upstream.call_count == 1


def test_vehicle_info_upstream_failure_returns_envelope_smoke(
    open_api_client: Callable[[UpstreamPort], AbstractContextManager[TestClient]],
    assignment_plate: str,
) -> None:
    upstream = failure_upstream(UpstreamFailureKind.NOT_FOUND)
    with open_api_client(upstream) as client:
        response = client.post("/vehicle-info", json={"license_plate": assignment_plate})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == ErrorCode.VEHICLE_NOT_FOUND.value


def test_vehicle_info_invalid_plate_returns_client_error_and_skips_upstream(
    open_api_client: Callable[[UpstreamPort], AbstractContextManager[TestClient]],
    success_memory_upstream: MemoryUpstream,
) -> None:
    # Litestar may respond with 400 or 422 for validation failures.
    with open_api_client(success_memory_upstream) as client:
        response = client.post("/vehicle-info", json={"license_plate": "bad-plate"})

    assert response.status_code in {400, 422}
    assert success_memory_upstream.call_count == 0


def test_trace_id_echoed_when_provided(
    api_client: TestClient,
    assignment_plate: str,
) -> None:
    response = api_client.post(
        "/vehicle-info",
        json={"license_plate": assignment_plate},
        headers={"X-Trace-ID": "client-trace-99"},
    )

    assert response.status_code == 200
    assert response.headers.get("x-trace-id") == "client-trace-99"
    assert response.json()["trace_id"] == "client-trace-99"


def test_trace_id_generated_when_missing(
    api_client: TestClient,
    assignment_plate: str,
) -> None:
    response = api_client.post("/vehicle-info", json={"license_plate": assignment_plate})

    trace = response.json()["trace_id"]
    assert trace
    assert response.headers.get("x-trace-id") == trace
