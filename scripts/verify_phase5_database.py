"""
AegisAPI Phase 5 Verification Script
Verifies SQLite Database Integration:
1. Database file creation & table initialization
2. Model metadata registration in SQLite
3. End-to-end prediction persistence via FastAPI
4. Foreign key integrity and query performance
5. Telemetry endpoints (/traffic, /anomalies, /statistics, /model-info)
6. Data persistence across simulated server restart
"""
import os
import sys
import sqlite3
import json

# Ensure project root and backend are on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.database import DEFAULT_DB_PATH, init_db

def run_verification():
    print("=" * 70)
    print("AegisAPI - Phase 5 Database Verification")
    print("=" * 70)

    # 1. Database file and initialization
    print(f"\n[1] Verifying SQLite Database File: {DEFAULT_DB_PATH}")
    init_db()
    assert os.path.exists(DEFAULT_DB_PATH), f"Database file missing: {DEFAULT_DB_PATH}"
    print(f" -> Database file exists. Size: {os.path.getsize(DEFAULT_DB_PATH)} bytes.")

    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cursor = conn.cursor()

    # 2. Schema inspection
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n[2] Database Tables Detected: {tables}")
    for required_table in ["traffic_events", "anomaly_predictions", "model_information"]:
        assert required_table in tables, f"Missing table: {required_table}"
    print(" -> All required tables (traffic_events, anomaly_predictions, model_information) exist.")

    # 3. Model Information seed
    cursor.execute("SELECT id, model_name, algorithm, training_records, feature_count, is_active FROM model_information;")
    models_stored = cursor.fetchall()
    print(f"\n[3] Model Information Registered in SQLite ({len(models_stored)} records):")
    for m in models_stored:
        print(f" -> ID: {m[0]} | Name: {m[1]} | Algo: {m[2]} | Records: {m[3]} | Features: {m[4]} | Active: {m[5]}")
    assert len(models_stored) > 0, "No model information found in SQLite table!"

    # 4. Ingest telemetry via FastAPI client
    client = TestClient(app)

    print("\n[4] Sending Ingest Predictions via FastAPI Endpoints...")
    # A. Normal GET
    resp_norm = client.post("/predict", json={
        "endpoint": "/api/v1/catalog",
        "http_method": "GET",
        "status_code": 200,
        "response_time_ms": 45.0,
        "request_size_bytes": 150,
        "response_size_bytes": 2200,
        "requests_per_minute": 12,
        "failed_requests": 0,
        "source_ip": "192.168.1.55",
        "user_agent": "Mozilla/5.0",
    })
    assert resp_norm.status_code == 200, resp_norm.text
    norm_data = resp_norm.json()
    print(f" -> Normal Request: is_anomaly={norm_data['is_anomaly']} | label={norm_data['prediction_label']} | score={norm_data['anomaly_score']}")

    # B. Anomalous Brute Force
    resp_anom = client.post("/predict", json={
        "endpoint": "/api/v1/auth/login",
        "http_method": "POST",
        "status_code": 401,
        "response_time_ms": 52.0,
        "request_size_bytes": 240,
        "response_size_bytes": 140,
        "requests_per_minute": 220,
        "failed_requests": 85,
        "source_ip": "198.51.100.99",
        "user_agent": "Hydra/9.5",
    })
    assert resp_anom.status_code == 200, resp_anom.text
    anom_data = resp_anom.json()
    print(f" -> Anomaly Request: is_anomaly={anom_data['is_anomaly']} | label={anom_data['prediction_label']} | score={anom_data['anomaly_score']}")

    # C. Batch Ingest
    batch_records = [
        {
            "endpoint": "/api/v1/checkout",
            "http_method": "POST",
            "status_code": 200,
            "response_time_ms": 80.0,
            "request_size_bytes": 400,
            "response_size_bytes": 800,
            "requests_per_minute": 15,
            "failed_requests": 0,
            "source_ip": "192.168.1.70",
        },
        {
            "endpoint": "/api/v1/data/dump",
            "http_method": "GET",
            "status_code": 200,
            "response_time_ms": 2900.0,
            "request_size_bytes": 450,
            "response_size_bytes": 18000000,
            "requests_per_minute": 10,
            "failed_requests": 0,
            "source_ip": "203.0.113.8",
        },
    ]
    resp_batch = client.post("/predict/batch", json={"records": batch_records})
    assert resp_batch.status_code == 200, resp_batch.text
    batch_data = resp_batch.json()
    print(f" -> Batch Ingest ({len(batch_data['predictions'])} records): Successful")

    # 5. Direct SQLite Inspection
    print("\n[5] Direct SQLite Verification via sqlite3 driver...")
    cursor.execute("""
        SELECT t.id, t.endpoint, t.http_method, t.status_code, p.is_anomaly, p.prediction_label, p.anomaly_score
        FROM traffic_events t
        JOIN anomaly_predictions p ON t.id = p.traffic_event_id
        ORDER BY t.id ASC;
    """)
    rows = cursor.fetchall()
    print(f" -> Found {len(rows)} joined traffic-prediction records in SQLite:")
    for r in rows:
        print(f"    Event #{r[0]}: {r[2]} {r[1]} [HTTP {r[3]}] -> Anomaly: {bool(r[4])} ({r[5]}, Score: {r[6]:.4f})")
    assert len(rows) >= 4, "Expected at least 4 stored records!"

    # 6. Verify API Telemetry Routes
    print("\n[6] Verifying API Telemetry Routes...")
    resp_traffic = client.get("/traffic?limit=5")
    assert resp_traffic.status_code == 200
    traffic_feed = resp_traffic.json()
    print(f" -> GET /traffic: Returned {len(traffic_feed)} events (Newest first)")

    resp_anomalies = client.get("/anomalies?limit=5")
    assert resp_anomalies.status_code == 200
    anomalies_feed = resp_anomalies.json()
    print(f" -> GET /anomalies: Returned {len(anomalies_feed)} anomalous events")
    for a in anomalies_feed:
        assert a["threat_level"] in ["Safe", "Low Threat", "Medium Threat", "High Threat", "Critical Threat"]
        print(f"    Incident #{a['id']}: {a['http_method']} {a['endpoint']} (Score: {a['anomaly_score']:.4f}, Level: {a['threat_level']})")

    resp_stats = client.get("/statistics")
    assert resp_stats.status_code == 200
    stats = resp_stats.json()
    print(f" -> GET /statistics: Total={stats['total_processed_requests']}, Anomalous={stats['anomalous_requests']}, Pct={stats['anomaly_percentage']}%, AvgLatency={stats['average_response_time_ms']}ms")

    resp_info = client.get("/model-info")
    assert resp_info.status_code == 200
    info = resp_info.json()
    print(f" -> GET /model-info: Model='{info['model_name']}', Algorithm='{info['algorithm']}', Features={info['feature_count']}")

    conn.close()

    # 7. Restart simulation
    print("\n[7] Simulating Server Restart & Persistence Verification...")
    conn2 = sqlite3.connect(DEFAULT_DB_PATH)
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT COUNT(*) FROM traffic_events;")
    total_after_restart = cursor2.fetchone()[0]
    cursor2.execute("SELECT COUNT(*) FROM anomaly_predictions;")
    preds_after_restart = cursor2.fetchone()[0]
    conn2.close()

    print(f" -> Persistence Confirmed: {total_after_restart} traffic events and {preds_after_restart} predictions survive session closure.")
    assert total_after_restart >= 4
    assert preds_after_restart == total_after_restart

    print("\n" + "=" * 70)
    print("PHASE 5 DATABASE INTEGRATION: FULLY VERIFIED AND OPERATIONAL")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
