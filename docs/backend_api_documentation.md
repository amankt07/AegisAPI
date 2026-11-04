# AegisAPI - Backend API Documentation (Phase 4)

## 1. Architectural Overview

The **AegisAPI Backend** is a high-throughput asynchronous REST API built with **FastAPI**, **Uvicorn**, **Pydantic v2**, and **Scikit-learn**. It acts as the intelligent security gateway and telemetry aggregation layer for the platform.

### Core Architectural Layers
```
                                 Client Request
                                       |
                                       v
                    +-------------------------------------+
                    |       FastAPI Application Core       |
                    |   (CORS, Validation, Error Handling) |
                    +-------------------------------------+
                                       |
                 +---------------------+---------------------+
                 |                                           |
                 v                                           v
+---------------------------------+         +---------------------------------+
|       ML Model Service          |         |      Traffic Event Service      |
| - Loads isolation_forest.pkl    |         | - Real-time In-memory Store     |
| - Loads scaler.pkl              |         | - Event Logging & Aggregations  |
| - Applies 42-feature transform  |         | - KPI Calculation & Threat Tiers|
| - Scores Anomaly & Threat Tier  |         +---------------------------------+
+---------------------------------+                          |
                 |                                           |
                 +---------------------+---------------------+
                                       |
                                       v
                            Structured JSON Response
```

---

## 2. API Endpoint Specifications

All endpoints are documented with OpenAPI specifications and accessible interactively via Swagger UI at `http://localhost:8000/docs` and Redoc at `http://localhost:8000/redoc`.

---

### 2.1 System & Health Endpoints

#### `GET /`
**Description:** Service discovery route providing operational status and documentation links.

- **Response `200 OK`:**
```json
{
  "service": "AegisAPI Telemetry & Anomaly Detection Backend",
  "version": "0.1.0",
  "status": "online",
  "documentation": "/docs",
  "redoc": "/redoc",
  "health_check": "/health",
  "model_loaded": true,
  "active_model": "Isolation Forest"
}
```

---

#### `GET /health`
**Description:** Health check reporting backend status, model loading status, and active feature dimensions.

- **Response `200 OK`:**
```json
{
  "status": "healthy",
  "service": "AegisAPI Backend",
  "version": "0.1.0",
  "model_loaded": true,
  "model_name": "Isolation Forest",
  "feature_count": 42
}
```

---

#### `GET /model-info`
**Description:** Exposes model audit metadata, hyperparameters, training partition size, and benchmark metrics.

- **Response `200 OK`:**
```json
{
  "model_name": "Isolation Forest",
  "algorithm": "sklearn.ensemble._iforest.IsolationForest",
  "training_date": "2026-11-04T09:35:36.438548",
  "feature_count": 42,
  "train_test_split": "80/20",
  "status": "production_champion",
  "hyperparameters": {
    "n_estimators": 100,
    "contamination": 0.15,
    "max_samples": "auto",
    "random_state": 42,
    "n_jobs": -1
  },
  "evaluation_metrics": {
    "Accuracy": 0.961,
    "Precision": 0.8588,
    "Recall": 0.8856,
    "F1-Score": 0.8720,
    "ROC-AUC": 0.9904,
    "PR-AUC": 0.9567,
    "False Positive Rate": 0.0257
  },
  "score_interpretation": "Continuous Anomaly Score = -1 * decision_function(X). Negative values indicate normal baseline traffic. Values >= 0 indicate anomalous deviations. Higher values represent severe threats.",
  "feature_names": [
    "response_time_ms_scaled",
    "request_size_bytes_scaled",
    "...",
    "endpoint_/api/v1/users/profile"
  ]
}
```

---

### 2.2 Anomaly Inference Endpoints

#### `POST /predict`
**Description:** Real-time single-record API traffic anomaly inspection. Validates input, transforms into 42 features via `RobustScaler`, executes Isolation Forest, and updates in-memory telemetry buffers.

- **Request Body:**
```json
{
  "endpoint": "/api/v1/products",
  "http_method": "GET",
  "status_code": 200,
  "response_time_ms": 68.42,
  "request_size_bytes": 180,
  "response_size_bytes": 3400,
  "requests_per_minute": 14,
  "failed_requests": 0,
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "source_ip": "192.168.1.45"
}
```

- **Response `200 OK` (Normal Example):**
```json
{
  "is_anomaly": 0,
  "prediction_label": "Normal",
  "anomaly_score": -0.1082,
  "threat_level": "Safe",
  "model_name": "Isolation Forest",
  "timestamp": "2026-11-04T04:35:10.123456Z",
  "details": {
    "endpoint": "/api/v1/products",
    "http_method": "GET",
    "status_code": 200,
    "response_time_ms": 68.42,
    "raw_decision_score": 0.1082,
    "score_direction": "higher_is_more_anomalous"
  }
}
```

- **Response `200 OK` (Anomaly Attack Example):**
```json
{
  "is_anomaly": 1,
  "prediction_label": "Anomaly",
  "anomaly_score": 0.0812,
  "threat_level": "Medium Threat",
  "model_name": "Isolation Forest",
  "timestamp": "2026-11-04T04:35:12.654321Z",
  "details": {
    "endpoint": "/api/v1/auth/login",
    "http_method": "POST",
    "status_code": 401,
    "response_time_ms": 55.0,
    "raw_decision_score": -0.0812,
    "score_direction": "higher_is_more_anomalous"
  }
}
```

---

#### `POST /predict/batch`
**Description:** Evaluates up to 500 traffic records in a vectorized call.

- **Request Body:**
```json
{
  "records": [
    {
      "endpoint": "/api/v1/products",
      "http_method": "GET",
      "status_code": 200,
      "response_time_ms": 60.0
    },
    {
      "endpoint": "/api/v1/auth/login",
      "http_method": "POST",
      "status_code": 401,
      "response_time_ms": 45.0,
      "requests_per_minute": 220,
      "failed_requests": 90,
      "user_agent": "Hydra/9.5"
    }
  ]
}
```

- **Response `200 OK`:**
```json
{
  "total_records": 2,
  "anomalies_detected": 1,
  "anomaly_rate_percent": 50.0,
  "model_name": "Isolation Forest",
  "predictions": [
    {
      "is_anomaly": 0,
      "prediction_label": "Normal",
      "anomaly_score": -0.1091,
      "threat_level": "Safe",
      "model_name": "Isolation Forest",
      "timestamp": "2026-11-04T04:36:00Z"
    },
    {
      "is_anomaly": 1,
      "prediction_label": "Anomaly",
      "anomaly_score": 0.0825,
      "threat_level": "Medium Threat",
      "model_name": "Isolation Forest",
      "timestamp": "2026-11-04T04:36:00Z"
    }
  ]
}
```

---

### 2.3 Telemetry & Observability Endpoints

#### `GET /traffic`
**Description:** Retrieves historical API traffic events (newest first) with pagination.

- **Query Parameters:** `limit` (default: 50, max: 500), `offset` (default: 0).
- **Response `200 OK`:**
```json
[
  {
    "id": 105,
    "timestamp": "2026-11-04T04:35:10Z",
    "source_ip": "192.168.1.45",
    "endpoint": "/api/v1/products",
    "http_method": "GET",
    "status_code": 200,
    "response_time_ms": 68.42,
    "request_size_bytes": 180,
    "response_size_bytes": 3400,
    "requests_per_minute": 14,
    "failed_requests": 0,
    "user_agent": "Mozilla/5.0...",
    "is_anomaly": 0,
    "prediction_label": "Normal",
    "anomaly_score": -0.1082,
    "threat_level": "Safe"
  }
]
```

---

#### `GET /anomalies`
**Description:** Retrieves security incidents flagged by the model with pagination.

- **Query Parameters:** `limit` (default: 50, max: 500), `offset` (default: 0).
- **Response `200 OK`:**
```json
[
  {
    "id": 106,
    "timestamp": "2026-11-04T04:35:12Z",
    "source_ip": "198.51.100.12",
    "endpoint": "/api/v1/auth/login",
    "http_method": "POST",
    "status_code": 401,
    "response_time_ms": 55.0,
    "request_size_bytes": 240,
    "response_size_bytes": 180,
    "requests_per_minute": 180,
    "failed_requests": 85,
    "anomaly_score": 0.0812,
    "threat_level": "Medium Threat"
  }
]
```

---

#### `GET /statistics`
**Description:** Returns real-time aggregated security metrics for the React dashboard.

- **Response `200 OK`:**
```json
{
  "total_processed_requests": 1420,
  "normal_requests": 1210,
  "anomalous_requests": 210,
  "anomaly_percentage": 14.79,
  "average_response_time_ms": 86.45,
  "http_error_count": 185,
  "threat_level_distribution": {
    "Safe": 1210,
    "Low Threat": 15,
    "Medium Threat": 145,
    "High Threat": 42,
    "Critical Threat": 8
  },
  "top_anomalous_endpoints": {
    "/api/v1/auth/login": 92,
    "/api/v1/products": 45,
    "/api/v1/checkout/process": 32,
    "/api/v1/users/export": 24,
    "/api/v1/reports/export": 17
  }
}
```

---

## 3. Threat Level Categorization Matrix

AegisAPI translates continuous anomaly scores into actionable operational security tiers:

$$\text{Anomaly Score} = -1 \times \text{decision\_function}(X)$$

| Threat Tier | Score Range | Operational Meaning & Recommended SOC Action |
|:---:|:---:|---|
| **Safe** | $\text{Score} < 0.00$ | Baseline normal traffic. Zero action required. |
| **Low Threat** | $0.00 \le \text{Score} < 0.07$ | Minor statistical variation (e.g. minor latency bump). Monitor passively. |
| **Medium Threat** | $0.07 \le \text{Score} < 0.15$ | Clear anomaly (e.g. repeated 401 login attempts, 500 server crash). Trigger security telemetry warning. |
| **High Threat** | $0.15 \le \text{Score} < 0.25$ | Volumetric traffic spike (> 1,000 RPM) or large exfiltration dump. Flag for immediate rate-limiting or IP isolation. |
| **Critical Threat** | $\text{Score} \ge 0.25$ | Severe multi-vector attack or massive denial-of-service. Trigger automated circuit breaking. |

*Note: Raw anomaly scores are unbounded continuous numbers, not probabilities.*

---

## 4. Error Handling and Security Measures

1. **Validation Constraints (HTTP 422):**
   - Negative response times, negative payload sizes, or invalid HTTP methods are rejected at the edge with clean, descriptive JSON diagnostics.
2. **Batch Ingestion Safeguards:**
   - Maximum batch payload limit is enforced at **500 items** to prevent memory exhaustion and denial-of-service on the backend.
3. **Information Disclosure Prevention:**
   - Internal file system paths, database credentials, and raw stack traces are masked from all API responses.
4. **CORS Headers:**
   - Pre-configured to support local Vite frontend development (`http://localhost:5173`).
5. **No Block Assumption:**
   - The platform acts as an anomaly detection and telemetry engine; it does not claim to execute in-kernel packet drops or autonomous blocking.

---

## 5. How to Run and Test

### 5.1 Starting the FastAPI Development Server
```powershell
# From the project root:
cd backend

# Activate virtual environment
.venv\Scripts\activate

# Start Uvicorn with auto-reload
uvicorn app.main:app --reload --port 8000
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

### 5.2 Executing Automated Pytest Suite
```powershell
# From the backend directory
pytest -v tests/
```
All 18 unit and integration tests validate health, single prediction, batch prediction, validation errors, telemetry logging, and model service fail-safes.

