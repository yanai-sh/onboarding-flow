import pytest
from litestar.testing import TestClient

from onboarding_flow.app import create_app
from onboarding_flow.memory_upstream import failure_upstream, success_upstream
from onboarding_flow.schemas import VehicleData
from onboarding_flow.upstream import UpstreamFailureKind

SAMPLE_VEHICLE = VehicleData(
    license_plate="12345678",
    manufacturer="Toyota",
    model="Corolla",
    year=2020,
    color="White",
)


def test_vehicle_info_happy_path() -> None:
    upstream = success_upstream(SAMPLE_VEHICLE)
    with TestClient(app=create_app(upstream=upstream)) as client:
        response = client.post("/vehicle-info", json={"license_plate": "12345678"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["manufacturer"] == "Toyota"
    assert body["trace_id"]
    assert upstream.call_count == 1


def test_vehicle_info_not_found() -> None:
    upstream = failure_upstream(UpstreamFailureKind.NOT_FOUND)
    with TestClient(app=create_app(upstream=upstream)) as client:
        response = client.post("/vehicle-info", json={"license_plate": "12345678"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "VEHICLE_NOT_FOUND"


@pytest.mark.parametrize(
    ("kind", "code"),
    [
        (UpstreamFailureKind.TIMEOUT, "UPSTREAM_TIMEOUT"),
        (UpstreamFailureKind.UNAVAILABLE, "UPSTREAM_UNAVAILABLE"),
        (UpstreamFailureKind.INVALID_RESPONSE, "UPSTREAM_INVALID_RESPONSE"),
    ],
)
def test_vehicle_info_upstream_failures(kind: UpstreamFailureKind, code: str) -> None:
    upstream = failure_upstream(kind)
    with TestClient(app=create_app(upstream=upstream)) as client:
        response = client.post("/vehicle-info", json={"license_plate": "12345678"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == code


def test_vehicle_info_invalid_plate_returns_422_and_skips_upstream() -> None:
    upstream = success_upstream(SAMPLE_VEHICLE)
    with TestClient(app=create_app(upstream=upstream)) as client:
        response = client.post("/vehicle-info", json={"license_plate": "bad-plate"})

    assert response.status_code in {400, 422}
    assert upstream.call_count == 0


def test_trace_id_echoed_when_provided() -> None:
    upstream = success_upstream(SAMPLE_VEHICLE)
    with TestClient(app=create_app(upstream=upstream)) as client:
        response = client.post(
            "/vehicle-info",
            json={"license_plate": "12345678"},
            headers={"X-Trace-ID": "client-trace-99"},
        )

    assert response.status_code == 200
    assert response.headers.get("x-trace-id") == "client-trace-99"
    assert response.json()["trace_id"] == "client-trace-99"


def test_trace_id_generated_when_missing() -> None:
    upstream = success_upstream(SAMPLE_VEHICLE)
    with TestClient(app=create_app(upstream=upstream)) as client:
        response = client.post("/vehicle-info", json={"license_plate": "12345678"})

    trace = response.json()["trace_id"]
    assert trace
    assert response.headers.get("x-trace-id") == trace
