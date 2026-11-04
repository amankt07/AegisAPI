"""
AegisAPI Backend Tests - Telemetry & Statistics Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.traffic_service import traffic_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_telemetry():
    """Clear traffic service before and after tests for isolated assertions."""
    traffic_service.clear()
    yield
    traffic_service.clear()


def test_traffic_and_statistics_flow():
    """Test full telemetry lifecycle: ingest records, check traffic feed, and statistics."""
    # 1. Initially empty
    stats_resp = client.get("/statistics")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_processed_requests"] == 0
    assert stats["anomalous_requests"] == 0

    # 2. Ingest one normal record
    normal_record = {
        "endpoint": "/api/v1/products",
        "http_method": "GET",
        "status_code": 200,
        "response_time_ms": 50.0,
        "request_size_bytes": 100,
        "response_size_bytes": 2000,
        "requests_per_minute": 10,
        "failed_requests": 0,
    }
    pred_norm = client.post("/predict", json=normal_record)
    assert pred_norm.status_code == 200

    # 3. Ingest one anomalous record
    anomaly_record = {
        "endpoint": "/api/v1/auth/login",
        "http_method": "POST",
        "status_code": 401,
        "response_time_ms": 60.0,
        "request_size_bytes": 250,
        "response_size_bytes": 150,
        "requests_per_minute": 250,
        "failed_requests": 95,
        "user_agent": "Hydra/9.5",
    }
    pred_anom = client.post("/predict", json=anomaly_record)
    assert pred_anom.status_code == 200

    # 4. Verify traffic feed
    traffic_resp = client.get("/traffic?limit=10")
    assert traffic_resp.status_code == 200
    traffic_data = traffic_resp.json()
    assert len(traffic_data) == 2
    # Newest first
    assert traffic_data[0]["endpoint"] == "/api/v1/auth/login"
    assert traffic_data[1]["endpoint"] == "/api/v1/products"

    # 5. Verify anomalies feed
    anom_resp = client.get("/anomalies?limit=10")
    assert anom_resp.status_code == 200
    anom_data = anom_resp.json()
    assert len(anom_data) == 1
    assert anom_data[0]["endpoint"] == "/api/v1/auth/login"
    assert anom_data[0]["status_code"] == 401

    # 6. Verify dashboard statistics
    stats_updated = client.get("/statistics").json()
    assert stats_updated["total_processed_requests"] == 2
    assert stats_updated["normal_requests"] == 1
    assert stats_updated["anomalous_requests"] == 1
    assert stats_updated["anomaly_percentage"] == 50.0
    assert stats_updated["average_response_time_ms"] == 55.0  # (50 + 60)/2
    assert stats_updated["http_error_count"] == 1  # 401
    assert "/api/v1/auth/login" in stats_updated["top_anomalous_endpoints"]


def test_pagination_limits():
    """Verify pagination parameters on traffic and anomalies."""
    # Seed 5 records
    for i in range(5):
        client.post(
            "/predict",
            json={
                "endpoint": f"/api/v1/products/{i}",
                "http_method": "GET",
                "status_code": 200,
                "response_time_ms": 50.0,
            },
        )

    resp_paged = client.get("/traffic?limit=2&offset=1")
    assert resp_paged.status_code == 200
    events = resp_paged.json()
    assert len(events) == 2

