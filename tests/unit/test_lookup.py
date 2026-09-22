import pytest

from onboarding_flow.envelope import ErrorCode
from onboarding_flow.lookup import (
    LookupFailure,
    LookupSuccess,
    VehicleLookup,
    lookup_result_from_outcome,
)
from onboarding_flow.memory_upstream import success_upstream
from onboarding_flow.schemas import VehicleData
from onboarding_flow.upstream import UpstreamFailure, UpstreamFailureKind, UpstreamSuccess


@pytest.mark.parametrize(
    ("kind", "expected_code"),
    [
        (UpstreamFailureKind.NOT_FOUND, ErrorCode.VEHICLE_NOT_FOUND),
        (UpstreamFailureKind.TIMEOUT, ErrorCode.UPSTREAM_TIMEOUT),
        (UpstreamFailureKind.UNAVAILABLE, ErrorCode.UPSTREAM_UNAVAILABLE),
        (UpstreamFailureKind.INVALID_RESPONSE, ErrorCode.UPSTREAM_INVALID_RESPONSE),
    ],
)
def test_lookup_maps_upstream_failures(
    kind: UpstreamFailureKind,
    expected_code: ErrorCode,
) -> None:
    result = lookup_result_from_outcome(UpstreamFailure(kind=kind))
    assert result.success is False
    assert isinstance(result, LookupFailure)
    assert result.error_code == expected_code
    assert result.message


def test_lookup_success() -> None:
    vehicle = VehicleData(
        license_plate="12345678",
        manufacturer="Toyota",
        model="Corolla",
        year=2020,
        color="White",
    )
    result = lookup_result_from_outcome(UpstreamSuccess(vehicle=vehicle))
    assert result.success is True
    assert isinstance(result, LookupSuccess)
    assert result.data == vehicle


@pytest.mark.asyncio
async def test_vehicle_lookup_calls_upstream_with_plate() -> None:
    vehicle = VehicleData(
        license_plate="12345678",
        manufacturer="Toyota",
        model="Corolla",
        year=2020,
        color="White",
    )
    upstream = success_upstream(vehicle)
    service = VehicleLookup(upstream)
    result = await service.lookup("12345678")
    assert result.success is True
    assert upstream.call_count == 1
    assert upstream.last_plate == "12345678"
