import json
from typing import Any

import pytest

from onboarding_flow.envelope import ErrorCode
from onboarding_flow.memory_upstream import failure_upstream, success_upstream
from onboarding_flow.schemas import VehicleData
from onboarding_flow.upstream import UpstreamFailureKind
from onboarding_flow.vehicle_lookup import lookup_vehicle_info


@pytest.mark.asyncio
async def test_lookup_happy_path_calls_upstream_and_returns_envelope(
    assignment_vehicle: VehicleData,
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
    assignment_vehicle: VehicleData,
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
async def test_lookup_logs_masked_plate_not_raw_value(
    assignment_vehicle: VehicleData,
    json_logs: list[dict[str, Any]],
) -> None:
    plate = assignment_vehicle.license_plate
    upstream = success_upstream(assignment_vehicle)
    await lookup_vehicle_info(plate, upstream, "trace-log")

    [event] = [line for line in json_logs if line["message"] == "vehicle_lookup_completed"]
    assert event["plate_mask"] == "****5678"
    assert event["trace_id"] == "trace-log"
    assert event["success"] is True
    assert isinstance(event["duration_ms"], int | float)
    assert event["duration_ms"] >= 0
    assert plate not in json.dumps(json_logs)


@pytest.mark.parametrize(
    ("kind", "expected_code"),
    [
        (UpstreamFailureKind.NOT_FOUND, "VEHICLE_NOT_FOUND"),
        (UpstreamFailureKind.TIMEOUT, "UPSTREAM_TIMEOUT"),
    ],
)
@pytest.mark.asyncio
async def test_lookup_logs_failure_outcome(
    assignment_vehicle: VehicleData,
    kind: UpstreamFailureKind,
    expected_code: str,
    json_logs: list[dict[str, Any]],
) -> None:
    upstream = failure_upstream(kind)
    plate = assignment_vehicle.license_plate
    await lookup_vehicle_info(plate, upstream, "trace-log")

    [event] = [line for line in json_logs if line["message"] == "vehicle_lookup_completed"]
    assert event["success"] is False
    assert event["error_code"] == expected_code
    assert plate not in json.dumps(json_logs)
