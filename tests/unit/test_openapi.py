from typing import Any

from litestar.testing import TestClient

from onboarding_flow.envelope import VehicleInfoResponse
from onboarding_flow.schemas import VehicleData, VehicleRequest


def _property_names(component_schema: dict[str, Any]) -> set[str]:
    properties = component_schema.get("properties")
    if not isinstance(properties, dict):
        msg = "OpenAPI component schema missing properties"
        raise AssertionError(msg)
    return set(properties)


def test_openapi_schema_lists_vehicle_info(api_client: TestClient) -> None:
    response = api_client.get("/schema/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Onboarding Flow Vehicle Proxy"
    paths = schema["paths"]
    assert isinstance(paths, dict)
    assert "/vehicle-info" in paths
    assert "post" in paths["/vehicle-info"]
    assert "/health" in paths


def test_openapi_vehicle_models_match_pydantic_contract(api_client: TestClient) -> None:
    response = api_client.get("/schema/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    components = schema["components"]
    assert isinstance(components, dict)
    schemas = components["schemas"]
    assert isinstance(schemas, dict)

    assert _property_names(schemas["VehicleRequest"]) == set(VehicleRequest.model_fields)
    assert _property_names(schemas["VehicleInfoResponse"]) == set(VehicleInfoResponse.model_fields)
    assert _property_names(schemas["VehicleData"]) == set(VehicleData.model_fields)

    post = schema["paths"]["/vehicle-info"]["post"]
    assert isinstance(post, dict)
    request_ref = post["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert request_ref == "#/components/schemas/VehicleRequest"

    response_ref = post["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert response_ref == "#/components/schemas/VehicleInfoResponse"

    responses = post["responses"]
    assert isinstance(responses, dict)
    client_error_codes = {int(code) for code in responses if code.isdigit()}
    assert client_error_codes & {400, 422}
