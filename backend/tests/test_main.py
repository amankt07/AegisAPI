"""
Basic health check and sanity test suite for AegisAPI backend.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify that the health check endpoint returns 200 OK and expected payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"
    assert "AegisAPI" in data.get("service")

