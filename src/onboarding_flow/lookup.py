"""Vehicle lookup orchestration over the upstream port."""

from dataclasses import dataclass

from onboarding_flow.envelope import ErrorCode, vehicle_info_response
from onboarding_flow.schemas import VehicleData
from onboarding_flow.upstream import UpstreamOutcome, UpstreamPort


@dataclass(frozen=True, slots=True)
class LookupSuccess:
    success: bool
    data: VehicleData


@dataclass(frozen=True, slots=True)
class LookupFailure:
    success: bool
    error_code: ErrorCode
    message: str


type LookupResult = LookupSuccess | LookupFailure


def lookup_result_from_outcome(outcome: UpstreamOutcome) -> LookupResult:
    envelope = vehicle_info_response(outcome, trace_id="")
    if envelope.success and envelope.data is not None:
        return LookupSuccess(success=True, data=envelope.data)
    if envelope.error_code is None or envelope.message is None:
        msg = "upstream failure must map to error_code and message"
        raise ValueError(msg)
    return LookupFailure(
        success=False,
        error_code=envelope.error_code,
        message=envelope.message,
    )


class VehicleLookup:
    def __init__(self, upstream: UpstreamPort) -> None:
        self._upstream = upstream

    async def lookup(self, license_plate: str) -> LookupResult:
        outcome = await self._upstream.fetch_vehicle(license_plate)
        return lookup_result_from_outcome(outcome)
