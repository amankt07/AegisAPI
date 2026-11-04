"""
AegisAPI Backend Tests - Main Suite Entrypoint
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_main_app_startup():
    """Verify application boots, responds, and mounts documentation."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "AegisAPI" in response.text
