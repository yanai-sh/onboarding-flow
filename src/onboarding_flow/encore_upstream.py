"""Production upstream adapter using niquests."""

from __future__ import annotations

import json
from typing import Any, override

import niquests
from niquests.exceptions import ConnectionError as NiquestsConnectionError
from niquests.exceptions import Timeout as NiquestsTimeout
from pydantic import ValidationError

from onboarding_flow.schemas import VehicleData
from onboarding_flow.upstream import (
    UpstreamAdapter,
    UpstreamFailure,
    UpstreamFailureKind,
    UpstreamOutcome,
    UpstreamSuccess,
)


class EncoreUpstream(UpstreamAdapter):
    def __init__(
        self,
        session: niquests.AsyncSession,
        url: str,
        timeout_seconds: float,
    ) -> None:
        self._session = session
        self._url = url
        self._timeout = timeout_seconds

    @override
    async def fetch_vehicle(self, license_plate: str) -> UpstreamOutcome:
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
                pass
            case _:
                return UpstreamFailure(kind=UpstreamFailureKind.UNAVAILABLE)

        try:
            body: Any = response.json()
        except json.JSONDecodeError, ValueError:
            return UpstreamFailure(kind=UpstreamFailureKind.INVALID_RESPONSE)

        if not isinstance(body, dict):
            return UpstreamFailure(kind=UpstreamFailureKind.INVALID_RESPONSE)

        if body.get("success") is True and isinstance(body.get("data"), dict):
            try:
                vehicle = VehicleData.model_validate(body["data"])
            except ValidationError:
                return UpstreamFailure(kind=UpstreamFailureKind.INVALID_RESPONSE)
            return UpstreamSuccess(vehicle=vehicle)

        if body.get("success") is False:
            return UpstreamFailure(kind=UpstreamFailureKind.NOT_FOUND)

        return UpstreamFailure(kind=UpstreamFailureKind.INVALID_RESPONSE)
