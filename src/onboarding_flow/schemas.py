"""Inbound request and shared vehicle record types for the vehicle lookup proxy."""

import uuid
from typing import Annotated

from pydantic import AfterValidator, BaseModel, BeforeValidator, Field, TypeAdapter, ValidationError

MAX_LICENSE_PLATE_LENGTH = 32
VEHICLE_YEAR_MIN = 1900
VEHICLE_YEAR_MAX = 2100
VEHICLE_TEXT_MAX_LENGTH = 128


def _strip_if_str(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


def normalize_license_plate(value: str) -> str:
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


LicensePlate = Annotated[
    str,
    BeforeValidator(_strip_if_str),
    AfterValidator(normalize_license_plate),
]

TraceId = Annotated[
    str,
    Field(min_length=1, max_length=128, pattern=r"[\x21-\x7E]+"),
]

_trace_id_adapter = TypeAdapter(TraceId)


def _new_trace_id() -> TraceId:
    return _trace_id_adapter.validate_python(str(uuid.uuid7()))


def parse_trace_id(header_value: str | None) -> TraceId:
    """Resolve trace id from X-Trace-ID; invalid client values are replaced with a new UUID."""
    if not header_value or not header_value.strip():
        return _new_trace_id()
    stripped = header_value.strip()
    try:
        return _trace_id_adapter.validate_python(stripped)
    except ValidationError:
        return _new_trace_id()


def _strip_vehicle_text(value: str) -> str:
    return value.strip()


NonEmptyVehicleText = Annotated[
    str,
    BeforeValidator(_strip_if_str),
    AfterValidator(_strip_vehicle_text),
    Field(min_length=1, max_length=VEHICLE_TEXT_MAX_LENGTH),
]


class VehicleData(BaseModel):
    license_plate: LicensePlate
    manufacturer: NonEmptyVehicleText
    model: NonEmptyVehicleText
    year: int = Field(ge=VEHICLE_YEAR_MIN, le=VEHICLE_YEAR_MAX)
    color: NonEmptyVehicleText


class VehicleRequest(BaseModel):
    license_plate: LicensePlate
