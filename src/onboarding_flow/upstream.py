"""Upstream vehicle lookup port and the production httpx adapter."""

import asyncio
import logging
import time
from http import HTTPStatus
from typing import Protocol

import httpx
from pydantic import HttpUrl, ValidationError

from onboarding_flow.observability import elapsed_ms
from onboarding_flow.schemas import ErrorCode, VehicleData

# The port answers with the vehicle or the envelope code explaining why there is none.
type UpstreamOutcome = VehicleData | ErrorCode

logger = logging.getLogger(__name__)


class UpstreamPort(Protocol):
    async def fetch_vehicle(self, license_plate: str) -> UpstreamOutcome: ...


def _failed(
    error_code: ErrorCode,
    started: float,
    *,
    status_code: int | None = None,
    exc: Exception | None = None,
) -> ErrorCode:
    """Record an unexpected upstream failure; not-found is a business outcome, not a failure."""
    logger.warning(
        "upstream_request_failed",
        extra={
            "error_code": error_code,
            "status_code": status_code,
            "exception": type(exc).__name__ if exc is not None else None,
            "duration_ms": elapsed_ms(started),
        },
    )
    return error_code


def _json_or_none(response: httpx.Response) -> object:
    try:
        return response.json()
    except ValueError:
        return None


class EncoreUpstream:
    def __init__(
        self, client: httpx.AsyncClient, url: HttpUrl | str, timeout_seconds: float
    ) -> None:
        self._client = client
        self._url = str(url)
        self._timeout = timeout_seconds

    async def fetch_vehicle(self, license_plate: str) -> UpstreamOutcome:
        started = time.perf_counter()
        try:
            # httpx timeouts apply per phase (connect, write, each read); asyncio.timeout
            # bounds the whole exchange so a slow-drip response cannot exceed the budget.
            async with asyncio.timeout(self._timeout):
                response = await self._client.post(
                    self._url,
                    json={"license_plate": license_plate},
                    timeout=self._timeout,
                )
        except (TimeoutError, httpx.TimeoutException) as exc:
            return _failed(ErrorCode.UPSTREAM_TIMEOUT, started, exc=exc)
        except httpx.RequestError as exc:
            # Transport, decoding, redirect, and other request-level faults.
            return _failed(ErrorCode.UPSTREAM_UNAVAILABLE, started, exc=exc)

        status = response.status_code
        match status, _json_or_none(response):
            case HTTPStatus.OK, {"success": True, "data": dict() as data}:
                try:
                    return VehicleData.model_validate(data)
                except ValidationError:
                    return _failed(ErrorCode.UPSTREAM_INVALID_RESPONSE, started, status_code=status)
            # The live upstream answers 404 {"detail": {"success": false, ...}}; any other
            # 404 body means a wrong URL, which must not pass for a missing vehicle.
            case (
                (HTTPStatus.OK | HTTPStatus.NOT_FOUND),
                ({"success": False} | {"detail": {"success": False}}),
            ):
                return ErrorCode.VEHICLE_NOT_FOUND
            case HTTPStatus.OK, _:
                return _failed(ErrorCode.UPSTREAM_INVALID_RESPONSE, started, status_code=status)
            # The proxy validates first, so an upstream rejection signals rule drift (warn),
            # but for the applicant it still means "re-enter the plate".
            case HTTPStatus.BAD_REQUEST | HTTPStatus.UNPROCESSABLE_ENTITY, _:
                return _failed(ErrorCode.INVALID_REQUEST, started, status_code=status)
            case _:
                return _failed(ErrorCode.UPSTREAM_UNAVAILABLE, started, status_code=status)
