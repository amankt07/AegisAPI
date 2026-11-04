"""
AegisAPI Phase 7: End-to-End System Benchmark & Reliability Validation
Measures actual API response times, batch inference throughput,
database query execution speeds, validation boundaries, and persistence.
"""
import os
import sys
import time
import json
import sqlite3
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.database import DEFAULT_DB_PATH, init_db

def run_benchmark():
    print("=" * 75)
    print("AEGISAPI – PHASE 7: END-TO-END VALIDATION & PERFORMANCE BENCHMARK")
    print("=" * 75)

    client = TestClient(app)
    results = {}

    # -----------------------------------------------------------------------
    # 1. Health & Model Integrity Check
    # -----------------------------------------------------------------------
    print("\n[1] Health & Model Loading Verification...")
    t0 = time.perf_counter()
    resp_health = client.get("/health")
    health_latency = (time.perf_counter() - t0) * 1000
    assert resp_health.status_code == 200, "Health check failed!"
    health_data = resp_health.json()
    assert health_data["model_loaded"] is True, "Model is not loaded!"
    print(f" -> Service Health: {health_data['status'].upper()} | Model: {health_data['model_name']} | Features: {health_data['feature_count']}")
    print(f" -> Health Endpoint Latency: {health_latency:.2f} ms")
    results["health_latency_ms"] = round(health_latency, 2)

    # -----------------------------------------------------------------------
    # 2. Single Prediction Latency Benchmark (N=50 runs)
    # -----------------------------------------------------------------------
    print("\n[2] Single Request Prediction Latency Benchmark (N=50)...")
    single_payload = {
        "endpoint": "/api/v1/auth/login",
        "http_method": "POST",
        "status_code": 401,
        "response_time_ms": 62.0,
        "request_size_bytes": 240,
        "response_size_bytes": 180,
        "requests_per_minute": 190,
        "failed_requests": 65,
        "source_ip": "198.51.100.45",
        "user_agent": "Hydra/9.5 (Kali)",
    }

    latencies = []
    for _ in range(50):
        t_start = time.perf_counter()
        resp = client.post("/predict", json=single_payload)
        t_end = time.perf_counter()
        assert resp.status_code == 200
        latencies.append((t_end - t_start) * 1000)

    p50 = float(np.percentile(latencies, 50))
    p95 = float(np.percentile(latencies, 95))
    p99 = float(np.percentile(latencies, 99))
    mean_lat = float(np.mean(latencies))

    pred_result = resp.json()
    print(f" -> Prediction Verdict: {pred_result['prediction_label']} | Score: {pred_result['anomaly_score']:.4f} | Tier: {pred_result['threat_level']}")
    print(f" -> Mean Latency: {mean_lat:.2f} ms | P50: {p50:.2f} ms | P95: {p95:.2f} ms | P99: {p99:.2f} ms")
    results["single_predict"] = {
        "mean_ms": round(mean_lat, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
    }

    # -----------------------------------------------------------------------
    # 3. Vectorized Batch Prediction Benchmark (10, 50, 100, 250 records)
    # -----------------------------------------------------------------------
    print("\n[3] Vectorized Batch Prediction Throughput Benchmark...")
    batch_sizes = [10, 50, 100, 250]
    batch_metrics = {}

    for size in batch_sizes:
        batch_payload = [
            {
                "endpoint": f"/api/v1/resource/{i % 10}",
                "http_method": "GET" if i % 2 == 0 else "POST",
                "status_code": 200 if i % 3 != 0 else 401,
                "response_time_ms": 40.0 + (i % 50),
                "request_size_bytes": 150 + i,
                "response_size_bytes": 1000 + i * 2,
                "requests_per_minute": 10 + (i % 20),
                "failed_requests": i % 5,
                "source_ip": f"192.168.1.{i % 250 + 1}",
            }
            for i in range(size)
        ]

        t0 = time.perf_counter()
        resp_batch = client.post("/predict/batch", json={"records": batch_payload})
        t_batch = (time.perf_counter() - t0) * 1000
        assert resp_batch.status_code == 200
        batch_resp = resp_batch.json()
        throughput = size / (t_batch / 1000)

        print(f" -> Batch Size {size:3d}: {t_batch:6.2f} ms | Throughput: {throughput:7.1f} rec/sec | Anomalies Detected: {batch_resp['anomalies_detected']}")
        batch_metrics[f"batch_{size}"] = {
            "total_ms": round(t_batch, 2),
            "throughput_rec_sec": round(throughput, 1),
            "anomalies_detected": batch_resp["anomalies_detected"],
        }
    results["batch_benchmarks"] = batch_metrics

    # -----------------------------------------------------------------------
    # 4. Database Query & Telemetry Performance
    # -----------------------------------------------------------------------
    print("\n[4] Database Query Execution Performance...")

    # A. Statistics SQL Aggregate
    t0 = time.perf_counter()
    resp_stats = client.get("/statistics")
    stats_ms = (time.perf_counter() - t0) * 1000
    assert resp_stats.status_code == 200
    stats = resp_stats.json()
    print(f" -> GET /statistics: {stats_ms:.2f} ms | Total Records: {stats['total_processed_requests']} | Anomalies: {stats['anomalous_requests']} ({stats['anomaly_percentage']}%)")

    # B. Recent Traffic (Limit 50)
    t0 = time.perf_counter()
    resp_traffic = client.get("/traffic?limit=50&offset=0")
    traffic_ms = (time.perf_counter() - t0) * 1000
    assert resp_traffic.status_code == 200
    print(f" -> GET /traffic (50 items): {traffic_ms:.2f} ms | Returned: {len(resp_traffic.json())}")

    # C. Anomalies Only (Limit 50)
    t0 = time.perf_counter()
    resp_anom = client.get("/anomalies?limit=50&offset=0")
    anom_ms = (time.perf_counter() - t0) * 1000
    assert resp_anom.status_code == 200
    print(f" -> GET /anomalies (50 items): {anom_ms:.2f} ms | Returned: {len(resp_anom.json())}")

    # D. Model Information
    t0 = time.perf_counter()
    resp_info = client.get("/model-info")
    info_ms = (time.perf_counter() - t0) * 1000
    assert resp_info.status_code == 200
    print(f" -> GET /model-info: {info_ms:.2f} ms | Active Champion: {resp_info.json()['model_name']}")

    results["query_latencies"] = {
        "statistics_ms": round(stats_ms, 2),
        "traffic_ms": round(traffic_ms, 2),
        "anomalies_ms": round(anom_ms, 2),
        "model_info_ms": round(info_ms, 2),
    }

    # -----------------------------------------------------------------------
    # 5. Input Validation & Error Handling Resilience
    # -----------------------------------------------------------------------
    print("\n[5] Input Validation & Edge-Case Error Handling...")

    # Test Invalid HTTP Method
    resp_err1 = client.post("/predict", json={**single_payload, "http_method": "INVALID_VERB"})
    assert resp_err1.status_code == 422
    print(f" -> Rejection of Invalid HTTP Verb: OK (Status 422)")

    # Test Negative Response Time
    resp_err2 = client.post("/predict", json={**single_payload, "response_time_ms": -100.0})
    assert resp_err2.status_code == 422
    print(f" -> Rejection of Negative Latency: OK (Status 422)")

    # Test Out-of-Range Status Code
    resp_err3 = client.post("/predict", json={**single_payload, "status_code": 999})
    assert resp_err3.status_code == 422
    print(f" -> Rejection of Out-of-Range HTTP Status Code (999): OK (Status 422)")

    # Test Missing Required Fields
    resp_err4 = client.post("/predict", json={"endpoint": "/api/v1/empty"})
    assert resp_err4.status_code == 422
    print(f" -> Rejection of Missing Required Fields: OK (Status 422)")

    # Test Empty Batch
    resp_err5 = client.post("/predict/batch", json={"records": []})
    assert resp_err5.status_code == 422
    print(f" -> Rejection of Empty Batch Payload: OK (Status 422)")

    # -----------------------------------------------------------------------
    # 6. Database Persistence Across Reconnect
    # -----------------------------------------------------------------------
    print("\n[6] Database Persistence Verification Across Session Reconnect...")
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM traffic_events;")
    total_events = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM anomaly_predictions;")
    total_preds = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM model_information;")
    total_models = cursor.fetchone()[0]
    conn.close()

    print(f" -> Traffic Events Persisted in SQLite: {total_events}")
    print(f" -> Anomaly Predictions Linked in SQLite: {total_preds}")
    print(f" -> Model Governance Records in SQLite: {total_models}")
    assert total_events == total_preds, "Mismatch between traffic events and predictions!"
    assert total_models >= 1, "Model metadata not stored!"
    print(" -> 1-to-1 Foreign Key and Persistence Integrity Verified.")

    print("\n" + "=" * 75)
    print("ALL PHASE 7 BENCHMARKS & INTEGRATION VALIDATIONS: 100% PASSED")
    print("=" * 75)

    return results

if __name__ == "__main__":
    benchmark_results = run_benchmark()

