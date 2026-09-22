"""Production upstream adapter using niquests."""

import json

import niquests
from niquests.exceptions import ConnectionError as NiquestsConnectionError
from niquests.exceptions import Timeout as NiquestsTimeout
from pydantic import HttpUrl, ValidationError

from onboarding_flow.schemas import LicensePlate, VehicleData
from onboarding_flow.upstream import (
    UpstreamFailure,
    UpstreamFailureKind,
    UpstreamOutcome,
    UpstreamSuccess,
)


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


class EncoreUpstream:
    def __init__(
        self,
        session: niquests.AsyncSession,
        url: HttpUrl | str,
        timeout_seconds: float,
    ) -> None:
        self._session = session
        self._url = str(url)
        self._timeout = timeout_seconds

    async def fetch_vehicle(self, license_plate: LicensePlate) -> UpstreamOutcome:
        try:
            response = await self._session.post(
                self._url,
                json={"license_plate": license_plate},
                timeout=self._timeout,
            )
        except NiquestsTimeout:
            return UpstreamFailure(kind=UpstreamFailureKind.TIMEOUT)
        except NiquestsConnectionError:
            return UpstreamFailure(kind=UpstreamFailureKind.UNAVAILABLE)

        status_code = response.status_code
        if status_code is None:
            return UpstreamFailure(kind=UpstreamFailureKind.UNAVAILABLE)

        match status_code:
            case 404:
                return UpstreamFailure(kind=UpstreamFailureKind.NOT_FOUND)
            case code if code >= 500:
                return UpstreamFailure(kind=UpstreamFailureKind.UNAVAILABLE)
            case 200:
                try:
                    body = response.json()
                except json.JSONDecodeError, ValueError:
                    return UpstreamFailure(kind=UpstreamFailureKind.INVALID_RESPONSE)
                return _outcome_from_upstream_body(body)
            case _:
                return UpstreamFailure(kind=UpstreamFailureKind.UNAVAILABLE)
