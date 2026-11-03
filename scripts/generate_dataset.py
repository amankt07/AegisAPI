"""
AegisAPI - Synthetic API Traffic Dataset Generator (Phase 1)
-----------------------------------------------------------
Generates a realistic, reproducible dataset of API traffic logs (~30,000 records)
with an 85% normal / 15% anomalous distribution for training and evaluating
unsupervised anomaly detection models (e.g., Isolation Forest).

Output path: data/raw/api_traffic.csv
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration & Reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED = 42
TOTAL_RECORDS = 30000
NORMAL_RATIO = 0.85
ANOMALY_RATIO = 0.15

NORMAL_COUNT = int(TOTAL_RECORDS * NORMAL_RATIO)      # 25,500
ANOMALOUS_COUNT = TOTAL_RECORDS - NORMAL_COUNT        # 4,500

# 5 distinct anomaly types evenly distributed (900 each)
ANOMALY_SUBTYPES = [
    "Traffic Spike",
    "Brute Force",
    "High Error Rate",
    "Unusual Latency",
    "Large Payload",
]
COUNT_PER_ANOMALY = ANOMALOUS_COUNT // len(ANOMALY_SUBTYPES)  # 900 each

# Multi-day simulation window (7 days)
START_TIME = datetime(2026, 10, 25, 0, 0, 0)
DURATION_SECONDS = 7 * 24 * 3600  # 604,800 seconds

# Synthetic IP Pools (RFC 1918 & RFC 5737 Documentation/Private IP ranges)
NORMAL_IPS = [f"192.168.1.{i}" for i in range(10, 250)] + \
             [f"10.0.{i}.{j}" for i in range(1, 10) for j in range(10, 40)] + \
             [f"172.16.5.{i}" for i in range(1, 100)]

ATTACKER_IPS = [f"198.51.100.{i}" for i in range(1, 35)] + \
               [f"203.0.113.{i}" for i in range(1, 35)]

# User Agents
STANDARD_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
]

AUTOMATION_USER_AGENTS = [
    "python-requests/2.31.0",
    "curl/8.4.0",
    "Go-http-client/1.1",
    "PostmanRuntime/7.36.0",
    "Hydra/9.5",
    "Apache-HttpClient/4.5.13",
]


def seed_everything(seed: int = RANDOM_SEED):
    """Set seeds for reproducibility across Python and NumPy."""
    random.seed(seed)
    np.random.seed(seed)


def generate_timestamps(n: int, start_time: datetime, duration_sec: int) -> list:
    """Generate monotonically distributed random timestamps across a multi-day span."""
    offsets = np.sort(np.random.randint(0, duration_sec, size=n))
    return [start_time + timedelta(seconds=int(sec)) for sec in offsets]


# ---------------------------------------------------------------------------
# Generators for Traffic Categories
# ---------------------------------------------------------------------------

def generate_normal_traffic(count: int) -> list:
    """
    Generate realistic normal API traffic.
    - Low-to-moderate latency (20 - 220 ms)
    - Normal payload sizes (< 2.5 KB requests, < 15 KB responses)
    - Low request frequency (1 - 45 req/min)
    - Predominantly 2xx responses, negligible failed requests (0 or 1)
    """
    records = []
    endpoint_choices = [
        ("/api/v1/products", "GET", 0.25),
        ("/api/v1/products/detail", "GET", 0.18),
        ("/api/v1/users/profile", "GET", 0.12),
        ("/api/v1/users/profile", "PUT", 0.05),
        ("/api/v1/cart", "GET", 0.10),
        ("/api/v1/cart/items", "POST", 0.08),
        ("/api/v1/cart/items", "DELETE", 0.03),
        ("/api/v1/orders", "GET", 0.08),
        ("/api/v1/orders", "POST", 0.05),
        ("/api/v1/auth/login", "POST", 0.04),
        ("/api/v1/health", "GET", 0.02),
    ]
    endpoints = [x[0] for x in endpoint_choices]
    methods = [x[1] for x in endpoint_choices]
    weights = [x[2] for x in endpoint_choices]

    # Pre-sample selections for efficiency
    idx_choices = np.random.choice(len(endpoint_choices), size=count, p=weights)

    for i in range(count):
        idx = idx_choices[i]
        endpoint = endpoints[idx]
        method = methods[idx]

        # Status code: 92% 200, 5% 201, 1.5% 204, 1% 400, 0.5% 404
        status_prob = np.random.rand()
        if status_prob < 0.92:
            status_code = 200
        elif status_prob < 0.97:
            status_code = 201 if method == "POST" else 200
        elif status_prob < 0.985:
            status_code = 204 if method in ["PUT", "DELETE"] else 200
        elif status_prob < 0.995:
            status_code = 400
        else:
            status_code = 404

        # Latency: gamma distributed, centered around 65-90 ms
        base_latency = np.random.gamma(shape=3.5, scale=20.0)
        response_time_ms = round(float(np.clip(base_latency, 18.0, 240.0)), 2)

        # Request size (bytes)
        if method == "GET":
            request_size_bytes = int(np.random.normal(180, 45))
        elif method in ["POST", "PUT"]:
            request_size_bytes = int(np.random.normal(850, 220))
        else:  # DELETE
            request_size_bytes = int(np.random.normal(120, 30))
        request_size_bytes = max(50, request_size_bytes)

        # Response size (bytes)
        if status_code in [204, 404, 400]:
            response_size_bytes = int(np.random.normal(250, 50))
        else:
            response_size_bytes = int(np.random.normal(3200, 950))
        response_size_bytes = max(80, response_size_bytes)

        # Requests per minute: standard human browsing / normal client
        requests_per_minute = int(np.random.poisson(lam=14))
        requests_per_minute = int(np.clip(requests_per_minute, 1, 45))

        # Failed requests: almost always 0, rarely 1 for 4xx errors
        failed_requests = 1 if status_code >= 400 and np.random.rand() < 0.7 else 0

        source_ip = random.choice(NORMAL_IPS)
        user_agent = random.choice(STANDARD_USER_AGENTS)

        records.append({
            "source_ip": source_ip,
            "endpoint": endpoint,
            "http_method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "request_size_bytes": request_size_bytes,
            "response_size_bytes": response_size_bytes,
            "requests_per_minute": requests_per_minute,
            "failed_requests": failed_requests,
            "user_agent": user_agent,
            "is_anomaly": 0,
            "anomaly_type": "Normal",
        })

    return records


def generate_traffic_spike(count: int) -> list:
    """
    Anomaly Type: Traffic Spike
    - Extreme requests per minute (280 - 1800 req/min)
    - Burst scraping or DoS flood from specific attacker IPs
    - Triggers 429 Too Many Requests or 503 Service Unavailable under load
    """
    records = []
    spike_endpoints = [
        ("/api/v1/products", "GET"),
        ("/api/v1/products/detail", "GET"),
        ("/api/v1/search", "GET"),
        ("/api/v1/orders", "POST"),
    ]
    spike_ips = random.sample(ATTACKER_IPS, k=8)

    for _ in range(count):
        endpoint, method = random.choice(spike_endpoints)
        source_ip = random.choice(spike_ips)

        # 60% 200, 30% 429 (rate limit), 10% 503 (server overloaded)
        p = np.random.rand()
        if p < 0.60:
            status_code = 200
        elif p < 0.90:
            status_code = 429
        else:
            status_code = 503

        # Elevated requests per minute
        requests_per_minute = int(np.random.uniform(280, 1600))

        # Slightly degraded response time under load
        response_time_ms = round(float(np.random.uniform(140.0, 750.0)), 2)

        request_size_bytes = int(np.random.normal(320, 80))
        request_size_bytes = max(100, request_size_bytes)

        if status_code in [429, 503]:
            response_size_bytes = int(np.random.normal(320, 40))
            failed_requests = int(np.random.uniform(12, 60))
        else:
            response_size_bytes = int(np.random.normal(2400, 600))
            failed_requests = int(np.random.uniform(2, 10))

        response_size_bytes = max(100, response_size_bytes)
        user_agent = random.choice(AUTOMATION_USER_AGENTS)

        records.append({
            "source_ip": source_ip,
            "endpoint": endpoint,
            "http_method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "request_size_bytes": request_size_bytes,
            "response_size_bytes": response_size_bytes,
            "requests_per_minute": requests_per_minute,
            "failed_requests": failed_requests,
            "user_agent": user_agent,
            "is_anomaly": 1,
            "anomaly_type": "Traffic Spike",
        })

    return records


def generate_brute_force(count: int) -> list:
    """
    Anomaly Type: Brute Force
    - Targeted at authentication endpoints
    - Predominantly HTTP 401 Unauthorized / 403 Forbidden
    - High failed request counts (15 - 120)
    - Rapid repetitive login attempts
    """
    records = []
    auth_endpoints = [
        "/api/v1/auth/login",
        "/api/v1/auth/token",
        "/api/v1/auth/reset-password",
    ]
    brute_force_ips = random.sample(ATTACKER_IPS, k=10)

    for _ in range(count):
        endpoint = random.choice(auth_endpoints)
        method = "POST"
        source_ip = random.choice(brute_force_ips)

        # 82% 401 Unauthorized, 12% 403 Forbidden, 6% 429
        p = np.random.rand()
        if p < 0.82:
            status_code = 401
        elif p < 0.94:
            status_code = 403
        else:
            status_code = 429

        # Fast credential verification latency
        response_time_ms = round(float(np.random.uniform(35.0, 190.0)), 2)

        # Small JSON credentials payload
        request_size_bytes = int(np.random.uniform(140, 380))
        # Small JSON error response
        response_size_bytes = int(np.random.uniform(90, 260))

        # Elevated requests per minute
        requests_per_minute = int(np.random.uniform(60, 360))

        # High failed request history
        failed_requests = int(np.random.uniform(16, 120))

        # Script or bot tool user agent
        user_agent = random.choice(["Hydra/9.5", "python-requests/2.31.0", "curl/8.4.0", "Go-http-client/1.1"])

        records.append({
            "source_ip": source_ip,
            "endpoint": endpoint,
            "http_method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "request_size_bytes": request_size_bytes,
            "response_size_bytes": response_size_bytes,
            "requests_per_minute": requests_per_minute,
            "failed_requests": failed_requests,
            "user_agent": user_agent,
            "is_anomaly": 1,
            "anomaly_type": "Brute Force",
        })

    return records


def generate_high_error_rate(count: int) -> list:
    """
    Anomaly Type: High Error Rate
    - Server crashes, database connection failures, upstream 5xx errors
    - High failed_requests count
    - Elevated latency from unhandled exceptions or timeout waits
    """
    records = []
    error_endpoints = [
        ("/api/v1/checkout/process", "POST"),
        ("/api/v1/reports", "GET"),
        ("/api/v1/analytics", "GET"),
        ("/api/v1/payments", "POST"),
        ("/api/v1/orders", "POST"),
    ]

    for _ in range(count):
        endpoint, method = random.choice(error_endpoints)
        source_ip = random.choice(NORMAL_IPS + ATTACKER_IPS[:5])

        # 60% 500 Internal Server Error, 25% 502 Bad Gateway, 15% 503 Service Unavailable
        p = np.random.rand()
        if p < 0.60:
            status_code = 500
        elif p < 0.85:
            status_code = 502
        else:
            status_code = 503

        # Server error latency (stack traces, failed db connections)
        response_time_ms = round(float(np.random.uniform(380.0, 2600.0)), 2)

        request_size_bytes = int(np.random.uniform(280, 1800))
        response_size_bytes = int(np.random.uniform(150, 750))  # JSON error stack / page

        requests_per_minute = int(np.random.uniform(10, 85))
        failed_requests = int(np.random.uniform(8, 48))

        user_agent = random.choice(STANDARD_USER_AGENTS + AUTOMATION_USER_AGENTS[:2])

        records.append({
            "source_ip": source_ip,
            "endpoint": endpoint,
            "http_method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "request_size_bytes": request_size_bytes,
            "response_size_bytes": response_size_bytes,
            "requests_per_minute": requests_per_minute,
            "failed_requests": failed_requests,
            "user_agent": user_agent,
            "is_anomaly": 1,
            "anomaly_type": "High Error Rate",
        })

    return records


def generate_unusual_latency(count: int) -> list:
    """
    Anomaly Type: Unusual Latency
    - Severe latency anomalies (2,500 ms - 15,000 ms)
    - Resource deadlock, unindexed queries, or 504 Gateway Timeout
    """
    records = []
    heavy_endpoints = [
        ("/api/v1/reports/export", "GET"),
        ("/api/v1/analytics/query", "POST"),
        ("/api/v1/search", "GET"),
        ("/api/v1/products/detail", "GET"),
    ]

    for _ in range(count):
        endpoint, method = random.choice(heavy_endpoints)
        source_ip = random.choice(NORMAL_IPS)

        # 70% 200 OK (eventual slow resolution), 30% 504 Gateway Timeout
        status_code = 200 if np.random.rand() < 0.70 else 504

        # Massive latency spike: 2,500 ms to 15,000 ms
        response_time_ms = round(float(np.random.uniform(2500.0, 15000.0)), 2)

        request_size_bytes = int(np.random.uniform(200, 2200))
        response_size_bytes = int(np.random.uniform(1200, 18000)) if status_code == 200 else int(np.random.uniform(150, 450))

        # Slowloris or slow client typically has low RPM
        requests_per_minute = int(np.random.uniform(1, 28))
        failed_requests = int(np.random.uniform(1, 5)) if status_code == 504 else 0

        user_agent = random.choice(STANDARD_USER_AGENTS)

        records.append({
            "source_ip": source_ip,
            "endpoint": endpoint,
            "http_method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "request_size_bytes": request_size_bytes,
            "response_size_bytes": response_size_bytes,
            "requests_per_minute": requests_per_minute,
            "failed_requests": failed_requests,
            "user_agent": user_agent,
            "is_anomaly": 1,
            "anomaly_type": "Unusual Latency",
        })

    return records


def generate_large_payload(count: int) -> list:
    """
    Anomaly Type: Large Payload
    - Data exfiltration (abnormally huge response sizes: 500 KB - 25 MB)
    - Buffer overflow / payload injection / huge uploads (abnormally huge request sizes: 150 KB - 15 MB)
    - Elevated latency due to transmission overhead
    """
    records = []
    exfiltration_endpoints = [
        ("/api/v1/users/export", "GET"),
        ("/api/v1/reports/export", "GET"),
        ("/api/v1/orders/dump", "GET"),
    ]
    injection_endpoints = [
        ("/api/v1/upload", "POST"),
        ("/api/v1/users/profile", "PUT"),
        ("/api/v1/cart/items", "POST"),
    ]

    for _ in range(count):
        # 50% large outbound exfiltration, 50% large inbound upload/injection
        is_exfiltration = np.random.rand() < 0.50

        if is_exfiltration:
            endpoint, method = random.choice(exfiltration_endpoints)
            status_code = 200
            request_size_bytes = int(np.random.uniform(200, 800))
            # 500 KB to 25 MB
            response_size_bytes = int(np.random.uniform(500_000, 25_000_000))
        else:
            endpoint, method = random.choice(injection_endpoints)
            # 70% 200, 20% 413 Payload Too Large, 10% 400 Bad Request
            p = np.random.rand()
            if p < 0.70:
                status_code = 200
            elif p < 0.90:
                status_code = 413
            else:
                status_code = 400
            # 150 KB to 15 MB
            request_size_bytes = int(np.random.uniform(150_000, 15_000_000))
            response_size_bytes = int(np.random.uniform(200, 1500))

        # Latency accounts for wire transfer time
        response_time_ms = round(float(np.random.uniform(550.0, 4800.0)), 2)

        requests_per_minute = int(np.random.uniform(3, 45))
        failed_requests = 1 if status_code >= 400 else 0

        source_ip = random.choice(ATTACKER_IPS + NORMAL_IPS[:20])
        user_agent = random.choice(AUTOMATION_USER_AGENTS + STANDARD_USER_AGENTS[:2])

        records.append({
            "source_ip": source_ip,
            "endpoint": endpoint,
            "http_method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "request_size_bytes": request_size_bytes,
            "response_size_bytes": response_size_bytes,
            "requests_per_minute": requests_per_minute,
            "failed_requests": failed_requests,
            "user_agent": user_agent,
            "is_anomaly": 1,
            "anomaly_type": "Large Payload",
        })

    return records


# ---------------------------------------------------------------------------
# Master Dataset Assembly & Validation
# ---------------------------------------------------------------------------

def build_dataset() -> pd.DataFrame:
    """Synthesize, interleave, and chronologically sort all traffic records."""
    seed_everything(RANDOM_SEED)

    print("Generating normal API traffic...")
    normal_records = generate_normal_traffic(NORMAL_COUNT)

    print("Generating anomalous API traffic subcategories...")
    spike_records = generate_traffic_spike(COUNT_PER_ANOMALY)
    brute_force_records = generate_brute_force(COUNT_PER_ANOMALY)
    error_records = generate_high_error_rate(COUNT_PER_ANOMALY)
    latency_records = generate_unusual_latency(COUNT_PER_ANOMALY)
    payload_records = generate_large_payload(COUNT_PER_ANOMALY)

    all_records = (
        normal_records
        + spike_records
        + brute_force_records
        + error_records
        + latency_records
        + payload_records
    )

    # Generate chronologically ordered multi-day timestamps
    print(f"Generating {len(all_records)} timestamps spanning 7 days...")
    timestamps = generate_timestamps(len(all_records), START_TIME, DURATION_SECONDS)

    # Assign timestamps randomly across records so anomalies are naturally distributed over time
    random.shuffle(all_records)
    for record, ts in zip(all_records, timestamps):
        record["timestamp"] = ts.strftime("%Y-%m-%d %H:%M:%S")

    df = pd.DataFrame(all_records)

    # Reorder columns explicitly according to specification
    column_order = [
        "timestamp",
        "source_ip",
        "endpoint",
        "http_method",
        "status_code",
        "response_time_ms",
        "request_size_bytes",
        "response_size_bytes",
        "requests_per_minute",
        "failed_requests",
        "user_agent",
        "is_anomaly",
        "anomaly_type",
    ]
    df = df[column_order]

    # Sort strictly by timestamp
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    return df


def validate_dataset(df: pd.DataFrame):
    """Perform rigorous validation checks on the synthesized dataset."""
    print("\n" + "=" * 60)
    print("DATASET VALIDATION & SUMMARY REPORT")
    print("=" * 60)

    # Dimensions
    print(f"\n1. Total Records: {len(df):,}")
    print(f"   Total Columns: {df.shape[1]}")

    # Normal vs Anomaly distribution
    print("\n2. Ground-Truth Anomaly Label Distribution:")
    anomaly_counts = df["is_anomaly"].value_counts().rename({0: "Normal (0)", 1: "Anomaly (1)"})
    anomaly_pcts = df["is_anomaly"].value_counts(normalize=True) * 100
    for label, count in anomaly_counts.items():
        pct = anomaly_pcts[0 if "0" in label else 1]
        print(f"   - {label}: {count:,} ({pct:.2f}%)")

    # Anomaly breakdown by type
    print("\n3. Traffic Breakdown by Anomaly Type:")
    type_counts = df["anomaly_type"].value_counts()
    type_pcts = df["anomaly_type"].value_counts(normalize=True) * 100
    for atype, count in type_counts.items():
        print(f"   - {atype:18s}: {count:,} ({type_pcts[atype]:.2f}%)")

    # Missing values check
    missing_count = df.isnull().sum().sum()
    print(f"\n4. Missing Values Count: {missing_count}")
    if missing_count > 0:
        print("   Missing by column:")
        print(df.isnull().sum())
    else:
        print("   [PASSED]: Zero missing values across all columns.")

    # Duplicate rows check
    dup_count = df.duplicated().sum()
    print(f"\n5. Duplicate Rows Count: {dup_count}")
    if dup_count == 0:
        print("   [PASSED]: Zero duplicate records found.")
    else:
        print(f"   Warning: {dup_count} duplicate rows detected.")

    # First five records
    print("\n6. First 5 Records (Preview):")
    print(df.head().to_string())

    # Statistical summary
    print("\n7. Basic Statistical Summaries (Numeric Features):")
    numeric_cols = [
        "status_code",
        "response_time_ms",
        "request_size_bytes",
        "response_size_bytes",
        "requests_per_minute",
        "failed_requests",
    ]
    print(df[numeric_cols].describe().round(2).to_string())
    print("\n" + "=" * 60)


def main():
    """Main execution entrypoint."""
    # Resolve project root dynamically
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    output_dir = os.path.join(project_root, "data", "raw")
    output_path = os.path.join(output_dir, "api_traffic.csv")

    os.makedirs(output_dir, exist_ok=True)

    print(f"Starting AegisAPI Phase 1 Dataset Generation...")
    print(f"Target record count: {TOTAL_RECORDS:,}")
    print(f"Output target: {output_path}")

    df = build_dataset()

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"\nSuccessfully generated and saved dataset to: {output_path}")

    # Run validation
    validate_dataset(df)


if __name__ == "__main__":
    main()
