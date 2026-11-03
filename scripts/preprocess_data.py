"""
AegisAPI - Data Preprocessing & Exploratory Data Analysis (EDA) Pipeline (Phase 2)
---------------------------------------------------------------------------------
Performs automated data validation, cleaning, feature engineering, and statistical
visualizations on raw API traffic logs.

Inputs:
  - data/raw/api_traffic.csv

Outputs:
  - data/processed/api_traffic_processed.csv (full cleaned & engineered dataset)
  - data/processed/X_features.csv (model input feature matrix, no target/leakage)
  - data/processed/y_labels.csv (ground truth binary anomaly labels)
  - docs/eda/*.png (8 high-resolution analytical charts)
  - docs/preprocessing_report.md
"""

import os
import sys
import tempfile
import warnings
from typing import Tuple

# Configure headless backend and temporary writable cache for Matplotlib
os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "aegis_mpl_cache")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.preprocessing import RobustScaler

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "api_traffic.csv")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
PROCESSED_DATA_PATH = os.path.join(PROCESSED_DIR, "api_traffic_processed.csv")
X_FEATURES_PATH = os.path.join(PROCESSED_DIR, "X_features.csv")
Y_LABELS_PATH = os.path.join(PROCESSED_DIR, "y_labels.csv")
EDA_DIR = os.path.join(PROJECT_ROOT, "docs", "eda")

# Styling constants for EDA plots
sns.set_theme(style="whitegrid", palette="muted")
COLOR_NORMAL = "#2ecc71"     # Emerald Green
COLOR_ANOMALY = "#e74c3c"    # Crimson Red
PALETTE_BINARY = {0: COLOR_NORMAL, 1: COLOR_ANOMALY, "0": COLOR_NORMAL, "1": COLOR_ANOMALY}
PALETTE_TYPES = {
    "Normal": "#2ecc71",
    "Traffic Spike": "#e67e22",
    "Brute Force": "#e74c3c",
    "High Error Rate": "#9b59b6",
    "Unusual Latency": "#3498db",
    "Large Payload": "#1abc9c",
}


# ---------------------------------------------------------------------------
# 1. Dataset Inspection
# ---------------------------------------------------------------------------
def inspect_dataset(df: pd.DataFrame):
    """Log comprehensive sanity and quality metrics on raw dataset."""
    print("=" * 65)
    print("1. DATASET SANITY INSPECTION")
    print("=" * 65)
    print(f"Dimensions: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print("\nData Types:")
    for col, dtype in df.dtypes.items():
        print(f"  - {col:22s}: {dtype}")

    # Missing values
    missing_series = df.isnull().sum()
    total_missing = missing_series.sum()
    print(f"\nMissing Values Check: {total_missing} total missing")
    if total_missing > 0:
        print(missing_series[missing_series > 0])
    else:
        print("  [PASSED]: Zero missing values found.")

    # Duplicate rows
    dup_count = df.duplicated().sum()
    print(f"\nDuplicate Records Check: {dup_count} duplicate rows found")
    if dup_count == 0:
        print("  [PASSED]: Zero duplicate rows found.")

    # Domain integrity checks
    neg_latency = (df["response_time_ms"] < 0).sum()
    neg_req_size = (df["request_size_bytes"] < 0).sum()
    neg_res_size = (df["response_size_bytes"] < 0).sum()
    neg_rpm = (df["requests_per_minute"] < 0).sum()
    neg_failed = (df["failed_requests"] < 0).sum()
    invalid_status = (~df["status_code"].between(100, 599)).sum()

    print("\nDomain Integrity Assertions:")
    print(f"  - Non-negative latency:        {'[PASSED]' if neg_latency == 0 else f'[FAILED]: {neg_latency}'}")
    print(f"  - Non-negative request size:   {'[PASSED]' if neg_req_size == 0 else f'[FAILED]: {neg_req_size}'}")
    print(f"  - Non-negative response size:  {'[PASSED]' if neg_res_size == 0 else f'[FAILED]: {neg_res_size}'}")
    print(f"  - Non-negative RPM:            {'[PASSED]' if neg_rpm == 0 else f'[FAILED]: {neg_rpm}'}")
    print(f"  - Non-negative failed req:     {'[PASSED]' if neg_failed == 0 else f'[FAILED]: {neg_failed}'}")
    print(f"  - Valid RFC HTTP status codes: {'[PASSED]' if invalid_status == 0 else f'[FAILED]: {invalid_status}'}")

    # Distribution summary
    print("\nClass & Anomaly Breakdown:")
    print(df["is_anomaly"].value_counts().rename({0: "Normal (0)", 1: "Anomalous (1)"}).to_string())
    print("\nAnomaly Subtypes:")
    print(df["anomaly_type"].value_counts().to_string())
    print("=" * 65)


# ---------------------------------------------------------------------------
# 2. Data Cleaning
# ---------------------------------------------------------------------------
def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate raw dataframe without dropping valid records."""
    cleaned = df.copy()

    # 1. Datetime conversion
    cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], format="%Y-%m-%d %H:%M:%S")

    # 2. Missing value handling (guarantee no NaNs)
    if cleaned.isnull().sum().sum() > 0:
        cleaned = cleaned.dropna().reset_index(drop=True)

    # 3. Duplicate row check
    duplicates_removed = cleaned.duplicated().sum()
    if duplicates_removed > 0:
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)

    # 4. Strict boundary filters
    cleaned = cleaned[
        (cleaned["response_time_ms"] >= 0) &
        (cleaned["request_size_bytes"] >= 0) &
        (cleaned["response_size_bytes"] >= 0) &
        (cleaned["requests_per_minute"] >= 0) &
        (cleaned["failed_requests"] >= 0) &
        (cleaned["status_code"].between(100, 599))
    ].reset_index(drop=True)

    print(f"\n[Data Cleaning] Processed {len(cleaned):,} records (Duplicates removed: {duplicates_removed})")
    return cleaned


# ---------------------------------------------------------------------------
# 3. Exploratory Data Analysis (Visualizations)
# ---------------------------------------------------------------------------
def generate_eda_charts(df: pd.DataFrame, output_dir: str):
    """Generate and save all 8 high-resolution analytical charts."""
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n[EDA] Generating analytical visualizations in: {output_dir}")

    # --- Chart 1: Normal vs Anomalous Traffic Distribution ---
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    counts = df["is_anomaly"].value_counts().sort_index()
    labels = ["Normal (0)", "Anomalous (1)"]
    colors = [COLOR_NORMAL, COLOR_ANOMALY]
    bars = ax.bar(labels, counts, color=colors, edgecolor="black", linewidth=1.2, width=0.55)
    for bar in bars:
        height = bar.get_height()
        pct = (height / len(df)) * 100
        ax.annotate(
            f"{height:,}\n({pct:.1f}%)",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )
    ax.set_title("AegisAPI - Normal vs. Anomalous Traffic Distribution", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel("Total API Requests", fontsize=12, fontweight="bold")
    ax.set_ylim(0, max(counts) * 1.15)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    plt.tight_layout()
    chart1_path = os.path.join(output_dir, "01_normal_vs_anomalous_distribution.png")
    fig.savefig(chart1_path)
    plt.close(fig)
    print("  -> Saved: 01_normal_vs_anomalous_distribution.png")

    # --- Chart 2: Anomaly Type Breakdown ---
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    type_counts = df["anomaly_type"].value_counts()
    colors = [PALETTE_TYPES.get(t, "#95a5a6") for t in type_counts.index]
    bars = ax.barh(type_counts.index, type_counts.values, color=colors, edgecolor="black", linewidth=1.1, height=0.6)
    for bar in bars:
        width = bar.get_width()
        pct = (width / len(df)) * 100
        ax.annotate(
            f" {width:,} ({pct:.1f}%)",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
        )
    ax.set_title("AegisAPI - Traffic Breakdown by Anomaly Subcategory", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Record Count", fontsize=12, fontweight="bold")
    ax.set_xlim(0, max(type_counts.values) * 1.15)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    ax.invert_yaxis()
    plt.tight_layout()
    chart2_path = os.path.join(output_dir, "02_anomaly_type_distribution.png")
    fig.savefig(chart2_path)
    plt.close(fig)
    print("  -> Saved: 02_anomaly_type_distribution.png")

    # --- Chart 3: Response Time Distribution ---
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    sns.histplot(
        data=df,
        x="response_time_ms",
        hue="is_anomaly",
        palette=PALETTE_BINARY,
        log_scale=True,
        bins=50,
        kde=True,
        element="step",
        ax=ax,
    )
    ax.set_title("AegisAPI - API Response Time Distribution (Log Scale)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Response Latency in Milliseconds (log scale)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Request Frequency", fontsize=12, fontweight="bold")
    ax.legend(title="Traffic Class", labels=["Anomalous (1)", "Normal (0)"], loc="upper right")
    plt.tight_layout()
    chart3_path = os.path.join(output_dir, "03_response_time_distribution.png")
    fig.savefig(chart3_path)
    plt.close(fig)
    print("  -> Saved: 03_response_time_distribution.png")

    # --- Chart 4: Requests Per Minute Distribution ---
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    sns.histplot(
        data=df,
        x="requests_per_minute",
        hue="is_anomaly",
        palette=PALETTE_BINARY,
        bins=60,
        log_scale=(False, True),
        element="step",
        ax=ax,
    )
    ax.set_title("AegisAPI - Client Velocity: Requests Per Minute (RPM)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Requests Per Minute", fontsize=12, fontweight="bold")
    ax.set_ylabel("Log Frequency (Count)", fontsize=12, fontweight="bold")
    ax.legend(title="Traffic Class", labels=["Anomalous (1)", "Normal (0)"], loc="upper right")
    plt.tight_layout()
    chart4_path = os.path.join(output_dir, "04_requests_per_minute_distribution.png")
    fig.savefig(chart4_path)
    plt.close(fig)
    print("  -> Saved: 04_requests_per_minute_distribution.png")

    # --- Chart 5: HTTP Status Code Distribution ---
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    status_order = sorted(df["status_code"].unique())
    sns.countplot(
        data=df,
        x="status_code",
        hue="is_anomaly",
        palette=PALETTE_BINARY,
        order=status_order,
        ax=ax,
    )
    ax.set_title("AegisAPI - HTTP Status Code Distribution: Normal vs. Anomaly", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("HTTP Status Code", fontsize=12, fontweight="bold")
    ax.set_ylabel("Occurrences (Log Scale)", fontsize=12, fontweight="bold")
    ax.set_yscale("log")
    ax.legend(title="Traffic Class", labels=["Normal (0)", "Anomalous (1)"], loc="upper right")
    plt.tight_layout()
    chart5_path = os.path.join(output_dir, "05_status_code_distribution.png")
    fig.savefig(chart5_path)
    plt.close(fig)
    print("  -> Saved: 05_status_code_distribution.png")

    # --- Chart 6: Request Size vs Response Time ---
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    # Downsample normal points for readable scatter rendering
    normal_subset = df[df["is_anomaly"] == 0].sample(n=3000, random_state=42)
    anom_subset = df[df["is_anomaly"] == 1]
    plot_sub = pd.concat([normal_subset, anom_subset]).sample(frac=1.0, random_state=42)

    sns.scatterplot(
        data=plot_sub,
        x="request_size_bytes",
        y="response_time_ms",
        hue="is_anomaly",
        palette=PALETTE_BINARY,
        alpha=0.6,
        s=30,
        ax=ax,
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title("AegisAPI - Request Size vs. Response Time (Log-Log Scale)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Request Size in Bytes (log scale)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Response Latency in Milliseconds (log scale)", fontsize=12, fontweight="bold")
    ax.legend(title="Traffic Class", labels=["Normal (0)", "Anomalous (1)"], loc="upper left")
    plt.tight_layout()
    chart6_path = os.path.join(output_dir, "06_request_size_vs_response_time.png")
    fig.savefig(chart6_path)
    plt.close(fig)
    print("  -> Saved: 06_request_size_vs_response_time.png")

    # --- Chart 7: Normal vs Anomalous Response-Time Comparison (Boxplot) ---
    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    sns.boxplot(
        data=df,
        x="is_anomaly",
        y="response_time_ms",
        hue="is_anomaly",
        palette=PALETTE_BINARY,
        legend=False,
        ax=ax,
        showmeans=True,
        meanprops={"marker": "o", "markerfacecolor": "white", "markeredgecolor": "black", "markersize": 8},
    )
    ax.set_yscale("log")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Normal Traffic (0)", "Anomalous Traffic (1)"], fontsize=11, fontweight="bold")
    ax.set_title("AegisAPI - Latency Comparison: Normal vs. Anomalous (Log Scale)", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel("Response Time in Milliseconds (log scale)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Traffic Classification", fontsize=12, fontweight="bold")
    plt.tight_layout()
    chart7_path = os.path.join(output_dir, "07_normal_vs_anomalous_response_time.png")
    fig.savefig(chart7_path)
    plt.close(fig)
    print("  -> Saved: 07_normal_vs_anomalous_response_time.png")

    # --- Chart 8: Traffic Volume Over Time (Hourly Timeline) ---
    fig, ax = plt.subplots(figsize=(14, 6), dpi=300)
    time_df = df.set_index("timestamp")
    hourly_normal = time_df[time_df["is_anomaly"] == 0].resample("1h")["is_anomaly"].count()
    hourly_anom = time_df[time_df["is_anomaly"] == 1].resample("1h")["is_anomaly"].count()

    ax.plot(hourly_normal.index, hourly_normal.values, label="Normal Traffic", color=COLOR_NORMAL, linewidth=1.8)
    ax.plot(hourly_anom.index, hourly_anom.values, label="Anomalous Incidents", color=COLOR_ANOMALY, linewidth=2.0)
    ax.set_title("AegisAPI - Hourly API Traffic Ingestion Volume Across 7-Day Simulation", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Date & Time (UTC)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Requests per Hour", fontsize=12, fontweight="bold")
    ax.legend(loc="upper right", frameon=True)
    plt.xticks(rotation=25)
    plt.tight_layout()
    chart8_path = os.path.join(output_dir, "08_traffic_volume_over_time.png")
    fig.savefig(chart8_path)
    plt.close(fig)
    print("  -> Saved: 08_traffic_volume_over_time.png")


# ---------------------------------------------------------------------------
# 4. Feature Engineering
# ---------------------------------------------------------------------------
def engineer_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Transform raw API logs into high-signal model features.
    Strictly removes target labels (is_anomaly, anomaly_type) and leakable identifiers (source_ip, timestamp).
    """
    feat_df = df.copy()

    # --- Time-based features ---
    feat_df["hour"] = feat_df["timestamp"].dt.hour
    feat_df["day_of_week"] = feat_df["timestamp"].dt.dayofweek
    feat_df["is_weekend"] = (feat_df["day_of_week"] >= 5).astype(int)

    # --- Cyclical encoding of hour (preserves circular 23:00 -> 00:00 continuity) ---
    feat_df["hour_sin"] = np.sin(2 * np.pi * feat_df["hour"] / 24.0)
    feat_df["hour_cos"] = np.cos(2 * np.pi * feat_df["hour"] / 24.0)

    # --- HTTP Semantics & Status Flags ---
    feat_df["is_error"] = (feat_df["status_code"] >= 400).astype(int)
    feat_df["is_client_error"] = ((feat_df["status_code"] >= 400) & (feat_df["status_code"] < 500)).astype(int)
    feat_df["is_server_error"] = (feat_df["status_code"] >= 500).astype(int)

    # --- User Agent Categorization ---
    # Classify whether user agent matches script/bot/tool signature
    tool_signatures = ["curl", "requests", "Go-http-client", "Hydra", "Postman", "Apache-HttpClient"]
    pattern = "|".join(tool_signatures)
    feat_df["is_automation_agent"] = feat_df["user_agent"].str.contains(pattern, case=False, regex=True).astype(int)

    # --- Domain Interaction Ratios ---
    feat_df["failure_rate"] = feat_df["failed_requests"] / (feat_df["requests_per_minute"] + 1.0)
    feat_df["total_bytes"] = feat_df["request_size_bytes"] + feat_df["response_size_bytes"]
    feat_df["byte_ratio"] = feat_df["response_size_bytes"] / (feat_df["request_size_bytes"] + 1.0)

    # --- One-Hot Encoding for Categorical Columns ---
    # Methods: GET, POST, PUT, DELETE
    method_dummies = pd.get_dummies(feat_df["http_method"], prefix="method", dtype=int)

    # Top API endpoint paths
    endpoint_dummies = pd.get_dummies(feat_df["endpoint"], prefix="endpoint", dtype=int)

    # Base numerical features to scale
    numerical_cols = [
        "response_time_ms",
        "request_size_bytes",
        "response_size_bytes",
        "requests_per_minute",
        "failed_requests",
        "failure_rate",
        "total_bytes",
        "byte_ratio",
    ]

    # RobustScaler is chosen because it uses median and IQR, preventing
    # extreme DDoS spikes or exfiltration payloads from corrupting the scaling center.
    scaler = RobustScaler()
    scaled_num = pd.DataFrame(
        scaler.fit_transform(feat_df[numerical_cols]),
        columns=[f"{c}_scaled" for c in numerical_cols],
        index=feat_df.index,
    )

    # Assemble model input matrix X
    # Integer/binary indicators:
    binary_features = pd.concat([
        feat_df[[
            "hour",
            "day_of_week",
            "is_weekend",
            "hour_sin",
            "hour_cos",
            "status_code",
            "is_error",
            "is_client_error",
            "is_server_error",
            "is_automation_agent",
        ]],
        method_dummies,
        endpoint_dummies,
    ], axis=1)

    X_features = pd.concat([scaled_num, binary_features], axis=1)

    # Separate ground truth label vector
    y_labels = feat_df["is_anomaly"].astype(int)

    # Complete processed dataset containing all original columns + new features for analytics
    processed_full = pd.concat([feat_df, scaled_num, method_dummies, endpoint_dummies], axis=1)
    # Remove any potential duplicate columns from concat
    processed_full = processed_full.loc[:, ~processed_full.columns.duplicated()]

    return processed_full, X_features, y_labels


# ---------------------------------------------------------------------------
# 5. Pipeline Validation
# ---------------------------------------------------------------------------
def validate_pipeline_outputs(X_features: pd.DataFrame, y_labels: pd.Series):
    """Verify integrity of engineered features and label separation."""
    print("\n" + "=" * 65)
    print("5. MODEL FEATURE MATRIX VALIDATION")
    print("=" * 65)

    # 1. Row counts match
    assert len(X_features) == len(y_labels), "Row count mismatch between features and labels!"
    print(f"[PASSED] Row count synchronization: {len(X_features):,} records.")

    # 2. Check for missing values
    missing_in_X = X_features.isnull().sum().sum()
    assert missing_in_X == 0, f"Missing values detected in feature matrix: {missing_in_X}"
    print(f"[PASSED] Zero missing values in feature matrix (null count: {missing_in_X}).")

    # 3. Label balance verification
    label_counts = y_labels.value_counts().to_dict()
    assert 0 in label_counts and 1 in label_counts, "Target labels do not contain both 0 and 1!"
    print(f"[PASSED] Target label presence confirmed: {label_counts}")

    # 4. Strict Leakage Prevention Verification
    forbidden_columns = ["is_anomaly", "anomaly_type", "source_ip", "timestamp"]
    for col in forbidden_columns:
        assert col not in X_features.columns, f"LEAKAGE DETECTED: Column '{col}' present in X_features!"
    print("[PASSED] Zero data leakage: No labels, anomaly types, IPs, or raw timestamps in X_features.")

    # 5. Dimensionality
    print(f"\nFinal Feature Matrix Dimensions: {X_features.shape[0]:,} rows x {X_features.shape[1]} features")
    print(f"Final Label Vector Dimensions:   {len(y_labels):,} rows")
    print("\nFeature Columns List:")
    for i, col in enumerate(X_features.columns, start=1):
        print(f"  {i:2d}. {col}")

    print("\nFeature Matrix Head (Preview first 3 rows):")
    print(X_features.head(3).to_string())
    print("=" * 65)


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------
def main():
    print("Starting AegisAPI Phase 2: Data Preprocessing & EDA Pipeline...")

    # Step 1: Verification of raw data file
    if not os.path.exists(RAW_DATA_PATH):
        print(f"\n[ERROR] Raw dataset not found at expected path: {RAW_DATA_PATH}")
        print("Please ensure Phase 1 generation has completed before running Phase 2.")
        sys.exit(1)

    print(f"Loading raw dataset from: {RAW_DATA_PATH}")
    df_raw = pd.read_csv(RAW_DATA_PATH)

    # Step 2: Inspection
    inspect_dataset(df_raw)

    # Step 3: Cleaning
    df_cleaned = clean_dataset(df_raw)

    # Step 4: Exploratory Data Analysis & Chart Generation
    generate_eda_charts(df_cleaned, EDA_DIR)

    # Step 5: Feature Engineering
    print("\n[Feature Engineering] Transforming raw logs into model-ready features...")
    df_processed, X_features, y_labels = engineer_features(df_cleaned)

    # Step 6: Save Artifacts
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    print(f"\n[Storage] Saving processed artifacts to: {PROCESSED_DIR}")

    df_processed.to_csv(PROCESSED_DATA_PATH, index=False)
    print(f"  -> Saved full processed dataset: {PROCESSED_DATA_PATH}")

    X_features.to_csv(X_FEATURES_PATH, index=False)
    print(f"  -> Saved model feature matrix:   {X_FEATURES_PATH}")

    y_labels.to_csv(Y_LABELS_PATH, index=False, header=["is_anomaly"])
    print(f"  -> Saved ground-truth labels:    {Y_LABELS_PATH}")

    # Step 7: Validation
    validate_pipeline_outputs(X_features, y_labels)
    print("\nPhase 2 Preprocessing & EDA completed successfully!")


if __name__ == "__main__":
    main()
