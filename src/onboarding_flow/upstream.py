"""Upstream vehicle lookup port and adapter outcome types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from onboarding_flow.schemas import VehicleData


class UpstreamFailureKind(StrEnum):
    NOT_FOUND = "not_found"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    INVALID_RESPONSE = "invalid_response"


@dataclass(frozen=True, slots=True)
class UpstreamSuccess:
    vehicle: VehicleData


@dataclass(frozen=True, slots=True)
class UpstreamFailure:
    kind: UpstreamFailureKind


type UpstreamOutcome = UpstreamSuccess | UpstreamFailure


class UpstreamAdapter(ABC):
    @abstractmethod
    async def fetch_vehicle(self, license_plate: str) -> UpstreamOutcome: ...


class UpstreamPort(Protocol):
    async def fetch_vehicle(self, license_plate: str) -> UpstreamOutcome: ...
