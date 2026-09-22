from unittest.mock import patch

import pytest

from onboarding_flow.envelope import ErrorCode
from onboarding_flow.memory_upstream import failure_upstream, success_upstream
from onboarding_flow.upstream import UpstreamFailureKind
from onboarding_flow.vehicle_lookup import lookup_vehicle_info


@pytest.mark.asyncio
async def test_lookup_happy_path_calls_upstream_and_returns_envelope(
    assignment_vehicle,
) -> None:
    upstream = success_upstream(assignment_vehicle)
    response = await lookup_vehicle_info(assignment_vehicle.license_plate, upstream, "trace-1")

    assert response.success is True
    assert response.data == assignment_vehicle
    assert response.trace_id == "trace-1"
    assert upstream.call_count == 1


@pytest.mark.parametrize(
    ("kind", "expected_code"),
    [
        (UpstreamFailureKind.NOT_FOUND, ErrorCode.VEHICLE_NOT_FOUND),
        (UpstreamFailureKind.TIMEOUT, ErrorCode.UPSTREAM_TIMEOUT),
        (UpstreamFailureKind.UNAVAILABLE, ErrorCode.UPSTREAM_UNAVAILABLE),
        (UpstreamFailureKind.INVALID_RESPONSE, ErrorCode.UPSTREAM_INVALID_RESPONSE),
    ],
)
@pytest.mark.asyncio
async def test_lookup_maps_upstream_failures(
    assignment_vehicle,
    kind: UpstreamFailureKind,
    expected_code: ErrorCode,
) -> None:
    upstream = failure_upstream(kind)
    plate = assignment_vehicle.license_plate
    response = await lookup_vehicle_info(plate, upstream, "trace-fail")

    assert response.success is False
    assert response.error_code == expected_code
    assert upstream.call_count == 1


@pytest.mark.asyncio
async def test_lookup_logs_masked_plate_not_raw_value(assignment_vehicle) -> None:
    plate = assignment_vehicle.license_plate
    upstream = success_upstream(assignment_vehicle)
    with patch("onboarding_flow.vehicle_lookup.logger.info") as log_info:
        await lookup_vehicle_info(plate, upstream, "trace-log")

    log_info.assert_called_once()
    extra = log_info.call_args.kwargs["extra"]
    assert extra["plate_mask"] == "****5678"
    assert extra["trace_id"] == "trace-log"
    assert plate not in extra.values()


@pytest.mark.parametrize(
    "kind",
    [
        UpstreamFailureKind.NOT_FOUND,
        UpstreamFailureKind.TIMEOUT,
    ],
)
@pytest.mark.asyncio
async def test_lookup_logs_failure_outcome(
    assignment_vehicle,
    kind: UpstreamFailureKind,
) -> None:
    upstream = failure_upstream(kind)
    plate = assignment_vehicle.license_plate
    with patch("onboarding_flow.vehicle_lookup.logger.info") as log_info:
        await lookup_vehicle_info(plate, upstream, "trace-log")

    extra = log_info.call_args.kwargs["extra"]
    assert extra["success"] is False
    assert extra["error_code"] is not None
