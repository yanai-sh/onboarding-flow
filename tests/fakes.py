"""Test doubles for the upstream port."""

from onboarding_flow.upstream import UpstreamOutcome


class MemoryUpstream:
    """Returns (or raises) a fixed outcome and records every plate it was asked for."""

    def __init__(self, outcome: UpstreamOutcome | Exception) -> None:
        self._outcome = outcome
        self.plates: list[str] = []

    async def fetch_vehicle(self, license_plate: str) -> UpstreamOutcome:
        self.plates.append(license_plate)
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome
