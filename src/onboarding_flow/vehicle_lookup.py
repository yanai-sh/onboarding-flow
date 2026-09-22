"""Vehicle lookup orchestration: upstream fetch, envelope mapping, completion logging."""

import logging
import time

from onboarding_flow.envelope import VehicleInfoResponse, vehicle_info_response
from onboarding_flow.observability import elapsed_ms, mask_plate
from onboarding_flow.schemas import LicensePlate, TraceId
from onboarding_flow.upstream import UpstreamPort

logger = logging.getLogger(__name__)


async def lookup_vehicle_info(
    license_plate: LicensePlate,
    upstream: UpstreamPort,
    trace_id: TraceId,
) -> VehicleInfoResponse:
    started = time.perf_counter()
    outcome = await upstream.fetch_vehicle(license_plate)
    duration_ms = elapsed_ms(started)
    response = vehicle_info_response(outcome, trace_id)

    logger.info(
        "vehicle_lookup_completed",
        extra={
            "trace_id": trace_id,
            "success": response.success,
            "error_code": response.error_code,
            "plate_mask": mask_plate(license_plate),
            "duration_ms": duration_ms,
        },
    )
    return response
