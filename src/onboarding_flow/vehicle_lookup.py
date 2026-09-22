"""Vehicle lookup orchestration: upstream fetch, envelope mapping, completion logging."""

import structlog

from onboarding_flow.envelope import VehicleInfoResponse, vehicle_info_response
from onboarding_flow.observability import mask_plate
from onboarding_flow.upstream import UpstreamPort

logger = structlog.get_logger()


async def lookup_vehicle_info(
    license_plate: str,
    upstream: UpstreamPort,
    trace_id: str,
) -> VehicleInfoResponse:
    outcome = await upstream.fetch_vehicle(license_plate)
    response = vehicle_info_response(outcome, trace_id)

    logger.info(
        "vehicle_lookup_completed",
        success=response.success,
        error_code=response.error_code.value if response.error_code else None,
        plate_mask=mask_plate(license_plate),
    )
    return response
