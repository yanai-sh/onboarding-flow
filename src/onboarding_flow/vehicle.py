"""HTTP surface for vehicle lookup."""

import structlog
from litestar import Controller, Request, post
from litestar.status_codes import HTTP_200_OK

from onboarding_flow.envelope import (
    VehicleInfoResponse,
    error_response,
    success_response,
)
from onboarding_flow.lookup import LookupFailure, LookupSuccess, VehicleLookup
from onboarding_flow.observability import mask_plate, trace_id_from_request
from onboarding_flow.schemas import VehicleRequest

logger = structlog.get_logger()


class VehicleController(Controller):
    path = "/"

    @post(
        "/vehicle-info",
        status_code=HTTP_200_OK,
        tags=["Vehicle"],
        summary="Look up vehicle by license plate",
        description=(
            "Proxies the Encore vehicle registry. Expected upstream failures "
            "return HTTP 200 with success=false and a stable error_code for "
            "Insait routing."
        ),
    )
    async def vehicle_info(
        self,
        data: VehicleRequest,
        request: Request,
    ) -> VehicleInfoResponse:
        lookup: VehicleLookup = request.app.state.lookup
        trace_id = trace_id_from_request(request)
        result = await lookup.lookup(data.license_plate)

        match result:
            case LookupSuccess(data=vehicle):
                logger.info(
                    "vehicle_lookup_completed",
                    success=True,
                    plate_mask=mask_plate(data.license_plate),
                )
                return success_response(vehicle, trace_id)
            case LookupFailure(error_code=error_code, message=message):
                logger.info(
                    "vehicle_lookup_completed",
                    success=False,
                    error_code=error_code.value,
                    plate_mask=mask_plate(data.license_plate),
                )
                return error_response(error_code, message, trace_id)
