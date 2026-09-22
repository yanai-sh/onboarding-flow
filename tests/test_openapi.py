from typing import Any

from litestar.testing import TestClient

from onboarding_flow.app import create_app
from onboarding_flow.memory_upstream import success_upstream
from onboarding_flow.schemas import VehicleData, VehicleInfoResponse, VehicleRequest

SAMPLE_VEHICLE = VehicleData(
    license_plate="12345678",
    manufacturer="Toyota",
    model="Corolla",
    year=2020,
    color="White",
)


def _property_names(component_schema: dict[str, Any]) -> set[str]:
    properties = component_schema.get("properties")
    if not isinstance(properties, dict):
        msg = "OpenAPI component schema missing properties"
        raise AssertionError(msg)
    return set(properties)


def _fetch_openapi() -> dict[str, Any]:
    upstream = success_upstream(SAMPLE_VEHICLE)
    with TestClient(app=create_app(upstream=upstream)) as client:
        response = client.get("/schema/openapi.json")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    return body


def test_openapi_schema_lists_vehicle_info() -> None:
    schema = _fetch_openapi()
    assert schema["info"]["title"] == "Onboarding Flow Vehicle Proxy"
    paths = schema["paths"]
    assert isinstance(paths, dict)
    assert "/vehicle-info" in paths
    assert "post" in paths["/vehicle-info"]
    assert "/health" in paths


def test_openapi_vehicle_models_match_pydantic_contract() -> None:
    schema = _fetch_openapi()
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
