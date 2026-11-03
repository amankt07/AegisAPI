# AegisAPI - Data Preprocessing & Exploratory Data Analysis (EDA) Report (Phase 2)

## 1. Executive Summary

Phase 2 of **AegisAPI** transforms the raw synthetic API traffic dataset (`data/raw/api_traffic.csv`) into a high-signal, model-ready feature matrix (`data/processed/X_features.csv`) paired with a separate ground-truth target vector (`data/processed/y_labels.csv`).

Key milestones accomplished:
1. **Zero Data Quality Deficits:** Verified zero missing values, zero duplicates, and complete RFC HTTP domain validity across 30,000 records.
2. **Comprehensive Exploratory Data Analysis:** Generated eight publication-grade visualizations in `docs/eda/` analyzing class balance, threat taxonomy, latency distributions, velocity bursts, error rates, and payload boundaries.
3. **Leakage-Free Feature Engineering:** Engineered 42 features spanning robust-scaled numerical metrics, cyclical temporal encodings, HTTP semantic flags, user-agent threat indicators, domain interaction ratios, and one-hot categorical encodings.
4. **Strict Isolation Protocol:** Completely isolated target labels (`is_anomaly`, `anomaly_type`) and raw identifiers (`source_ip`, `timestamp`) from the training matrix.

---

## 2. Dataset Inspection & Data Cleaning

### 2.1 Raw Dataset Audit
- **Input File:** `data/raw/api_traffic.csv`
- **Initial Shape:** 30,000 rows × 13 columns
- **Memory Footprint:** ~5.74 MB

### 2.2 Integrity & Boundary Assertions
Every record in the raw dataset underwent domain assertion checks:

| Assertion Check | Target Condition | Result | Notes |
|---|---|:---:|---|
| **Missing Values** | `count(NaN) == 0` | **PASSED** | 0 missing values across all 13 columns. |
| **Duplicate Rows** | `count(duplicates) == 0` | **PASSED** | 0 duplicate records found. |
| **Response Latency** | `response_time_ms >= 0` | **PASSED** | Minimum latency is `18.00 ms`. |
| **Request Size** | `request_size_bytes >= 0` | **PASSED** | Minimum request payload size is `50 B`. |
| **Response Size** | `response_size_bytes >= 0` | **PASSED** | Minimum response payload size is `80 B`. |
| **Request Velocity** | `requests_per_minute >= 0` | **PASSED** | Minimum RPM is `1 req/min`. |
| **Failure Velocity** | `failed_requests >= 0` | **PASSED** | Range `0` to `119`. |
| **RFC HTTP Status** | `100 <= status_code <= 599` | **PASSED** | All codes conform to standard HTTP specifications. |

### 2.3 Cleaning Transformations
- Converted `timestamp` from raw string format (`YYYY-MM-DD HH:MM:SS`) to timezone-naive pandas `datetime64[ns]` objects.
- Preserved all 30,000 records; zero records required pruning due to strict compliance.

---

## 3. Exploratory Data Analysis (EDA) Findings

Eight visualizations were produced and archived in `docs/eda/`:

### Chart 1: Normal vs. Anomalous Traffic Distribution (`01_normal_vs_anomalous_distribution.png`)
- **Distribution:** Exactly **25,500 normal records (85.0%)** and **4,500 anomalous records (15.0%)**.
- **Security Implications:** Mirrors enterprise API gateway telemetry where baseline traffic constitutes the vast majority, while anomalous incidents represent an actionable minority.

### Chart 2: Anomaly Type Distribution (`02_anomaly_type_distribution.png`)
- **Subtypes:** The 4,500 anomalies are partitioned into five equal classes of 900 records (3.0% of total each):
  - `Traffic Spike` (900)
  - `Brute Force` (900)
  - `High Error Rate` (900)
  - `Unusual Latency` (900)
  - `Large Payload` (900)
- **Security Implications:** Ensures multi-faceted model evaluation against volumetric, authentication, stability, latency, and data-exfiltration attack surfaces.

### Chart 3: Response Time Distribution (`03_response_time_distribution.png`)
- **Findings:** Normal API traffic adheres to a tight gamma distribution centered at `65–90 ms` (99% under `220 ms`). Anomalous traffic displays a pronounced heavy right tail with delays extending up to `14,991 ms` (15 seconds), typical of denial-of-service, slowloris connection holds, or unindexed database queries.

### Chart 4: Requests Per Minute (RPM) Velocity (`04_requests_per_minute_distribution.png`)
- **Findings:** Normal clients generate `1–45 req/min` (mean ~`14 req/min`). Traffic spike anomalies surge between `280` and `1,598 req/min`. A sharp discontinuity exists between normal human/client usage and scraping botnets.

### Chart 5: HTTP Status Code Breakdown (`05_status_code_distribution.png`)
- **Findings:** Normal traffic is dominated by `HTTP 200 OK` (26,753 occurrences) and `HTTP 201 Created`. Anomalous incidents cluster around `401 Unauthorized` (756 occurrences) and `403 Forbidden` (104) for brute-force attacks, `429 Too Many Requests` (299) for rate limiting, `500/502/503` (1,006 combined) for backend failures, and `504 Gateway Timeout` (280) for latency anomalies.

### Chart 6: Request Size vs. Response Time (`06_request_size_vs_response_time.png`)
- **Findings:** A log-log scatter reveals distinct clusters:
  1. *Normal cluster:* Compact cluster at `100–2,000 B` request size and `20–200 ms` response time.
  2. *Large Request Injections:* Horizontal outlier band with request sizes reaching `15 MB` (buffer overflow / rogue uploads).
  3. *Exfiltration Outliers:* Outbound payload sizes surging to `25 MB` accompanied by elevated transmission latency.

### Chart 7: Normal vs. Anomalous Latency Comparison (`07_normal_vs_anomalous_response_time.png`)
- **Findings:** Boxplot comparison on a logarithmic scale shows non-overlapping interquartile ranges (IQR). The median normal latency is `70.4 ms`, whereas the anomalous subset displays high variance with an upper fence stretching beyond `10,000 ms`.

### Chart 8: Traffic Volume Over Time (`08_traffic_volume_over_time.png`)
- **Findings:** Hourly resampling across the 7-day timeline confirms that anomalous records are continuously interleaved with benign traffic throughout all hours of the day, reflecting realistic production log streams.

---

## 4. Feature Engineering Architecture

A total of **42 model-ready features** were engineered for the training matrix:

### 4.1 Numerical Features & Robust Scaling (8 Features)
In cybersecurity anomaly detection, classical `StandardScaler` (z-score normalization) is vulnerable to distortion because extreme outliers (e.g. 15,000 ms latency or 25 MB payloads) artificially inflate the mean and variance.

We deployed **`sklearn.preprocessing.RobustScaler`**, which centers numerical features around the median and scales according to the **Interquartile Range (IQR = Q3 - Q1)**:

$$\text{Scaled Value} = \frac{X - \text{median}(X)}{\text{IQR}(X)}$$

Features scaled with RobustScaler:
1. `response_time_ms_scaled`
2. `request_size_bytes_scaled`
3. `response_size_bytes_scaled`
4. `requests_per_minute_scaled`
5. `failed_requests_scaled`
6. `failure_rate_scaled` ($\frac{\text{failed\_requests}}{\text{requests\_per\_minute} + 1.0}$)
7. `total_bytes_scaled` ($\text{request\_size} + \text{response\_size}$)
8. `byte_ratio_scaled` ($\frac{\text{response\_size}}{\text{request\_size} + 1.0}$)

### 4.2 Temporal & Cyclical Encodings (5 Features)
- `hour`: Discrete hour of day (`0–23`).
- `day_of_week`: Day index (`0` for Monday to `6` for Sunday).
- `is_weekend`: Binary flag (`1` for Saturday/Sunday, `0` for weekdays).
- `hour_sin` & `hour_cos`: Continuous sine/cosine circular transformation preserving the boundary continuity between `23:59` and `00:00`:

$$\text{hour\_sin} = \sin\left(\frac{2\pi \cdot \text{hour}}{24}\right), \quad \text{hour\_cos} = \cos\left(\frac{2\pi \cdot \text{hour}}{24}\right)$$

### 4.3 HTTP Semantic & Status Code Indicators (5 Features)
- `status_code`: Raw integer HTTP status code.
- `is_error`: Binary flag (`1` if `status_code >= 400`, else `0`).
- `is_client_error`: Binary flag (`1` if `400 <= status_code < 500`, else `0`).
- `is_server_error`: Binary flag (`1` if `status_code >= 500`, else `0`).
- `is_automation_agent`: Threat intelligence flag (`1` if User-Agent matches script/bot tool signatures: `curl`, `requests`, `Hydra`, `Go-http-client`, `Postman`, `Apache-HttpClient`; `0` for standard browsers).

### 4.4 One-Hot Encoded HTTP Methods (4 Features)
- `method_DELETE`
- `method_GET`
- `method_POST`
- `method_PUT`

### 4.5 One-Hot Encoded Endpoints (20 Features)
Complete one-hot expansion across all API routes:
- `endpoint_/api/v1/analytics`
- `endpoint_/api/v1/analytics/query`
- `endpoint_/api/v1/auth/login`
- `endpoint_/api/v1/auth/reset-password`
- `endpoint_/api/v1/auth/token`
- `endpoint_/api/v1/cart`
- `endpoint_/api/v1/cart/items`
- `endpoint_/api/v1/checkout/process`
- `endpoint_/api/v1/health`
- `endpoint_/api/v1/orders`
- `endpoint_/api/v1/orders/dump`
- `endpoint_/api/v1/payments`
- `endpoint_/api/v1/products`
- `endpoint_/api/v1/products/detail`
- `endpoint_/api/v1/reports`
- `endpoint_/api/v1/reports/export`
- `endpoint_/api/v1/search`
- `endpoint_/api/v1/upload`
- `endpoint_/api/v1/users/export`
- `endpoint_/api/v1/users/profile`

---

## 5. Data Leakage Prevention

To ensure valid and trustworthy model evaluation:
1. **Target Removal:** `is_anomaly` and `anomaly_type` were strictly omitted from `X_features.csv`.
2. **Identifier Removal:** `source_ip` was stripped to prevent the algorithm from simply memorizing attacker IP addresses rather than learning anomalous behavioral dynamics.
3. **Timestamp Removal:** Raw timestamp strings/datetimes were eliminated; only generalized cyclical and chronological features (`hour`, `day_of_week`, `is_weekend`, `hour_sin`, `hour_cos`) were retained.
4. **Target Isolation:** Ground truth was exported exclusively to `data/processed/y_labels.csv`.

---

## 6. Output Artifacts

| File Path | Dimensions | File Size | Description |
|---|:---:|:---:|---|
| [`data/processed/api_traffic_processed.csv`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/data/processed/api_traffic_processed.csv) | 30,000 × 59 | ~13.28 MB | Master processed dataset containing all original fields, engineered features, and target labels for downstream analytics. |
| [`data/processed/X_features.csv`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/data/processed/X_features.csv) | 30,000 × 42 | ~6.83 MB | Model-ready feature matrix without labels or identifiers. |
| [`data/processed/y_labels.csv`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/data/processed/y_labels.csv) | 30,000 × 1 | ~90 KB | Ground truth binary anomaly target vector (`0` or `1`). |
| [`docs/eda/`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/docs/eda) | 8 PNGs | ~2.72 MB | Visualizations for distribution, latency, status codes, and volume. |
| [`scripts/preprocess_data.py`](file:///c:/Users/amank/OneDrive/Desktop/AegisAPI/scripts/preprocess_data.py) | - | ~22 KB | End-to-end, reproducible CLI preprocessing pipeline script. |

---

## 7. How to Reproduce Preprocessing

```powershell
# From project root:
backend\.venv\Scripts\python.exe scripts\preprocess_data.py
```
Or with an active virtual environment:
```powershell
python scripts/preprocess_data.py
```

The script is idempotent, asserts all boundary criteria, saves all processed matrices, and validates row synchronization.

