# AegisAPI: Intelligent API Traffic Anomaly Detection & Threat Monitoring Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite%205-61DAFB?logo=react)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS%203-38B2AC?logo=tailwindcss)](https://tailwindcss.com)
[![Recharts](https://img.shields.io/badge/Visualizations-Recharts%202.13-FF6384?logo=chartdotjs)](https://recharts.org)
[![SQLite](https://img.shields.io/badge/Persistence-SQLite%203%20%2B%20SQLAlchemy%202.0-003B57?logo=sqlite)](https://sqlite.org)
[![Scikit-Learn](https://img.shields.io/badge/ML%20Engine-Isolation%20Forest%20(42%20Features)-F7931E?logo=scikitlearn)](https://scikit-learn.org)
[![Test Suite](https://img.shields.io/badge/Tests-28%2F28%20Passed%20(100%25)-brightgreen)](docs/testing_report.md)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

---

## 1. Executive Summary & Problem Statement

**AegisAPI** is an enterprise-grade cybersecurity telemetry, anomaly detection, and operational observability platform designed to monitor RESTful APIs against distributed denial-of-service bursts, credential brute-force attacks, data exfiltration dumps, abnormal latency degradation, and server crash cascades.

### The Security Challenge
Modern cloud microservices face sophisticated, multi-vector threats that standard signature-based Web Application Firewalls (WAFs) and static rate limiters fail to detect:
1. **Multi-Variate Threat Signatures:** An attack may present a standard HTTP status (`200 OK`) while concealing an abnormally large data dump (exfiltration), or normal latency during distributed low-frequency credential stuffing.
2. **Absence of Pre-Labeled Breach Data:** Production API telemetry rarely contains ground-truth breach labels. Supervised models overfit to known attack signatures and fail against novel zero-day exploits.
3. **Low-Latency Operational Thresholds:** Security telemetry inspection must execute in sub-50 ms to avoid degrading application throughput.

AegisAPI solves these challenges by deploying an **unsupervised machine learning engine (Isolation Forest)** fitted across a **42-dimensional feature space**, integrated with a high-throughput **FastAPI** backend, **SQLite** transactional persistence, and a cybersecurity **React SOC Dashboard**.

---

## 2. End-to-End System Architecture

```
                                  +---------------------------------------+
                                  |         Inbound Client Traffic        |
                                  |  (Web Clients, Mobile Apps, Scripts)  |
                                  +---------------------------------------+
                                                      |
                                                      v
+---------------------------------------------------------------------------------------------------+
|                                      AegisAPI Backend (FastAPI)                                   |
|                                                                                                   |
|  +---------------------------+      +-------------------------------+      +-------------------+  |
|  | Traffic Ingestion Router  | ---> | Feature Preprocessing Engine  | ---> | Isolation Forest  |  |
|  | (POST /predict)           |      | (RobustScaler & Cyclical Enc) |      | Inference Model   |  |
|  +---------------------------+      +-------------------------------+      +-------------------+  |
|               |                                                                      |            |
|               |                                                                      v            |
|               |                                                            +-------------------+  |
|               |                                                            | Anomaly Scorer &  |  |
|               |                                                            | Threat Classifier |  |
|               |                                                            +-------------------+  |
|               v                                                                      |            |
|  +-----------------------------------------------------------------------------------+---------+  |
|  |                                  Persistence & Analytics Layer                              |  |
|  |                   (SQLAlchemy 2.0 ORM -> SQLite Database Engine: aegisapi.db)                |  |
|  +---------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
                                                      |
                                                      v
+---------------------------------------------------------------------------------------------------+
|                                Frontend Threat Dashboard (React + Vite)                           |
|                                                                                                   |
|  +---------------------------+      +-------------------------------+      +-------------------+  |
|  | 6 Core KPI Metric Cards   |      | Interactive Recharts Suite    |      | Threat Incidents  |  |
|  | (Requests, Anomalies, Lat)|      | (Velocity, Donut, Latency)    |      | Live Alert Queue  |  |
|  +---------------------------+      +-------------------------------+      +-------------------+  |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Key Capabilities & Features

- **Unsupervised Anomaly Scoring:** Uses an Isolation Forest ensemble (100 estimators, contamination: 0.15) to detect zero-day deviations without requiring labeled attack datasets.
- **42-Dimensional Feature Engineering:** Automatically computes temporal cyclical sine/cosine encodings, request/response payload ratios, failure velocity scores, status error flags, and one-hot endpoint vectors.
- **Sub-40ms Inference & Storage:** Measured mean latency of **37.08 ms** (P50: **33.81 ms**, P95: **51.60 ms**) for full feature extraction, inference, and SQLite transaction persistence.
- **High-Throughput Vectorized Batching:** Ingests up to 500 records per request with measured throughput exceeding **90 records/second**.
- **Transactional SQLite Persistence:** Multi-threaded SQLAlchemy ORM managing `traffic_events`, `anomaly_predictions`, and `model_information` with 1-to-1 cascading integrity.
- **SOC Analyst React Dashboard:** Cybersecurity interface with dark navy styling (`#080C14`), 6 live KPI metric cards, 5 Recharts visualizations, and full pagination/filtering.
- **Interactive Simulation Drawer:** Built-in modal allowing operators to inject simulated threat vectors (*Benign Catalog*, *Auth Brute-Force*, *Data Exfiltration*, *Volumetric DDoS*) to verify real-time scoring.
- **Automated Healthchecks & Zero-Falsification:** Configurable polling (10s–30s) with request overlap prevention. Displays explicit error/empty states when the backend is offline.

---

## 4. Machine Learning Benchmarks & Offline Validation

Three unsupervised outlier detection algorithms were evaluated on a strictly stratified 80/20 train/test partition (24,000 train / 6,000 held-out test records):

| Algorithm Evaluated | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | False Positive Rate | Inference Speed |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Isolation Forest (Champion)** | **99.88%** | **99.78%** | **99.83%** | **99.98%** | **99.91%** | **0.02%** | **0.063 ms / sample** |
| Local Outlier Factor (LOF) | 99.44% | 99.33% | 99.39% | 99.63% | 99.39% | 0.08% | 0.812 ms / sample |
| One-Class SVM (OC-SVM) | 98.79% | 98.44% | 98.62% | 99.17% | 98.68% | 0.18% | 1.845 ms / sample |

```
+---------------------------------------------------------------------------------+
| Anomaly Score Interpretation (Inverted Decision Function):                     |
|   Score < 0.00         -> Safe / Nominal Baseline                               |
|   0.00 <= Score < 0.07 -> Low Threat Deviation                                  |
|   0.07 <= Score < 0.15 -> Medium Threat (e.g., Latency Spike / Moderate Rate)   |
|   0.15 <= Score < 0.25 -> High Threat (e.g., Auth Login Brute Force)            |
|   Score >= 0.25        -> Critical Threat (e.g., Mass Data Exfiltration Burst)  |
+---------------------------------------------------------------------------------+
```

> [!NOTE]
> All evaluation benchmarks reflect offline validation against synthetic ground-truth test data. In compliance with academic rigor, metrics are labeled as offline evaluation results rather than live dynamic accuracy.

---

## 5. Technology Stack Matrix

| Domain | Technology / Library | Version | Purpose |
| :--- | :--- | :---: | :--- |
| **Backend Framework** | FastAPI | `^0.110.0` | Asynchronous high-throughput ASGI REST microservice |
| **ASGI Web Server** | Uvicorn | `^0.28.0` | Production ASGI web server |
| **Data Contracts** | Pydantic v2 | `^2.6.0` | Request validation, range boundaries, and schemas |
| **Database & ORM** | SQLite 3 / SQLAlchemy | `^2.0.28` | Multi-threaded ORM with foreign key cascades |
| **Machine Learning** | Scikit-Learn | `^1.4.0` | Isolation Forest ensemble model & RobustScaler |
| **Data Science** | NumPy & Pandas | `^1.26 / ^2.2` | Matrix manipulations & cyclical transformations |
| **Frontend SPA** | React | `^18.3.1` | Component-driven UI architecture |
| **Build Tool** | Vite | `^5.4.9` | Optimized frontend bundling & HMR |
| **CSS Architecture** | Tailwind CSS | `^3.4.14` | Cybersecurity SOC palette (`#080C14` / `#0D1322`) |
| **Analytics Charts** | Recharts | `^2.13.0` | SVG responsive charts (Area, Donut, Line, Bar) |
| **HTTP Client** | Axios | `^1.7.7` | Intercepted client with timeouts and error handling |
| **Routing** | React Router DOM | `^6.27.0` | Client-side SPA routing and navigation |
| **Test Automation** | Pytest & AnyIO | `^8.0 / ^4.16` | Automated backend testing suite (28/28 passed) |

---

## 6. Project Directory Structure

```text
AegisAPI/
├── backend/
│   ├── aegisapi.db                     # SQLite persistence database (auto-created)
│   ├── Dockerfile                      # Multi-stage Python 3.11-slim production container
│   ├── requirements.txt                # Python backend dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI entrypoint, lifespan, CORS & handlers
│   │   ├── database.py                 # SQLite engine, SessionLocal & idempotent init_db
│   │   ├── models.py                   # SQLAlchemy ORM schemas (TrafficEvent, AnomalyPrediction, ModelInfo)
│   │   ├── schemas.py                  # Pydantic validation contracts
│   │   ├── routes/                     # Modular API route controllers
│   │   │   ├── __init__.py
│   │   │   ├── health.py               # GET /health service status
│   │   │   ├── prediction.py           # POST /predict & POST /predict/batch
│   │   │   ├── traffic.py              # GET /traffic & GET /anomalies feeds
│   │   │   ├── statistics.py           # GET /statistics SQL aggregate KPIs
│   │   │   └── model_info.py           # GET /model-info audit metadata
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── model_service.py        # ML loader, 42-feature preprocessor & scoring
│   │       ├── database_service.py     # Transactional persistence, savepoints & SQL queries
│   │       └── traffic_service.py      # Telemetry store & in-memory buffer
│   └── tests/
│       ├── test_database.py            # SQLite connection, cascades, rollbacks & persistence
│       ├── test_health.py              # Health check & model status tests
│       ├── test_main.py                # App startup & docs mounting tests
│       ├── test_model_service.py       # Unit tests for transforms & error handling
│       ├── test_prediction.py          # Single & batch prediction boundary tests
│       └── test_telemetry.py           # Telemetry feed & KPI aggregation tests
│
├── frontend/                           # React 18 + Vite 5 cybersecurity SOC dashboard
│   ├── Dockerfile                      # Multi-stage Nginx Alpine production container
│   ├── nginx.conf                      # Nginx SPA routing & gzip configuration
│   ├── package.json                    # Frontend dependencies & build scripts
│   ├── vite.config.js                  # Vite configuration & code-split chunks
│   ├── tailwind.config.js              # Dark navy cyber theme palette
│   ├── .env.example                    # API base URL & polling template
│   ├── index.html                      # HTML5 template with Inter & JetBrains Mono
│   └── src/
│       ├── main.jsx                    # React DOM mount
│       ├── App.jsx                     # Router, layout wrapper & polling engine
│       ├── index.css                   # Tailwind imports & radar animations
│       ├── services/api.js             # Centralized Axios client
│       ├── components/                 # Reusable UI component library
│       │   ├── layout/                 # Sidebar, Topbar & Layout
│       │   ├── common/                 # MetricCard, DataTable, ThreatBadge, States
│       │   ├── charts/                 # Recharts volume, ratio, latency & endpoints
│       │   └── modals/                 # TestPredictionModal simulation drawer
│       └── pages/                      # Dashboard, Anomalies, Traffic, ModelInfo
│
├── data/
│   ├── raw/api_traffic.csv             # Raw 30,000 synthetic records (5.74 MB)
│   └── processed/
│       ├── X_features.csv              # Model-ready feature matrix (30,000 x 42, 6.83 MB)
│       └── y_labels.csv                # Binary ground-truth target vector (90 KB)
│
├── models/
│   ├── isolation_forest.pkl            # Champion model artifact (851.9 KB)
│   ├── scaler.pkl                      # Fitted RobustScaler preprocessor (1.0 KB)
│   ├── feature_columns.json            # 42-feature schema contract (3.0 KB)
│   └── model_metadata.json             # Hyperparameters, evaluation metrics & config (1.2 KB)
│
├── scripts/
│   ├── generate_dataset.py             # Phase 1 dataset generator script
│   ├── preprocess_data.py              # Phase 2 cleaning, EDA & feature pipeline
│   ├── train_model.py                  # Phase 3 model training & benchmarking script
│   ├── evaluate_model.py               # Phase 3 standalone model evaluator
│   ├── verify_phase5_database.py       # Phase 5 SQLite persistence verification script
│   ├── verify_phase6_frontend.py       # Phase 6 Frontend integration & build test script
│   └── verify_phase7_e2e_benchmark.py  # Phase 7 E2E benchmark & reliability script
│
├── docs/
│   ├── PROJECT_REPORT.md               # Master living capstone project report
│   ├── system_architecture.md          # Technical design & sequence specifications
│   ├── testing_report.md               # Comprehensive testing & benchmark report
│   ├── deployment_guide.md             # Operations & multi-container Docker guide
│   ├── dataset_documentation.md        # Technical dataset documentation (Phase 1)
│   ├── preprocessing_report.md         # Data preprocessing report (Phase 2)
│   ├── model_training_report.md        # Model training & benchmarking report (Phase 3)
│   ├── backend_api_documentation.md    # FastAPI backend API specifications (Phase 4)
│   ├── database_documentation.md       # SQLite schema, tables & queries (Phase 5)
│   └── frontend_documentation.md       # Frontend SOC architecture & guide (Phase 6)
│
├── docker-compose.yml                  # Multi-container orchestration with healthchecks
├── .gitignore                          # Strict exclusion rules for virtualenvs, node_modules, DBs
└── README.md                           # Master repository documentation (this file)
```

---

## 7. Quickstart & Installation Instructions

### Option A: Local Bare-Metal Execution

#### Prerequisites
- Python 3.11+
- Node.js 18+ & npm 9+

#### Terminal 1: Start Backend Microservice
```powershell
# 1. Clone repository
git clone https://github.com/amank/AegisAPI.git
cd AegisAPI/backend

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Run automated test suite (28 tests)
pytest tests/ -v

# 5. Launch FastAPI backend service
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend Swagger OpenAPI docs accessible at:* **`http://127.0.0.1:8000/docs`**

#### Terminal 2: Start React Frontend Dashboard
```powershell
# 1. Navigate to frontend directory
cd AegisAPI/frontend

# 2. Install dependencies
npm install

# 3. Launch Vite development server
npm run dev
```
*Frontend SOC Dashboard accessible at:* **`http://localhost:5173`**

---

### Option B: Multi-Container Docker Compose

```powershell
# Build and run containers in detached mode
docker compose up -d --build

# Verify container health
docker compose ps
```
- Frontend Dashboard: `http://localhost:5173`
- Backend API Docs: `http://localhost:8000/docs`

---

## 8. Production API Endpoint Specifications

| Method & Route | Route Category | Request Body | Description |
| :--- | :--- | :--- | :--- |
| `GET /` | Root | None | Service discovery, online status, and Swagger links. |
| `GET /health` | Observability | None | System status, version, and model loading state. |
| `POST /predict` | Detection | `TrafficRecordInput` | Real-time single API anomaly detection and SQLite persistence. |
| `POST /predict/batch` | Detection | `BatchTrafficInput` | Vectorized batch inference (up to 500 records). |
| `GET /traffic` | Telemetry | `limit`, `offset` | Chronological recent traffic events with pagination. |
| `GET /anomalies` | Incidents | `limit`, `offset` | Filtered security incident queue (`is_anomaly == True`). |
| `GET /statistics` | Analytics | None | Live SQL aggregate KPIs (total, anomaly %, latency, error counts). |
| `GET /model-info` | Governance | None | Active champion model metadata, hyperparameters, and offline metrics. |

### Sample Inference Request:
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "endpoint": "/api/v1/auth/login",
       "http_method": "POST",
       "status_code": 401,
       "response_time_ms": 65.0,
       "request_size_bytes": 240,
       "response_size_bytes": 160,
       "requests_per_minute": 220,
       "failed_requests": 85,
       "source_ip": "198.51.100.99",
       "user_agent": "Hydra/9.5"
     }'
```

### Sample Inference Response:
```json
{
  "is_anomaly": 1,
  "prediction_label": "Anomaly",
  "anomaly_score": 0.0688,
  "threat_level": "Low Threat",
  "model_name": "Isolation Forest",
  "timestamp": "2026-11-04T15:16:55.123456Z"
}
```

---

## 9. Known Operational Limitations & Future Roadmap

### Prototype Scope & Limitations
- **Defensive Monitoring Prototype:** AegisAPI is an intelligent **telemetry monitoring and anomaly detection system**. It does **not** terminate network connections or execute inline firewall packet dropping.
- **Single-Node SQLite Persistence:** SQLite is optimized for concurrent reads with single-writer serialization (`check_same_thread=False`). Extremely high-concurrency enterprise deployments should substitute PostgreSQL via SQLAlchemy connection strings.
- **Synthetic Training Benchmark:** While grounded in real-world microservice traffic distributions, real production deployments should incrementally retrain models against domain-specific traffic logs.

### Future Roadmap
1. **Dynamic Model Drift Detection:** Implement Kolmogorov-Smirnov statistical testing to flag distribution drift over rolling 30-day windows.
2. **PostgreSQL / TimescaleDB Migration:** Enable distributed hypertable time-series storage for sustained high-throughput streams.
3. **Automated Incident Response Webhooks:** Dispatch PagerDuty / Slack notifications when high or critical threats exceed configurable anomaly thresholds.

---

## 10. License & Academic Attribution

This project is released under the **MIT License**. Engineered for academic evaluation, research demonstration, and cybersecurity defense prototyping.
