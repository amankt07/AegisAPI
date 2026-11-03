# AegisAPI Dataset Documentation (Phase 1)

## 1. Dataset Overview & Purpose

The **AegisAPI Traffic Dataset** (`data/raw/api_traffic.csv`) is a synthetic, high-fidelity security dataset representing API gateway access logs over a continuous multi-day period.

Its primary purpose is to provide a realistic benchmark for training, evaluating, and fine-tuning unsupervised machine learning models (specifically **Isolation Forest**) for **API anomaly detection, threat identification, and traffic telemetry**.

Traditional rule-based web application firewalls (WAFs) struggle with multi-variate anomalous behavior. This dataset simulates both normal consumer/client API usage and five prevalent classes of API attacks and operational anomalies without relying on artificial indicators.

---

## 2. Dataset Dimensions & Volume

| Dimension | Value | Notes |
|---|---|---|
| **Total Records** | **30,000** | Ground-truth labeled synthetic API requests |
| **Total Features** | **13** | 11 telemetry features + 2 target labels |
| **Time Span** | **7 Days** | `2026-10-25 00:00:00` to `2026-10-31 23:59:59` |
| **Missing Values** | **0** | Clean, zero missing values across all columns |
| **Duplicates** | **0** | Zero duplicate records |
| **File Format** | **CSV** | Stored at `data/raw/api_traffic.csv` (~5.74 MB) |

---

## 3. Class & Anomaly Distribution

The dataset adheres strictly to an **85% Normal / 15% Anomalous** distribution. The 4,500 anomalous records are distributed evenly across 5 distinct threat categories (900 records each):

| Ground-Truth Label (`is_anomaly`) | Subcategory (`anomaly_type`) | Record Count | Percentage of Total | Description |
|:---:|:---:|:---:|:---:|---|
| **0** | **Normal** | **25,500** | **85.00%** | Standard API access, healthy response times, low error frequency, normal request sizes. |
| **1** | **Traffic Spike** | **900** | **3.00%** | Sudden extreme frequency bursts (280–1,600 req/min), automated scraping or DoS flood. |
| **1** | **Brute Force** | **900** | **3.00%** | Rapid repetitive credential guessing targeting `/api/v1/auth/*`, high 401/403 and high failure counts. |
| **1** | **High Error Rate** | **900** | **3.00%** | Server crash loops and backend unavailabilities dominated by HTTP 500, 502, and 503. |
| **1** | **Unusual Latency** | **900** | **3.00%** | Severe execution delays (2,500 ms – 15,000 ms), unindexed database queries, slowloris or 504 timeouts. |
| **1** | **Large Payload** | **900** | **3.00%** | Data exfiltration dumps (500 KB – 25 MB responses) or oversized payload/buffer overflow injections (150 KB – 15 MB requests). |
| **Total** | | **30,000** | **100.00%** | |

---

## 4. Feature Dictionary

| # | Column Name | Data Type | Example Value | Description & Domain Range |
|---|---|---|---|---|
| 1 | `timestamp` | String (`YYYY-MM-DD HH:MM:SS`) | `2026-10-25 04:12:35` | The chronological timestamp when the request reached the API gateway. Spans 7 continuous days. |
| 2 | `source_ip` | String | `192.168.1.45`, `198.51.100.22` | The synthetic IPv4 address originating the request. Normal traffic uses private pools (`192.168.x.x`, `10.x.x.x`); attacks originate from concentrated synthetic external pools (`198.51.100.x`, `203.0.113.x`). |
| 3 | `endpoint` | String | `/api/v1/products`, `/api/v1/auth/login` | The destination API endpoint path. |
| 4 | `http_method` | String | `GET`, `POST`, `PUT`, `DELETE` | Standard HTTP verb used for the request. |
| 5 | `status_code` | Integer | `200`, `201`, `401`, `429`, `500`, `504` | HTTP response code returned by the gateway or upstream server. |
| 6 | `response_time_ms` | Float | `68.42` | End-to-end latency in milliseconds. Normal is 18–240 ms; anomalous latency spans up to 15,000 ms. |
| 7 | `request_size_bytes` | Integer | `320`, `2458920` | Size of the inbound HTTP request body and headers in bytes. |
| 8 | `response_size_bytes`| Integer | `3450`, `12405820` | Size of the outbound HTTP response payload in bytes. |
| 9 | `requests_per_minute`| Integer | `14`, `840` | Rolling request velocity from the originating `source_ip` per minute. Normal range: 1–45; spikes reach up to 1,600. |
| 10| `failed_requests` | Integer | `0`, `45`, `92` | Number of failed requests (4xx/5xx) from the source IP within the current evaluation window. |
| 11| `user_agent` | String | `Mozilla/5.0...`, `curl/8.4.0` | Client user-agent string. Normal traffic mimics desktop/mobile browsers; anomalies include automation tools (`Hydra/9.5`, `python-requests`, `curl`, `Go-http-client`). |
| 12| `is_anomaly` | Integer (`0` or `1`) | `0`, `1` | **Ground-truth label** for evaluation: `0` for normal traffic, `1` for anomalous traffic. **Must NOT be used as a model input feature.** |
| 13| `anomaly_type` | String | `Normal`, `Traffic Spike`, `Brute Force` | Specific classification category. **Must NOT be used as a model input feature.** |

---

## 5. Anomaly Pattern Deep Dive

### A. Traffic Spike
- **Mechanism:** Bot-driven scraping, automated indexing bursts, or volumetric denial-of-service attempts.
- **Key Indicators:**
  - `requests_per_minute` surges to **280 – 1,600 req/min** (normal is < 45).
  - Repetitive queries targeting product listings, search queries, or orders.
  - Server rate-limiting responses (`HTTP 429 Too Many Requests`) or capacity depletion (`HTTP 503 Service Unavailable`).
  - Elevated `failed_requests` (3–25) and slightly elevated response times (140–750 ms) under load.

### B. Brute Force
- **Mechanism:** Automated credential stuffing or password dictionary attacks targeting authentication.
- **Key Indicators:**
  - Targeted almost exclusively at `/api/v1/auth/login`, `/api/v1/auth/token`, or `/api/v1/auth/reset-password`.
  - HTTP method is strictly `POST`.
  - Heavy concentration of `HTTP 401 Unauthorized` (82%) and `HTTP 403 Forbidden` (12%).
  - Very high `failed_requests` count (16 – 120 failures).
  - Latency remains low (35 – 190 ms) as authentication failure rejection is fast.

### C. High Error Rate
- **Mechanism:** Unhandled exceptions, broken backend microservices, or database lockouts.
- **Key Indicators:**
  - Heavy concentration of 5xx HTTP codes: `500 Internal Server Error` (60%), `502 Bad Gateway` (25%), `503 Service Unavailable` (15%).
  - Occurs on complex stateful operations (`/api/v1/checkout/process`, `/api/v1/reports`, `/api/v1/payments`).
  - Elevated `failed_requests` (8 – 48) and elevated latency (380 – 2,600 ms).

### D. Unusual Latency
- **Mechanism:** Unindexed heavy SQL queries, slowloris connection holds, CPU resource starvation, or upstream timeout.
- **Key Indicators:**
  - Latency explodes to **2,500 ms – 15,000 ms** (mean ~8,500 ms vs normal ~75 ms).
  - Normal or low request rate (`requests_per_minute` 1–28).
  - Status codes are either `200 OK` (eventual completion after delay) or `504 Gateway Timeout`.

### E. Large Payload
- **Mechanism:** Unauthorized mass data exfiltration (outbound) or buffer overflow / payload injection / excessive upload attempts (inbound).
- **Key Indicators:**
  - **Exfiltration:** Outbound `response_size_bytes` reaches **500,000 to 25,000,000 bytes** (500 KB to 25 MB).
  - **Injection / Upload:** Inbound `request_size_bytes` reaches **150,000 to 15,000,000 bytes** (150 KB to 15 MB).
  - High transmission time reflected in `response_time_ms` (550 – 4,800 ms).
  - `HTTP 413 Payload Too Large` or `HTTP 400 Bad Request` on oversized inbound payloads.

---

## 6. Dataset Limitations & Assumptions

1. **Synthetic Nature:** While feature distributions, correlations, and latency models are calibrated against realistic web traffic, they are synthetically generated and do not contain organic human variance (e.g., natural typo corrections, network packet drops, or fluctuating mobile signal latency).
2. **IP Anonymity:** Only synthetic private (RFC 1918) and documentation (RFC 5737) IP ranges are used. No real consumer or enterprise IP addresses are present.
3. **Session State:** The dataset does not include cookie session identifiers or JWT cryptographic signatures to maintain privacy and simplicity for isolation tree clustering.
4. **Label Separation:** The columns `is_anomaly` and `anomaly_type` serve purely as **ground-truth benchmarks** for calculating precision, recall, ROC-AUC, and F1-score during model validation. They must be stripped prior to unsupervised model training.

---

## 7. How to Regenerate the Dataset

The dataset can be completely reproduced at any time using the standalone generator script:

```powershell
# From the project root:
backend\.venv\Scripts\python.exe scripts\generate_dataset.py
```

Or using an active virtual environment:
```powershell
# Activate environment
.venv\Scripts\activate

# Execute generation
python scripts/generate_dataset.py
```

The script sets a deterministic seed (`RANDOM_SEED = 42`) and validates:
- Exactly 30,000 generated records.
- 85% normal / 15% anomalous ratio.
- 0 missing values.
- 0 duplicate rows.
- Saves directly to `data/raw/api_traffic.csv`.

