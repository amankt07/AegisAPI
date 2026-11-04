"""
AegisAPI - Model Evaluation & Real-Time Inference Tester (Phase 3)
-----------------------------------------------------------------
Evaluates saved model artifacts on the unseen test partition and tests
real-time scoring across simulated production traffic payloads.

Outputs:
  - Validates models/isolation_forest.pkl
  - Computes test set classification report
  - Runs live inference simulation on realistic attack vectors
"""

import json
import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, average_precision_score
from sklearn.model_selection import train_test_split

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "isolation_forest.pkl")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")
SCHEMA_PATH = os.path.join(MODELS_DIR, "feature_columns.json")
META_PATH = os.path.join(MODELS_DIR, "model_metadata.json")

X_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "X_features.csv")
Y_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "y_labels.csv")

RANDOM_STATE = 42
TEST_SIZE = 0.20


def load_artifacts():
    """Verify and load saved model artifacts."""
    for path in [MODEL_PATH, SCALER_PATH, SCHEMA_PATH, META_PATH]:
        if not os.path.exists(path):
            print(f"[ERROR] Required model artifact missing: {path}")
            sys.exit(1)

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
    with open(META_PATH, "r") as f:
        metadata = json.load(f)

    return model, scaler, schema, metadata


def evaluate_test_set(model, schema):
    """Run evaluation on the stratified test split."""
    print("=" * 65)
    print("AEGISAPI MODEL EVALUATION REPORT")
    print("=" * 65)

    X = pd.read_csv(X_PATH)
    y = pd.read_csv(Y_PATH)["is_anomaly"].astype(int)

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    # Confirm column ordering matches schema
    X_test = X_test[schema["feature_names"]]

    # Predict: -1 is anomaly, 1 is normal
    raw_preds = model.predict(X_test)
    y_preds = np.where(raw_preds == -1, 1, 0)
    scores = -model.decision_function(X_test)

    roc = roc_auc_score(y_test, scores)
    pr = average_precision_score(y_test, scores)
    cm = confusion_matrix(y_test, y_preds)
    tn, fp, fn, tp = cm.ravel()

    print(f"\nTest Set Size: {len(X_test):,} samples")
    print(f"ROC-AUC:       {roc:.4f}")
    print(f"PR-AUC:        {pr:.4f}")
    print("\nConfusion Matrix:")
    print(f"  True Negatives  (Normal -> Normal):     {tn:,} ({(tn/(tn+fp))*100:.2f}%)")
    print(f"  False Positives (Normal -> Anomaly):    {fp:,} ({(fp/(tn+fp))*100:.2f}%)")
    print(f"  False Negatives (Anomaly -> Normal):    {fn:,} ({(fn/(fn+tp))*100:.2f}%)")
    print(f"  True Positives  (Anomaly -> Anomaly):   {tp:,} ({(tp/(fn+tp))*100:.2f}%)")

    print("\nClassification Report:")
    print(classification_report(y_test, y_preds, target_names=["Normal (0)", "Anomaly (1)"], digits=4))


def simulate_live_traffic_scoring(model, scaler, schema):
    """Simulate real-time scoring on 6 diverse synthetic production API scenarios."""
    print("=" * 65)
    print("LIVE PRODUCTION TRAFFIC INFERENCE SIMULATION")
    print("=" * 65)

    scenarios = [
        {
            "name": "Scenario 1: Normal Product Browsing",
            "method": "GET",
            "endpoint": "/api/v1/products",
            "status_code": 200,
            "latency": 65.0,
            "req_size": 180,
            "res_size": 3400,
            "rpm": 14,
            "failed_req": 0,
            "is_automation": 0,
            "hour": 14,
            "expected": "Normal",
        },
        {
            "name": "Scenario 2: Automated Scraper Volumetric Spike",
            "method": "GET",
            "endpoint": "/api/v1/products",
            "status_code": 429,
            "latency": 350.0,
            "req_size": 320,
            "res_size": 400,
            "rpm": 1250,
            "failed_req": 35,
            "is_automation": 1,
            "hour": 3,
            "expected": "Anomaly (Traffic Spike)",
        },
        {
            "name": "Scenario 3: Credential Stuffing Brute Force",
            "method": "POST",
            "endpoint": "/api/v1/auth/login",
            "status_code": 401,
            "latency": 55.0,
            "req_size": 240,
            "res_size": 180,
            "rpm": 180,
            "failed_req": 85,
            "is_automation": 1,
            "hour": 2,
            "expected": "Anomaly (Brute Force)",
        },
        {
            "name": "Scenario 4: Backend Database Crash Loop",
            "method": "POST",
            "endpoint": "/api/v1/checkout/process",
            "status_code": 500,
            "latency": 1450.0,
            "req_size": 850,
            "res_size": 320,
            "rpm": 45,
            "failed_req": 28,
            "is_automation": 0,
            "hour": 18,
            "expected": "Anomaly (High Error Rate)",
        },
        {
            "name": "Scenario 5: Slowloris / Extreme Latency Hang",
            "method": "GET",
            "endpoint": "/api/v1/reports/export",
            "status_code": 504,
            "latency": 11500.0,
            "req_size": 280,
            "res_size": 250,
            "rpm": 6,
            "failed_req": 4,
            "is_automation": 0,
            "hour": 11,
            "expected": "Anomaly (Unusual Latency)",
        },
        {
            "name": "Scenario 6: Mass Data Exfiltration Dump",
            "method": "GET",
            "endpoint": "/api/v1/users/export",
            "status_code": 200,
            "latency": 2800.0,
            "req_size": 450,
            "res_size": 18500000,
            "rpm": 12,
            "failed_req": 0,
            "is_automation": 1,
            "hour": 4,
            "expected": "Anomaly (Large Payload)",
        },
    ]

    all_features = schema["feature_names"]

    for sc in scenarios:
        # Construct feature vector
        vector = pd.DataFrame(0.0, index=[0], columns=all_features)

        # 1. Raw numerical values
        failure_rate = sc["failed_req"] / (sc["rpm"] + 1.0)
        total_bytes = sc["req_size"] + sc["res_size"]
        byte_ratio = sc["res_size"] / (sc["req_size"] + 1.0)
        raw_num = pd.DataFrame([[
            sc["latency"],
            sc["req_size"],
            sc["res_size"],
            sc["rpm"],
            sc["failed_req"],
            failure_rate,
            total_bytes,
            byte_ratio,
        ]], columns=schema["raw_numerical_features"])

        scaled_num = scaler.transform(raw_num)
        for i, col in enumerate(schema["scaled_numerical_features"]):
            vector.loc[0, col] = scaled_num[0, i]

        # 2. Temporal & Security flags
        hour = sc["hour"]
        vector.loc[0, "hour"] = hour
        vector.loc[0, "day_of_week"] = 2  # Wednesday
        vector.loc[0, "is_weekend"] = 0
        vector.loc[0, "hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
        vector.loc[0, "hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
        vector.loc[0, "status_code"] = sc["status_code"]
        vector.loc[0, "is_error"] = 1 if sc["status_code"] >= 400 else 0
        vector.loc[0, "is_client_error"] = 1 if 400 <= sc["status_code"] < 500 else 0
        vector.loc[0, "is_server_error"] = 1 if sc["status_code"] >= 500 else 0
        vector.loc[0, "is_automation_agent"] = sc["is_automation"]

        # 3. Categoricals
        method_col = f"method_{sc['method']}"
        endpoint_col = f"endpoint_{sc['endpoint']}"
        if method_col in vector.columns:
            vector.loc[0, method_col] = 1
        if endpoint_col in vector.columns:
            vector.loc[0, endpoint_col] = 1

        # Predict
        raw_pred = model.predict(vector)[0]
        is_anomaly = 1 if raw_pred == -1 else 0
        score = -model.decision_function(vector)[0]

        # Map score to Threat Tier
        if score < -0.05:
            threat_tier = "Normal (Safe)"
        elif score < 0.05:
            threat_tier = "Low Threat"
        elif score < 0.15:
            threat_tier = "Medium Threat"
        elif score < 0.25:
            threat_tier = "High Threat"
        else:
            threat_tier = "Critical Threat"

        status_str = "[ALERT: ANOMALY]" if is_anomaly == 1 else "[NORMAL TRAFFIC]"
        print(f"\n{sc['name']}")
        print(f"  Endpoint:      {sc['method']} {sc['endpoint']} (HTTP {sc['status_code']})")
        print(f"  Classification: {status_str} (Ground Expected: {sc['expected']})")
        print(f"  Anomaly Score:  {score:+.4f} -> Threat Tier: {threat_tier}")

    print("\n" + "=" * 65)


def main():
    model, scaler, schema, metadata = load_artifacts()
    print(f"Loaded Champion Model: {metadata['model_name']} ({metadata['algorithm']})")
    print(f"Model Training Date:   {metadata['training_date']}")

    evaluate_test_set(model, schema)
    simulate_live_traffic_scoring(model, scaler, schema)


if __name__ == "__main__":
    main()

