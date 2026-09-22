import pytest

from onboarding_flow.envelope import (
    ErrorCode,
    error_response,
    success_response,
    vehicle_info_response,
)
from onboarding_flow.schemas import VehicleData
from onboarding_flow.upstream import UpstreamFailure, UpstreamFailureKind, UpstreamSuccess
from tests.shared import ASSIGNMENT_SAMPLE_VEHICLE


def test_success_envelope_shape() -> None:
    data = VehicleData(
        license_plate="12345678",
        manufacturer="Toyota",
        model="Corolla",
        year=2020,
        color="White",
    )
    envelope = success_response(data, trace_id="trace-1")
    assert envelope.success is True
    assert envelope.data == data
    assert envelope.error_code is None
    assert envelope.message is None
    assert envelope.trace_id == "trace-1"


def test_error_envelope_shape() -> None:
    envelope = error_response(
        ErrorCode.VEHICLE_NOT_FOUND,
        "Vehicle not found.",
        trace_id="trace-2",
    )
    assert envelope.success is False
    assert envelope.data is None
    assert envelope.error_code == ErrorCode.VEHICLE_NOT_FOUND
    assert envelope.message == "Vehicle not found."
    assert envelope.trace_id == "trace-2"


def test_api_response_serializes_error_code_as_string() -> None:
    envelope = error_response(
        ErrorCode.UPSTREAM_TIMEOUT,
        "Timed out.",
        trace_id="t",
    )
    payload = envelope.model_dump(mode="json")
    assert payload["error_code"] == "UPSTREAM_TIMEOUT"


def test_all_error_codes_exist() -> None:
    expected = {
        "INVALID_REQUEST",
        "VEHICLE_NOT_FOUND",
        "UPSTREAM_TIMEOUT",
        "UPSTREAM_UNAVAILABLE",
        "UPSTREAM_INVALID_RESPONSE",
    }
    assert {code.value for code in ErrorCode} == expected


@pytest.mark.parametrize(
    ("kind", "expected_code"),
    [
        (UpstreamFailureKind.NOT_FOUND, ErrorCode.VEHICLE_NOT_FOUND),
        (UpstreamFailureKind.TIMEOUT, ErrorCode.UPSTREAM_TIMEOUT),
        (UpstreamFailureKind.UNAVAILABLE, ErrorCode.UPSTREAM_UNAVAILABLE),
        (UpstreamFailureKind.INVALID_RESPONSE, ErrorCode.UPSTREAM_INVALID_RESPONSE),
    ],
)
def test_envelope_maps_upstream_failures(
    kind: UpstreamFailureKind,
    expected_code: ErrorCode,
) -> None:
    response = vehicle_info_response(UpstreamFailure(kind=kind), trace_id="trace-1")
    assert response.success is False
    assert response.error_code == expected_code
    assert response.message
    assert response.trace_id == "trace-1"


def test_envelope_maps_upstream_success() -> None:
    response = vehicle_info_response(
        UpstreamSuccess(vehicle=ASSIGNMENT_SAMPLE_VEHICLE),
        trace_id="trace-2",
    )
    assert response.success is True
    assert response.data == ASSIGNMENT_SAMPLE_VEHICLE
    assert response.trace_id == "trace-2"
