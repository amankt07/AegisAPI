# AegisAPI – Comprehensive Testing & Validation Report (Phase 7)

This report details the testing methodologies, benchmark measurements, validation criteria, and reliability assessments conducted across the AegisAPI platform.

---

## 1. Test Suite Summary & Coverage Matrix

| Test Suite Module | Test Scope & Target | Tests Executed | Status | Execution Time |
| :--- | :--- | :---: | :---: | :---: |
| [`test_database.py`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/backend/tests/test_database.py) | Engine connection, schema tables, 1-to-1 foreign key cascade, rollback on error, paginated queries, SQL metrics, cross-session persistence | 10 | **PASS** | 2.14s |
| [`test_health.py`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/backend/tests/test_health.py) | Root route discovery, `/health` response contract, model loading flag, `/model-info` metadata | 3 | **PASS** | 0.42s |
| [`test_main.py`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/backend/tests/test_main.py) | ASGI startup lifespan, OpenAPI docs mounting (`/docs`, `/redoc`), global exception handlers | 1 | **PASS** | 0.28s |
| [`test_model_service.py`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/backend/tests/test_model_service.py) | Feature transformation pipeline, schema contract validation, RobustScaler transforms, missing directory fail-safe | 3 | **PASS** | 0.45s |
| [`test_prediction.py`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/backend/tests/test_prediction.py) | Benign GET inference, brute-force POST detection, data exfiltration detection, negative latency rejection, invalid verb rejection, batch inference | 9 | **PASS** | 1.82s |
| [`test_telemetry.py`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/backend/tests/test_telemetry.py) | Telemetry ingestion lifecycle, `/traffic` feed, `/anomalies` incident queue, `/statistics` KPI consistency, limit/offset pagination | 2 | **PASS** | 0.88s |
| **Total Automated Pytest Tests** | **Full Backend Test Coverage** | **28** | **PASS (100%)** | **~6.0s** |

---

## 2. Empirical Performance & Latency Benchmarks

Measured using [`scripts/verify_phase7_e2e_benchmark.py`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/scripts/verify_phase7_e2e_benchmark.py) under Python 3.13 on Windows 11.

### A. Single Request Real-Time Scoring Latency (N=50 runs)
Each request executes: Pydantic parsing $\rightarrow$ 42-feature engineering $\rightarrow$ RobustScaler transform $\rightarrow$ Isolation Forest tree traversals (100 estimators) $\rightarrow$ SQLite atomic commit $\rightarrow$ JSON serialization.

| Metric | Measured Value | Target SLA | Compliance |
| :--- | :---: | :---: | :---: |
| **Mean Execution Latency** | **37.08 ms** | < 100 ms | **Exceeds Target** |
| **Median (P50) Latency** | **33.81 ms** | < 80 ms | **Exceeds Target** |
| **95th Percentile (P95)** | **51.60 ms** | < 120 ms | **Exceeds Target** |
| **99th Percentile (P99)** | **84.13 ms** | < 150 ms | **Exceeds Target** |

### B. Vectorized Batch Prediction Throughput
Evaluates multi-record ingestion using vectorized NumPy/Pandas batching and savepoint-isolated database commits:

| Batch Size | Total Processing Time (ms) | Ingestion Throughput (Records / Sec) |
| :---: | :---: | :---: |
| **10 records** | 162.73 ms | 61.5 records/sec |
| **50 records** | 694.98 ms | 71.9 records/sec |
| **100 records** | 1,552.26 ms | 64.4 records/sec |
| **250 records** | 2,732.74 ms | **91.5 records/sec** |

### C. Database Query & Analytics Latency (460+ stored records)
| Endpoint | Operation Executed | Query Speed |
| :--- | :--- | :---: |
| `GET /health` | Health verification & model memory check | 32.01 ms |
| `GET /statistics` | SQL aggregate calculations (`count`, `avg`, `GROUP BY`) | 26.65 ms |
| `GET /traffic?limit=50` | Indexed chronological telemetry retrieval with eager JOIN | 11.80 ms |
| `GET /anomalies?limit=50` | Filtered incident query (`is_anomaly == True`) | 10.78 ms |
| `GET /model-info` | Model metadata lookup from SQLite | 15.73 ms |

---

## 3. Machine Learning Model Validation

### A. Artifact Verification
- Champion model loaded: `models/isolation_forest.pkl` (851.9 KB).
- Fitted preprocessor loaded: `models/scaler.pkl` (1.0 KB, scikit-learn `RobustScaler`).
- Feature contract: `models/feature_columns.json` (42 exact columns).
- Metadata audited: `models/model_metadata.json`.

### B. Offline Benchmark Metrics vs. Real-World Expectations
The evaluation metrics below were computed on a strictly stratified 80/20 train/test partition (24,000 train / 6,000 test) using synthetic ground-truth labels:

```
+--------------------------------------------------------------+
|             ISOLATION FOREST BENCHMARK VALIDATION            |
+--------------------------+-----------------------------------+
| Metric                   | Measured Offline Benchmark Value  |
+--------------------------+-----------------------------------+
| Precision                | 99.88%                            |
| Recall                   | 99.78%                            |
| F1-Score                 | 99.83%                            |
| ROC-AUC                  | 99.98%                            |
| PR-AUC                   | 99.91%                            |
| False Positive Rate      | 0.02% (1 false alarm per 5,000)   |
| False Negative Rate      | 0.22%                             |
+--------------------------+-----------------------------------+
```

> [!IMPORTANT]
> **Anti-Leakage Confirmation:** Neither `is_anomaly` nor `anomaly_type` were present in the training feature matrix $X$. The unsupervised Isolation Forest was fit strictly on continuous and categorical telemetry variables.

### C. Decision Score Inversion Integrity
Scikit-learn's native `decision_function()` returns negative values for anomalies and positive values for inliers. AegisAPI inverts this score:
$$\text{Anomaly Score} = -\text{decision\_function}(X)$$
- **Nominal / Safe traffic:** Scores $< 0.00$
- **Low-threat deviations:** Scores $0.00 \le s < 0.07$
- **Medium threats:** Scores $0.07 \le s < 0.15$
- **High threats:** Scores $0.15 \le s < 0.25$
- **Critical exfiltration/bursts:** Scores $\ge 0.25$

---

## 4. Input Validation & Resilience Edge Cases

FastAPI's Pydantic v2 schemas rigorously intercept malformed, out-of-boundary, or malicious payloads before model inference:

| Boundary / Attack Scenario | Payload Submitted | Expected Result | Verified Result | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Invalid HTTP Verb** | `http_method: "EXPLOIT"` | HTTP 422 | HTTP 422 Unprocessable Content | **PASS** |
| **Negative Latency** | `response_time_ms: -100.0` | HTTP 422 | HTTP 422 Unprocessable Content | **PASS** |
| **Invalid Status Code** | `status_code: 999` | HTTP 422 | HTTP 422 Unprocessable Content | **PASS** |
| **Missing Required Route**| `{ "http_method": "GET" }` | HTTP 422 | HTTP 422 Unprocessable Content | **PASS** |
| **Negative Payload Bytes** | `request_size_bytes: -50` | HTTP 422 | HTTP 422 Unprocessable Content | **PASS** |
| **Empty Batch Payload** | `{ "records": [] }` | HTTP 422 | HTTP 422 Unprocessable Content | **PASS** |
| **Oversized Batch** | `len(records) > 500` | HTTP 422 | HTTP 422 Unprocessable Content | **PASS** |

---

## 5. Frontend Integration & Build Verification

- **Production Build:** Vite compiled 2,248 modules with zero errors.
- **Bundle Optimization:** Chunks code-split into `vendor.js` (160 KB), `charts.js` (425 KB), `icons.js` (16 KB), `index.js` (130 KB), and `index.css` (25 KB).
- **Responsive Layout:** Validated on mobile (375px), tablet (768px), and desktop (1440px).
- **Polling Resilience:** Confirmed polling timer (10s–30s) prevents overlapping concurrent requests using `useRef(isFetchingRef)` and cleanly clears timers upon unmount.
- **Fail-Safe Integrity:** When backend is offline, Topbar renders `BACKEND DISCONNECTED` and displays an actionable `ErrorState` card with a retry button instead of showing fabricated data.

---

## 6. End-to-End System Workflow Verification

1. **Submission:** User triggers a simulated attack in `TestPredictionModal` (`POST /api/v1/auth/login`, status 401, latency 65ms, RPM 210, failed requests 80).
2. **Backend Interception:** FastAPI parses and validates `TrafficRecordInput`.
3. **Feature Preprocessing:** `ModelService` engineers 42 numerical, cyclical, interaction, and one-hot features and scales them via `scaler.pkl`.
4. **Model Inference:** `isolation_forest.pkl` scores the sample (`score = +0.0655`, verdict: `Anomaly`, tier: `Low Threat`).
5. **Persistence:** `DatabaseService` atomically commits `TrafficEvent` and linked `AnomalyPrediction` to `backend/aegisapi.db`.
6. **Response & UI Refresh:** Backend returns HTTP 200 `PredictionResponse`. Frontend polls `/statistics`, incrementing total requests and anomalies, updating charts and tables in real time.
7. **Session Reconnection:** Reopened SQLite connections confirm all historical events and linked predictions survive process termination.

