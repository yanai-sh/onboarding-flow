"""Production upstream adapter using httpx."""

import json
import logging
import time

import httpx
from pydantic import HttpUrl, ValidationError

from onboarding_flow.observability import elapsed_ms
from onboarding_flow.schemas import LicensePlate, VehicleData
from onboarding_flow.upstream import (
    UpstreamFailure,
    UpstreamFailureKind,
    UpstreamOutcome,
    UpstreamSuccess,
)

logger = logging.getLogger(__name__)


def _log_failure(
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
            "duration_ms": elapsed_ms(started),
        },
    )
    return UpstreamFailure(kind=kind)


def _outcome_from_upstream_body(body: object, started: float) -> UpstreamOutcome:
    match body:
        case {"success": True, "data": dict() as data}:
            try:
                vehicle = VehicleData.model_validate(data)
            except ValidationError:
                return _log_failure(UpstreamFailureKind.INVALID_RESPONSE, started, status_code=200)
            return UpstreamSuccess(vehicle=vehicle)
        case {"success": False}:
            return UpstreamFailure(kind=UpstreamFailureKind.NOT_FOUND)
        case _:
            return _log_failure(UpstreamFailureKind.INVALID_RESPONSE, started, status_code=200)


class EncoreUpstream:
    def __init__(
        self,
        client: httpx.AsyncClient,
        url: HttpUrl | str,
        timeout_seconds: float,
    ) -> None:
        self._client = client
        self._url = str(url)
        self._timeout = timeout_seconds

    async def fetch_vehicle(self, license_plate: LicensePlate) -> UpstreamOutcome:
        started = time.perf_counter()
        try:
            response = await self._client.post(
                self._url,
                json={"license_plate": license_plate},
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            return _log_failure(UpstreamFailureKind.TIMEOUT, started, exc=exc)
        except httpx.RequestError as exc:
            # Transport, decoding, redirect, and other request-level faults.
            return _log_failure(UpstreamFailureKind.UNAVAILABLE, started, exc=exc)

        match response.status_code:
            case 404:
                return UpstreamFailure(kind=UpstreamFailureKind.NOT_FOUND)
            case code if code >= 500:
                return _log_failure(UpstreamFailureKind.UNAVAILABLE, started, status_code=code)
            case 200:
                try:
                    body = response.json()
                except json.JSONDecodeError, ValueError:
                    return _log_failure(
                        UpstreamFailureKind.INVALID_RESPONSE, started, status_code=200
                    )
                return _outcome_from_upstream_body(body, started)
            case code:
                return _log_failure(UpstreamFailureKind.UNAVAILABLE, started, status_code=code)
