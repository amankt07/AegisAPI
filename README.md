# AegisAPI – Intelligent API Traffic Anomaly Detection & Threat Monitoring Platform

![Architecture](https://img.shields.io/badge/Architecture-FastAPI%20%7C%20React%20%7C%20Scikit--Learn-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite%20%2B%20Tailwind-61DAFB?logo=react)
![ML](https://img.shields.io/badge/ML%20Model-Isolation%20Forest-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 1. Executive Summary & Objective

**AegisAPI** is an intelligent security operations and observability platform engineered to monitor, analyze, and detect anomalous API traffic patterns in real time. 

Modern API ecosystems face threats ranging from credential stuffing, token harvesting, and scraping bursts to distributed denial-of-service (DDoS) and unauthorized privilege discovery. Standard threshold-based firewalls often fail against subtle or distributed anomalous behaviors. 

AegisAPI addresses this by pairing an **unsupervised machine learning pipeline (Isolation Forest)** with a **high-throughput asynchronous API backend (FastAPI)** and an **interactive threat telemetry dashboard (React + Vite + Tailwind CSS + Recharts)**.

---

## 2. Core Capabilities & Architecture

```
                       +---------------------------------------+
                       |          Inbound API Traffic          |
                       +---------------------------------------+
                                          |
                                          v
+---------------------------------------------------------------------------------+
|                               Backend (FastAPI)                                 |
|  +--------------------+    +----------------------+    +---------------------+  |
|  | Traffic Ingestion  |--->| Feature Extractor &  |--->|   Isolation Forest  |  |
|  |     Endpoints      |    | Scaler Preprocessing |    |   Inference Engine  |  |
|  +--------------------+    +----------------------+    +---------------------+  |
|                                                                    |            |
|                                                                    v            |
|                                                        +---------------------+  |
|                                                        | Anomaly Scorer &    |  |
|                                                        | Threat Categorizer  |  |
|                                                        +---------------------+  |
+---------------------------------------------------------------------------------+
                                          |
                 +------------------------+------------------------+
                 |                                                 |
                 v                                                 v
+---------------------------------+               +---------------------------------+
|   Storage Layer (SQLite / ORM)  |               |     Dashboard (React + Vite)    |
| - Traffic Logs Table            |               | - Real-Time Latency & Rate View |
| - Threat / Incident Records     |               | - Anomaly Distribution (Recharts)|
+---------------------------------+               | - Incident Alert Feed           |
                                                  +---------------------------------+
```

- **Asynchronous Telemetry Ingestion:** Lightweight, non-blocking ingestion of API access logs (latency, status codes, payload dimensions, IP, routing signatures).
- **Unsupervised Anomaly Detection:** Utilizes Scikit-learn's Isolation Forest algorithm to detect zero-day anomalies and outliers without requiring labeled historical breach datasets.
- **Dynamic Threat Scoring:** Computes anomaly scores and categorizes behavior into threat tiers (`Low`, `Medium`, `High`, `Critical`).
- **Interactive Security Dashboard:** Live visualization of traffic trends, status code distributions, latency spikes, and flagged anomaly incidents.

---

## 3. Technology Stack

| Layer | Component | Technology |
|---|---|---|
| **Language & Runtimes** | Core Language | Python 3.10+ |
| **Data & Scientific** | Numerical & Tabular Processing | Pandas, NumPy |
| **Machine Learning** | Unsupervised Model & Pipeline | Scikit-learn (Isolation Forest), Joblib |
| **Backend & API** | Framework & Web Server | FastAPI, Uvicorn, Pydantic v2 |
| **Database** | Persistence & ORM | SQLite, SQLAlchemy v2 |
| **Frontend UI** | Build Tool & Library | React.js (Vite), JavaScript / TypeScript |
| **Styling & UI Kit** | CSS Framework | Tailwind CSS |
| **Data Visualization** | Charting Engine | Recharts |
| **Version Control & CI/CD** | Repository & Orchestration | Git, GitHub, Docker Compose |

---

## 4. Project Directory Structure

```
AegisAPI/
│
├── backend/                        # Backend service & API layer
│   ├── app/
│   │   ├── __init__.py             # Backend package initializer
│   │   ├── main.py                 # FastAPI application root & middleware setup
│   │   ├── database.py             # SQLite engine & database session manager
│   │   ├── models.py               # SQLAlchemy ORM schemas
│   │   ├── schemas.py              # Pydantic validation & transfer schemas
│   │   ├── routes/                 # Endpoint routers (traffic, analytics, alerts)
│   │   ├── services/               # Business logic & threat assessment service
│   │   └── ml/                     # ML pipelines, feature extractors & scoring logic
│   │
│   ├── tests/                      # Automated test suite (Pytest & TestClient)
│   │   ├── __init__.py
│   │   └── test_main.py            # Basic sanity and health checks
│   └── requirements.txt            # Python dependencies
│
├── frontend/                       # React.js + Vite + Tailwind CSS dashboard
│   └── .gitkeep                    # Directory tracking placeholder
│
├── data/                           # Data storage for experiments and models
│   ├── raw/                        # Raw API logs and uncleaned traffic datasets
│   │   └── .gitkeep
│   └── processed/                  # Normalized, feature-engineered datasets
│       └── .gitkeep
│
├── notebooks/                      # Jupyter notebooks for EDA and model exploration
│   └── .gitkeep
│
├── models/                         # Serialized ML artifacts (.joblib / .pkl)
│   └── .gitkeep
│
├── scripts/                        # Automation scripts (traffic generators, training scripts)
│   └── .gitkeep
│
├── docs/                           # Documentation, diagrams, and API specifications
│   └── .gitkeep
│
├── .gitignore                      # Git exclusion rules for Python, Node, data & secrets
├── README.md                       # Comprehensive project documentation
└── docker-compose.yml              # Container orchestration for local deployment
```

---

## 5. Directory Responsibilities

- **`backend/app/`**: Contains the complete FastAPI application following a modular architecture:
  - `main.py`: Entrypoint initializing the FastAPI app, registering middleware, and mounting routers.
  - `database.py`: Establishes the SQLite connection pool, session maker, and dependency injection `get_db()`.
  - `models.py`: Database table definitions for traffic events and anomaly records using SQLAlchemy.
  - `schemas.py`: Pydantic models for incoming log payloads, response formatting, and validation.
  - `routes/`: Houses specialized sub-routers (`traffic.py`, `analytics.py`, `threats.py`).
  - `services/`: Encapsulates business logic, alerting rules, and log orchestration.
  - `ml/`: Model loading, inference routines, feature preprocessing, and isolation scoring.
- **`backend/tests/`**: Unit and integration test suites using `pytest` and `httpx.AsyncClient`.
- **`frontend/`**: The web presentation tier created with Vite + React, Tailwind CSS, and Recharts.
- **`data/raw/` & `data/processed/`**: Staging directories for synthetic or collected API traffic datasets. Excluded from version control.
- **`notebooks/`**: Exploratory data analysis, hyperparameter tuning, and model evaluation notebooks.
- **`models/`**: Serialized Isolation Forest model binaries and feature scalers. Excluded from version control.
- **`scripts/`**: CLI utilities, traffic simulator scripts, and automated model retraining triggers.
- **`docs/`**: Architecture diagrams, sequence flows, and API reference documentation.

---

## 6. Quick Start & Verification

### Step 1: Initialize Git Repository
Run the following commands in the project root:
```bash
git init
git add .
git commit -m "chore: initialize AegisAPI directory structure and architecture"
```

### Step 2: Backend Virtual Environment Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate Python virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run test suite
pytest
```

### Step 3: Run FastAPI Application
```bash
# From the backend directory
uvicorn app.main:app --reload --port 8000
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to verify Swagger interactive documentation and the `/health` endpoint.

---

## 7. Machine Learning Methodology (Isolation Forest)

1. **Feature Engineering**:
   - `response_time_ms`: Execution latency.
   - `request_size_bytes` & `response_size_bytes`: Payload volume metrics.
   - `status_code`: Categorical status (2xx, 4xx, 5xx) encoded or weighted.
   - `request_frequency_1m`: Rolling request count per IP.
2. **Isolation Principle**:
   - Outliers are few and different, making them susceptible to early isolation along random axis-parallel splits.
   - The shorter the average path length in the ensemble trees, the higher the anomaly probability score.

---

## 8. License & Development Status

This project is licensed under the MIT License. Designed as an academic and engineering capstone for API security observability.

