import pytest
from pydantic import ValidationError

from onboarding_flow.schemas import (
    ErrorCode,
    VehicleData,
    VehicleRequest,
    error_response,
    success_response,
)


def test_vehicle_request_normalizes_plate() -> None:
    req = VehicleRequest(license_plate="  ab12cd34  ")
    assert req.license_plate == "AB12CD34"


@pytest.mark.parametrize(
    "plate",
    ["", "   ", "ab-cd", "plate with spaces", "a" * 33],
)
def test_vehicle_request_rejects_invalid_plates(plate: str) -> None:
    with pytest.raises(ValidationError):
        VehicleRequest(license_plate=plate)


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
