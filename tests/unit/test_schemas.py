import pytest
from pydantic import ValidationError

from onboarding_flow.schemas import VehicleData, VehicleRequest


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


def test_vehicle_data_rejects_invalid_plate() -> None:
    with pytest.raises(ValidationError):
        VehicleData(
            license_plate="bad-plate",
            manufacturer="Toyota",
            model="Corolla",
            year=2020,
            color="White",
        )


def test_vehicle_data_rejects_invalid_year() -> None:
    with pytest.raises(ValidationError):
        VehicleData(
            license_plate="12345678",
            manufacturer="Toyota",
            model="Corolla",
            year=0,
            color="White",
        )


def test_vehicle_data_rejects_empty_manufacturer() -> None:
    with pytest.raises(ValidationError):
        VehicleData(
            license_plate="12345678",
            manufacturer="   ",
            model="Corolla",
            year=2020,
            color="White",
        )


def test_vehicle_data_normalizes_plate_and_trims_text_fields() -> None:
    data = VehicleData(
        license_plate="  ab12cd34  ",
        manufacturer="  Toyota  ",
        model="Corolla",
        year=2020,
        color="White",
    )
    assert data.license_plate == "AB12CD34"
    assert data.manufacturer == "Toyota"
