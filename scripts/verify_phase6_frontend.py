"""
AegisAPI Phase 6 Frontend Verification Script
Validates:
1. Frontend build artifacts (dist/index.html, vendor, charts, icons, css)
2. API Service client contract (endpoints, methods, base URLs)
3. Schema compatibility between FastAPI responses and React state
4. End-to-end integration test with live FastAPI client
"""
import os
import sys
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app

def verify_frontend():
    print("=" * 70)
    print("AegisAPI - Phase 6 Frontend Integration Verification")
    print("=" * 70)

    # 1. Check Frontend Build Output
    print("\n[1] Verifying Frontend Production Build Artifacts...")
    dist_dir = os.path.join(FRONTEND_DIR, "dist")
    assert os.path.exists(dist_dir), "dist/ directory missing. Run npm run build."

    index_html = os.path.join(dist_dir, "index.html")
    assert os.path.exists(index_html), "dist/index.html missing."

    assets_dir = os.path.join(dist_dir, "assets")
    assets = os.listdir(assets_dir) if os.path.exists(assets_dir) else []
    print(f" -> Found {len(assets)} compiled assets in dist/assets/:")
    for a in assets:
        size = os.path.getsize(os.path.join(assets_dir, a))
        print(f"    - {a} ({size / 1024:.1f} KB)")

    assert any(a.endswith(".js") for a in assets), "No JavaScript bundles found in dist/assets."
    assert any(a.endswith(".css") for a in assets), "No CSS bundle found in dist/assets."
    print(" -> Frontend build artifacts verified successfully.")

    # 2. Check File Contracts
    print("\n[2] Checking Required Frontend File Contracts...")
    api_js = os.path.join(FRONTEND_DIR, "src", "services", "api.js")
    assert os.path.exists(api_js), "frontend/src/services/api.js missing."
    with open(api_js, "r", encoding="utf-8") as f:
        api_content = f.read()

    required_methods = [
        "getHealth",
        "getStatistics",
        "getTraffic",
        "getAnomalies",
        "getModelInfo",
        "predictTraffic",
    ]
    for method in required_methods:
        assert method in api_content, f"Missing {method} in api.js"
        print(f" -> API method verified: {method}()")

    env_example = os.path.join(FRONTEND_DIR, ".env.example")
    assert os.path.exists(env_example), "frontend/.env.example missing."
    print(" -> frontend/.env.example verified.")

    # 3. Check Page Components
    pages = ["Dashboard.jsx", "AnomalyMonitoring.jsx", "TrafficExplorer.jsx", "ModelInformation.jsx"]
    print("\n[3] Verifying Page Components in frontend/src/pages/...")
    for p in pages:
        page_path = os.path.join(FRONTEND_DIR, "src", "pages", p)
        assert os.path.exists(page_path), f"Missing page: {p}"
        print(f" -> Page verified: {p}")

    # 4. Check Recharts Components
    charts = [
        "TrafficVolumeChart.jsx",
        "NormalVsAnomalyChart.jsx",
        "ResponseTimeChart.jsx",
        "StatusDistributionChart.jsx",
        "EndpointDistributionChart.jsx",
    ]
    print("\n[4] Verifying Chart Components in frontend/src/components/charts/...")
    for c in charts:
        chart_path = os.path.join(FRONTEND_DIR, "src", "components", "charts", c)
        assert os.path.exists(chart_path), f"Missing chart: {c}"
        print(f" -> Chart verified: {c}")

    # 5. Live FastAPI Endpoint Compatibility
    print("\n[5] Verifying FastAPI Endpoint Responses for React State Compatibility...")
    client = TestClient(app)

    # Health
    resp = client.get("/health")
    assert resp.status_code == 200
    health = resp.json()
    assert "status" in health and "model_loaded" in health
    print(f" -> GET /health: OK (status={health['status']}, model_loaded={health['model_loaded']})")

    # Statistics (for Dashboard 6 KPI cards & charts)
    resp = client.get("/statistics")
    assert resp.status_code == 200
    stats = resp.json()
    for kpi in ["total_processed_requests", "normal_requests", "anomalous_requests", "anomaly_percentage", "average_response_time_ms", "http_error_count"]:
        assert kpi in stats, f"Missing KPI field: {kpi}"
    print(f" -> GET /statistics: OK (Total: {stats['total_processed_requests']}, Anomalous: {stats['anomalous_requests']}, Rate: {stats['anomaly_percentage']}%)")

    # Traffic Explorer
    resp = client.get("/traffic?limit=10&offset=0")
    assert resp.status_code == 200
    traffic = resp.json()
    print(f" -> GET /traffic: OK (Returned {len(traffic)} records)")
    if len(traffic) > 0:
        t0 = traffic[0]
        for field in ["endpoint", "http_method", "status_code", "response_time_ms", "is_anomaly"]:
            assert field in t0, f"Missing field in TrafficEvent: {field}"

    # Anomalies
    resp = client.get("/anomalies?limit=10&offset=0")
    assert resp.status_code == 200
    anomalies = resp.json()
    print(f" -> GET /anomalies: OK (Returned {len(anomalies)} records)")
    if len(anomalies) > 0:
        a0 = anomalies[0]
        for field in ["endpoint", "http_method", "status_code", "anomaly_score", "threat_level"]:
            assert field in a0, f"Missing field in AnomalyEvent: {field}"

    # Model Info
    resp = client.get("/model-info")
    assert resp.status_code == 200
    model_info = resp.json()
    for field in ["model_name", "algorithm", "evaluation_metrics", "feature_names", "hyperparameters"]:
        assert field in model_info, f"Missing field in ModelInfo: {field}"
    print(f" -> GET /model-info: OK (Model: {model_info['model_name']}, Features: {model_info['feature_count']}, Metrics: {list(model_info['evaluation_metrics'].keys())})")

    # Predict
    resp = client.post("/predict", json={
        "endpoint": "/api/v1/auth/login",
        "http_method": "POST",
        "status_code": 401,
        "response_time_ms": 65.0,
        "requests_per_minute": 210,
        "failed_requests": 80,
    })
    assert resp.status_code == 200
    pred = resp.json()
    print(f" -> POST /predict: OK (is_anomaly={pred['is_anomaly']}, label={pred['prediction_label']}, score={pred['anomaly_score']:.4f}, level={pred['threat_level']})")

    print("\n" + "=" * 70)
    print("PHASE 6 FRONTEND DASHBOARD: FULLY VERIFIED AND INTEGRATED")
    print("=" * 70)

if __name__ == "__main__":
    verify_frontend()

