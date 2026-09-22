"""Wire types for the vehicle lookup proxy and the shared license plate rule."""

import re
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

# Structural bound on the raw request string; longer input is a client bug, not a typo.
MAX_LICENSE_PLATE_INPUT_LENGTH = 32
VEHICLE_YEAR_MIN = 1900
VEHICLE_YEAR_MAX = 2100

# The upstream accepts Israeli plates only: 7 or 8 ASCII digits. People write them
# as 12-345-67 or 123.45.678, so separators are removed before the rule applies.
_PLATE_SEPARATORS = re.compile(r"[ .-]")
_PLATE_DIGITS = re.compile(r"[0-9]{7,8}")


def normalize_license_plate(value: str) -> str:
    """Return the digits-only plate sent upstream, or raise if it breaks the plate rule."""
    plate = _PLATE_SEPARATORS.sub("", value.strip())
    if not _PLATE_DIGITS.fullmatch(plate):
        msg = "license plate must be 7 or 8 digits"
        raise ValueError(msg)
    return plate


LicensePlate = Annotated[str, AfterValidator(normalize_license_plate)]
VehicleText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]


class ErrorCode(StrEnum):
    """Stable codes for Insait routing on HTTP 200 responses (ADR 0003)."""

    INVALID_REQUEST = "INVALID_REQUEST"
    VEHICLE_NOT_FOUND = "VEHICLE_NOT_FOUND"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    UPSTREAM_INVALID_RESPONSE = "UPSTREAM_INVALID_RESPONSE"


class VehicleRequest(BaseModel):
    # Only structural checks here: a plate that breaks the plate rule is a lookup
    # outcome returned in the envelope, not a framework 4xx (ADR 0003).
    license_plate: str = Field(max_length=MAX_LICENSE_PLATE_INPUT_LENGTH)


class VehicleData(BaseModel):
    license_plate: LicensePlate
    manufacturer: VehicleText
    model: VehicleText
    year: int = Field(ge=VEHICLE_YEAR_MIN, le=VEHICLE_YEAR_MAX)
    color: VehicleText


class VehicleInfoResponse(BaseModel):
    success: bool
    data: VehicleData | None = None
    error_code: ErrorCode | None = None
    message: str | None = None
    trace_id: str
