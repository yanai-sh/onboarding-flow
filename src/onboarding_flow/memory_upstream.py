"""In-memory upstream adapter for tests."""

from onboarding_flow.schemas import LicensePlate, VehicleData
from onboarding_flow.upstream import (
    UpstreamFailure,
    UpstreamFailureKind,
    UpstreamOutcome,
    UpstreamSuccess,
)


class MemoryUpstream:
    """Returns a configured outcome or raises a configured exception."""

    def __init__(
        self,
        *,
        outcome: UpstreamOutcome | None = None,
        exc: BaseException | None = None,
    ) -> None:
        self._outcome = outcome
        self._exc = exc
        self.call_count = 0
        self.last_plate: LicensePlate | None = None

    async def fetch_vehicle(self, license_plate: LicensePlate) -> UpstreamOutcome:
        self.call_count += 1
        self.last_plate = license_plate
        if self._exc is not None:
            raise self._exc
        if self._outcome is None:
            msg = "MemoryUpstream outcome not configured"
            raise RuntimeError(msg)
        return self._outcome


def success_upstream(vehicle: VehicleData) -> MemoryUpstream:
    return MemoryUpstream(outcome=UpstreamSuccess(vehicle=vehicle))


def failure_upstream(kind: UpstreamFailureKind) -> MemoryUpstream:
    return MemoryUpstream(outcome=UpstreamFailure(kind=kind))
