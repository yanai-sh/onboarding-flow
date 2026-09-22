"""POST /vehicle-info: plate rule, upstream lookup, envelope mapping, completion log."""

import logging
import time

from litestar import Request, post
from litestar.status_codes import HTTP_200_OK

from onboarding_flow.observability import elapsed_ms, mask_plate
from onboarding_flow.schemas import (
    ErrorCode,
    VehicleData,
    VehicleInfoResponse,
    VehicleRequest,
    normalize_license_plate,
)
from onboarding_flow.upstream import UpstreamOutcome, UpstreamPort

# Spoken to the applicant by the Insait flow, so: plain words, a next step, no request data.
MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.INVALID_REQUEST: (
        "That plate number doesn't look right. Israeli plates have 7 or 8 digits."
    ),
    ErrorCode.VEHICLE_NOT_FOUND: (
        "We couldn't find a vehicle with that plate number. Please check it and try again."
    ),
    ErrorCode.UPSTREAM_TIMEOUT: (
        "The vehicle registry is taking too long to respond. Please try again in a moment."
    ),
    ErrorCode.UPSTREAM_UNAVAILABLE: (
        "The vehicle registry is unavailable right now. Please try again in a moment."
    ),
    ErrorCode.UPSTREAM_INVALID_RESPONSE: (
        "We couldn't read the vehicle details right now. Please try again in a moment."
    ),
}

logger = logging.getLogger(__name__)


def _envelope(outcome: UpstreamOutcome, trace_id: str) -> VehicleInfoResponse:
    match outcome:
        case VehicleData():
            return VehicleInfoResponse(success=True, data=outcome, trace_id=trace_id)
        case ErrorCode():
            return VehicleInfoResponse(
                success=False, error_code=outcome, message=MESSAGES[outcome], trace_id=trace_id
            )


@post(
    "/vehicle-info",
    status_code=HTTP_200_OK,
    tags=["Vehicle"],
    summary="Look up vehicle by license plate",
    description=(
        "Proxies the Encore vehicle registry. Plates are 7 or 8 digits; spaces, dashes, "
        "and dots are ignored. A plate that breaks this rule, a missing vehicle, and "
        "upstream failures all return HTTP 200 with success=false, a stable error_code "
        "for Insait routing, and a speakable message. Malformed request bodies return 400."
    ),
)
async def vehicle_info(data: VehicleRequest, request: Request) -> VehicleInfoResponse:
    started = time.perf_counter()
    plate: str | None = None
    try:
        plate = normalize_license_plate(data.license_plate)
    except ValueError:
        outcome: UpstreamOutcome = ErrorCode.INVALID_REQUEST
    else:
        upstream: UpstreamPort = request.app.state.upstream
        outcome = await upstream.fetch_vehicle(plate)

    response = _envelope(outcome, request.state.trace_id)
    logger.info(
        "vehicle_lookup_completed",
        extra={
            "success": response.success,
            "error_code": response.error_code,
            # Input that breaks the plate rule may not be a plate at all; log nothing of it.
            "plate_mask": mask_plate(plate) if plate else None,
            "duration_ms": elapsed_ms(started),
        },
    )
    return response
