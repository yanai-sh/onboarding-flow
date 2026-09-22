"""HTTP surface for vehicle lookup."""

from litestar import Controller, Request, post
from litestar.status_codes import HTTP_200_OK

from onboarding_flow.envelope import VehicleInfoResponse
from onboarding_flow.observability import trace_id_for_request
from onboarding_flow.schemas import VehicleRequest
from onboarding_flow.upstream import UpstreamPort
from onboarding_flow.vehicle_lookup import lookup_vehicle_info


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
        upstream: UpstreamPort = request.app.state.upstream
        trace_id = trace_id_for_request(request)
        return await lookup_vehicle_info(data.license_plate, upstream, trace_id)
