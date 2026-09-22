"""Vehicle lookup orchestration over the upstream port."""

from dataclasses import dataclass

from onboarding_flow.schemas import ErrorCode, VehicleData
from onboarding_flow.upstream import (
    UpstreamFailure,
    UpstreamFailureKind,
    UpstreamOutcome,
    UpstreamPort,
    UpstreamSuccess,
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
    match outcome:
        case UpstreamSuccess(vehicle=vehicle):
            return LookupSuccess(success=True, data=vehicle)
        case UpstreamFailure(kind=kind):
            return LookupFailure(
                success=False,
                error_code=_FAILURE_TO_ERROR[kind],
                message=_FAILURE_MESSAGES[kind],
            )


class VehicleLookup:
    def __init__(self, upstream: UpstreamPort) -> None:
        self._upstream = upstream

    async def lookup(self, license_plate: str) -> LookupResult:
        outcome = await self._upstream.fetch_vehicle(license_plate)
        return lookup_result_from_outcome(outcome)
