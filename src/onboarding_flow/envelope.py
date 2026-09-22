"""Response envelope for Insait: types, builders, and upstream outcome mapping."""

from enum import StrEnum

from pydantic import BaseModel

from onboarding_flow.schemas import TraceId, VehicleData
from onboarding_flow.upstream import (
    UpstreamFailure,
    UpstreamFailureKind,
    UpstreamOutcome,
    UpstreamSuccess,
)


class ErrorCode(StrEnum):
    """Stable error codes for Insait routing on HTTP 200 responses.

    INVALID_REQUEST is reserved for a future envelope-unified validation path;
    proxy ingress validation currently uses framework 4xx instead.
    """

    INVALID_REQUEST = "INVALID_REQUEST"
    VEHICLE_NOT_FOUND = "VEHICLE_NOT_FOUND"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    UPSTREAM_INVALID_RESPONSE = "UPSTREAM_INVALID_RESPONSE"


class APIResponse[T](BaseModel):
    success: bool
    data: T | None = None
    error_code: ErrorCode | None = None
    message: str | None = None
    trace_id: TraceId


class VehicleInfoResponse(APIResponse[VehicleData]):
    """Concrete envelope type for Litestar serialization."""


def success_response(data: VehicleData, trace_id: TraceId) -> VehicleInfoResponse:
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
    trace_id: TraceId,
) -> VehicleInfoResponse:
    return VehicleInfoResponse(
        success=False,
        data=None,
        error_code=code,
        message=message,
        trace_id=trace_id,
    )


_FAILURE_MESSAGES: dict[UpstreamFailureKind, str] = {
    UpstreamFailureKind.NOT_FOUND: "Vehicle not found.",
    UpstreamFailureKind.TIMEOUT: "Vehicle lookup timed out. Please try again.",
    UpstreamFailureKind.UNAVAILABLE: "Vehicle lookup is temporarily unavailable.",
    UpstreamFailureKind.INVALID_RESPONSE: "Vehicle lookup returned an invalid response.",
}

_FAILURE_TO_ERROR: dict[UpstreamFailureKind, ErrorCode] = {
    UpstreamFailureKind.NOT_FOUND: ErrorCode.VEHICLE_NOT_FOUND,
    UpstreamFailureKind.TIMEOUT: ErrorCode.UPSTREAM_TIMEOUT,
    UpstreamFailureKind.UNAVAILABLE: ErrorCode.UPSTREAM_UNAVAILABLE,
    UpstreamFailureKind.INVALID_RESPONSE: ErrorCode.UPSTREAM_INVALID_RESPONSE,
}


def vehicle_info_response(outcome: UpstreamOutcome, trace_id: TraceId) -> VehicleInfoResponse:
    match outcome:
        case UpstreamSuccess(vehicle=vehicle):
            return success_response(vehicle, trace_id)
        case UpstreamFailure(kind=kind):
            return error_response(
                _FAILURE_TO_ERROR[kind],
                _FAILURE_MESSAGES[kind],
                trace_id,
            )
