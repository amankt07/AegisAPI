"""
AegisAPI Backend Tests - Anomaly Detection Inference Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_predict_normal_traffic():
    """Verify inference on a standard, benign GET request."""
    payload = {
        "endpoint": "/api/v1/products",
        "http_method": "GET",
        "status_code": 200,
        "response_time_ms": 65.0,
        "request_size_bytes": 180,
        "response_size_bytes": 3400,
        "requests_per_minute": 14,
        "failed_requests": 0,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "source_ip": "192.168.1.45",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["is_anomaly"] == 0
    assert data["prediction_label"] == "Normal"
    assert data["threat_level"] in ["Safe", "Low Threat"]
    assert data["anomaly_score"] < 0.05
    assert data["model_name"] == "Isolation Forest"
    assert "timestamp" in data


def test_predict_anomaly_brute_force():
    """Verify detection on a synthetic brute force authentication attack."""
    payload = {
        "endpoint": "/api/v1/auth/login",
        "http_method": "POST",
        "status_code": 401,
        "response_time_ms": 55.0,
        "request_size_bytes": 240,
        "response_size_bytes": 180,
        "requests_per_minute": 180,
        "failed_requests": 85,
        "user_agent": "Hydra/9.5",
        "source_ip": "198.51.100.12",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["is_anomaly"] == 1
    assert data["prediction_label"] == "Anomaly"
    assert data["threat_level"] in ["Medium Threat", "High Threat", "Critical Threat"]
    assert data["anomaly_score"] > 0.0


def test_predict_anomaly_data_exfiltration():
    """Verify detection on a large outbound data dump."""
    payload = {
        "endpoint": "/api/v1/users/export",
        "http_method": "GET",
        "status_code": 200,
        "response_time_ms": 2800.0,
        "request_size_bytes": 450,
        "response_size_bytes": 18500000,
        "requests_per_minute": 12,
        "failed_requests": 0,
        "user_agent": "curl/8.4.0",
        "source_ip": "203.0.113.8",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["is_anomaly"] == 1
    assert data["prediction_label"] == "Anomaly"
    assert data["anomaly_score"] > 0.0


def test_predict_invalid_status_code():
    """Ensure invalid HTTP status code is rejected with 422."""
    payload = {
        "endpoint": "/api/v1/products",
        "http_method": "GET",
        "status_code": 999,  # Invalid RFC HTTP code
        "response_time_ms": 50.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_negative_latency():
    """Ensure negative latency is rejected with 422."""
    payload = {
        "endpoint": "/api/v1/products",
        "http_method": "GET",
        "status_code": 200,
        "response_time_ms": -10.5,  # Physically invalid
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_invalid_method():
    """Ensure invalid HTTP method is rejected with 422."""
    payload = {
        "endpoint": "/api/v1/products",
        "http_method": "INVALID_VERB",
        "status_code": 200,
        "response_time_ms": 50.0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_missing_required_fields():
    """Ensure payload missing required fields is rejected."""
    payload = {
        "http_method": "GET",
        # Missing endpoint and status_code
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_batch_success():
    """Verify batch inference endpoint with mixed records."""
    records = [
        {
            "endpoint": "/api/v1/products",
            "http_method": "GET",
            "status_code": 200,
            "response_time_ms": 60.0,
            "request_size_bytes": 150,
            "response_size_bytes": 3200,
            "requests_per_minute": 10,
            "failed_requests": 0,
        },
        {
            "endpoint": "/api/v1/auth/login",
            "http_method": "POST",
            "status_code": 401,
            "response_time_ms": 45.0,
            "request_size_bytes": 220,
            "response_size_bytes": 150,
            "requests_per_minute": 220,
            "failed_requests": 90,
            "user_agent": "Hydra/9.5",
        },
        {
            "endpoint": "/api/v1/cart",
            "http_method": "GET",
            "status_code": 200,
            "response_time_ms": 72.0,
            "request_size_bytes": 180,
            "response_size_bytes": 1200,
            "requests_per_minute": 15,
            "failed_requests": 0,
        },
    ]
    response = client.post("/predict/batch", json={"records": records})
    assert response.status_code == 200
    data = response.json()

    assert data["total_records"] == 3
    assert len(data["predictions"]) == 3
    assert data["anomalies_detected"] >= 1
    assert data["anomaly_rate_percent"] > 0.0


def test_predict_batch_empty():
    """Ensure empty batch is rejected."""
    response = client.post("/predict/batch", json={"records": []})
    assert response.status_code == 422

