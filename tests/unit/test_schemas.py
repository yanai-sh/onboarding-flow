import pytest
from pydantic import ValidationError

from onboarding_flow.schemas import VehicleRequest


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
