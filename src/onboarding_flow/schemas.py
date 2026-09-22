"""Inbound request and shared vehicle record types for the vehicle lookup proxy."""

from pydantic import BaseModel, Field, field_validator

MAX_LICENSE_PLATE_LENGTH = 32


class VehicleData(BaseModel):
    license_plate: str
    manufacturer: str
    model: str
    year: int
    color: str


class VehicleRequest(BaseModel):
    license_plate: str = Field(..., min_length=1)

    @field_validator("license_plate", mode="before")
    @classmethod
    def strip_whitespace(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("license_plate")
    @classmethod
    def validate_license_plate(cls, value: str) -> str:
        normalized = value.upper()
        if not normalized:
            msg = "license plate is required"
            raise ValueError(msg)
        if len(normalized) > MAX_LICENSE_PLATE_LENGTH:
            msg = f"license plate must be at most {MAX_LICENSE_PLATE_LENGTH} characters"
            raise ValueError(msg)
        if not normalized.isascii() or not normalized.isalnum():
            msg = "license plate must be ASCII alphanumeric"
            raise ValueError(msg)
        return normalized
