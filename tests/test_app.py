from litestar.testing import TestClient

from onboarding_flow.app import app


def test_health_endpoint() -> None:
    with TestClient(app=app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
