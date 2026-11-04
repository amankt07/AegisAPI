"""
AegisAPI Backend Tests - Health & Model Info Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that root endpoint returns service discovery metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "AegisAPI" in data["service"]
    assert data["model_loaded"] is True
    assert data["active_model"] == "Isolation Forest"


def test_health_endpoint():
    """Verify that health check reports healthy status and loaded model details."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["model_name"] == "Isolation Forest"
    assert data["feature_count"] == 42


def test_model_info_endpoint():
    """Verify that model-info endpoint returns complete metadata and metrics."""
    response = client.get("/model-info")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "Isolation Forest"
    assert data["feature_count"] == 42
    assert "evaluation_metrics" in data
    assert "hyperparameters" in data
    assert "score_interpretation" in data

    # Check that key metrics exist and are non-trivial
    metrics = data["evaluation_metrics"]
    assert metrics["Accuracy"] > 0.90
    assert metrics["ROC-AUC"] > 0.95
    assert metrics["F1-Score"] > 0.80

