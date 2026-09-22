"""Public request/response contracts for the vehicle lookup proxy."""

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

MAX_LICENSE_PLATE_LENGTH = 32


class ErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    VEHICLE_NOT_FOUND = "VEHICLE_NOT_FOUND"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    UPSTREAM_INVALID_RESPONSE = "UPSTREAM_INVALID_RESPONSE"


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


class APIResponse[T](BaseModel):
    success: bool
    data: T | None = None
    error_code: ErrorCode | None = None
    message: str | None = None
    trace_id: str


class VehicleInfoResponse(APIResponse[VehicleData]):
    """Concrete envelope type for Litestar serialization."""


def success_response(data: VehicleData, trace_id: str) -> VehicleInfoResponse:
    return VehicleInfoResponse(
        success=True,
        data=data,
        error_code=None,
        message=None,
        trace_id=trace_id,
    )


def error_response(
    code: ErrorCode,
    message: str,
    trace_id: str,
) -> VehicleInfoResponse:
    return VehicleInfoResponse(
        success=False,
        data=None,
        error_code=code,
        message=message,
        trace_id=trace_id,
    )
