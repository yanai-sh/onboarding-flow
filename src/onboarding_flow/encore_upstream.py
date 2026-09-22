"""Production upstream adapter using httpx."""

import json
import logging
import time

import httpx
from pydantic import HttpUrl, ValidationError

from onboarding_flow.schemas import LicensePlate, VehicleData
from onboarding_flow.upstream import (
    UpstreamFailure,
    UpstreamFailureKind,
    UpstreamOutcome,
    UpstreamSuccess,
)

logger = logging.getLogger(__name__)


def _outcome_from_upstream_body(body: object) -> UpstreamOutcome:
    match body:
        case {"success": True, "data": dict() as data}:
            try:
                vehicle = VehicleData.model_validate(data)
            except ValidationError:
                return UpstreamFailure(kind=UpstreamFailureKind.INVALID_RESPONSE)
            return UpstreamSuccess(vehicle=vehicle)
        case {"success": False}:
            return UpstreamFailure(kind=UpstreamFailureKind.NOT_FOUND)
        case _:
            return UpstreamFailure(kind=UpstreamFailureKind.INVALID_RESPONSE)


def _failure(
    kind: UpstreamFailureKind,
    started: float,
    *,
    status_code: int | None = None,
    exc: Exception | None = None,
) -> UpstreamFailure:
    """Record an unexpected upstream failure; NOT_FOUND is a business outcome, not a failure."""
    logger.warning(
        "upstream_request_failed",
        extra={
            "kind": kind,
            "status_code": status_code,
            "exception": type(exc).__name__ if exc is not None else None,
            "duration_ms": round((time.perf_counter() - started) * 1000, 1),
        },
    )
    return UpstreamFailure(kind=kind)


class EncoreUpstream:
    def __init__(
        self,
        session: httpx.AsyncClient,
        url: HttpUrl | str,
        timeout_seconds: float,
    ) -> None:
        self._session = session
        self._url = str(url)
        self._timeout = timeout_seconds

    async def fetch_vehicle(self, license_plate: LicensePlate) -> UpstreamOutcome:
        started = time.perf_counter()
        try:
            response = await self._session.post(
                self._url,
                json={"license_plate": license_plate},
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            return _failure(UpstreamFailureKind.TIMEOUT, started, exc=exc)
        except httpx.TransportError as exc:
            return _failure(UpstreamFailureKind.UNAVAILABLE, started, exc=exc)

        match response.status_code:
            case 404:
                return UpstreamFailure(kind=UpstreamFailureKind.NOT_FOUND)
            case code if code >= 500:
                return _failure(UpstreamFailureKind.UNAVAILABLE, started, status_code=code)
            case 200:
                try:
                    body = response.json()
                except json.JSONDecodeError, ValueError:
                    return _failure(UpstreamFailureKind.INVALID_RESPONSE, started, status_code=200)
                outcome = _outcome_from_upstream_body(body)
                match outcome:
                    case UpstreamFailure(kind=UpstreamFailureKind.INVALID_RESPONSE):
                        return _failure(
                            UpstreamFailureKind.INVALID_RESPONSE, started, status_code=200
                        )
                    case _:
                        return outcome
            case code:
                return _failure(UpstreamFailureKind.UNAVAILABLE, started, status_code=code)
