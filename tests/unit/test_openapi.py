from http import HTTPStatus

from tests.fakes import MemoryUpstream
from tests.shared import LIVE_VEHICLE, OpenClient


def test_openapi_documents_the_vehicle_info_contract(open_client: OpenClient) -> None:
    with open_client(MemoryUpstream(LIVE_VEHICLE)) as client:
        response = client.get("/schema/openapi.json")

    assert response.status_code == HTTPStatus.OK
    schema = response.json()
    assert "/health" in schema["paths"]
    post = schema["paths"]["/vehicle-info"]["post"]
    request_schema = post["requestBody"]["content"]["application/json"]["schema"]
    assert request_schema["$ref"] == "#/components/schemas/VehicleRequest"
    ok_schema = post["responses"]["200"]["content"]["application/json"]["schema"]
    assert ok_schema["$ref"] == "#/components/schemas/VehicleInfoResponse"
    assert "400" in post["responses"]
    assert set(schema["components"]["schemas"]["ErrorCode"]["enum"]) == {
        "INVALID_REQUEST",
        "VEHICLE_NOT_FOUND",
        "UPSTREAM_TIMEOUT",
        "UPSTREAM_UNAVAILABLE",
        "UPSTREAM_INVALID_RESPONSE",
    }
