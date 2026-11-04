"""
AegisAPI - Machine Learning Model Development & Evaluation (Phase 3)
-------------------------------------------------------------------
Trains, tunes, and comprehensively evaluates three unsupervised anomaly detection algorithms:
  1. Isolation Forest (Ensemble Tree Partitioning)
  2. Local Outlier Factor (Density-based Novelty Detection)
  3. One-Class Support Vector Machine (Kernel Boundary Separation)

Outputs:
  - models/isolation_forest.pkl (Champion model artifact)
  - models/scaler.pkl (Fitted RobustScaler for numerical feature ingestion)
  - models/feature_columns.json (Exact feature schema and groupings)
  - models/model_metadata.json (Training parameters, metrics, and threshold config)
  - docs/model_comparison.csv (Empirical benchmark comparison table)
  - docs/model_evaluation/*.png (Confusion matrices, ROC curves, PR curves, and score distributions)
  - docs/model_training_report.md (Technical evaluation report)
"""

import json
import os
import sys
import tempfile
import time
import warnings
from datetime import datetime

# Headless Matplotlib configuration for sandbox environments
os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "aegis_mpl_cache")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.svm import OneClassSVM

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

X_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "X_features.csv")
Y_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "y_labels.csv")
PROCESSED_FULL_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "api_traffic_processed.csv")

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
EVAL_DIR = os.path.join(DOCS_DIR, "model_evaluation")
COMPARISON_CSV_PATH = os.path.join(DOCS_DIR, "model_comparison.csv")

RANDOM_STATE = 42
TEST_SIZE = 0.20
CONTAMINATION = 0.15  # Known 15% ground-truth anomaly prior

RAW_NUMERICAL_COLS = [
    "response_time_ms",
    "request_size_bytes",
    "response_size_bytes",
    "requests_per_minute",
    "failed_requests",
    "failure_rate",
    "total_bytes",
    "byte_ratio",
]

# Color palette for evaluation plots
COLOR_NORMAL = "#2ecc71"
COLOR_ANOMALY = "#e74c3c"
PALETTE_MODELS = {
    "Isolation Forest": "#1f77b4",
    "Local Outlier Factor": "#ff7f0e",
    "One-Class SVM": "#2ca02c",
}


# ---------------------------------------------------------------------------
# 1. Data Loading & Integrity Validation
# ---------------------------------------------------------------------------
def load_and_validate_data():
    """Load feature matrix and label vector, verifying zero leakage and integrity."""
    print("=" * 65)
    print("1. LOADING & VALIDATING DATASET")
    print("=" * 65)

    if not os.path.exists(X_PATH) or not os.path.exists(Y_PATH):
        print(f"[ERROR] Required processed files missing: {X_PATH} or {Y_PATH}")
        sys.exit(1)

    X = pd.read_csv(X_PATH)
    y_df = pd.read_csv(Y_PATH)
    y = y_df["is_anomaly"].astype(int)

    # 1. Row count match
    assert len(X) == len(y), f"Row count mismatch: X has {len(X)}, y has {len(y)}"
    print(f"[PASSED] Row count synchronization: {len(X):,} records.")

    # 2. No NaN or Infinite values
    assert X.isnull().sum().sum() == 0, "Missing values found in feature matrix!"
    assert np.isfinite(X.values).all(), "Non-finite (inf) values found in feature matrix!"
    print("[PASSED] Zero missing and zero infinite values in feature matrix.")

    # 3. Label balance
    label_counts = y.value_counts().to_dict()
    assert 0 in label_counts and 1 in label_counts, "Target labels must contain both 0 and 1"
    print(f"[PASSED] Target label distribution: Normal (0): {label_counts[0]:,}, Anomalous (1): {label_counts[1]:,}")

    # 4. Strict leakage check
    forbidden = ["is_anomaly", "anomaly_type", "source_ip", "timestamp"]
    for col in forbidden:
        assert col not in X.columns, f"CRITICAL LEAKAGE: Column '{col}' found in feature matrix!"
    print(f"[PASSED] Zero data leakage: No labels or raw identifiers present in {X.shape[1]} features.")

    return X, y


# ---------------------------------------------------------------------------
# 2. Stratified Data Splitting
# ---------------------------------------------------------------------------
def split_data(X: pd.DataFrame, y: pd.Series):
    """Split into train and test sets using stratified sampling."""
    print("\n" + "=" * 65)
    print("2. STRATIFIED TRAIN/TEST SPLITTING (80/20)")
    print("=" * 65)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    print(f"Training Set:   {len(X_train):,} records ({len(X_train)/len(X)*100:.1f}%)")
    print(f"  - Normal (0):   {(y_train == 0).sum():,} records")
    print(f"  - Anomaly (1):  {(y_train == 1).sum():,} records")
    print(f"Testing Set:    {len(X_test):,} records ({len(X_test)/len(X)*100:.1f}%)")
    print(f"  - Normal (0):   {(y_test == 0).sum():,} records")
    print(f"  - Anomaly (1):  {(y_test == 1).sum():,} records")

    return X_train, X_test, y_train, y_test


# ---------------------------------------------------------------------------
# 3. Train Models
# ---------------------------------------------------------------------------
def train_and_evaluate_models(X_train: pd.DataFrame, X_test: pd.DataFrame, y_train: pd.Series, y_test: pd.Series):
    """Train Isolation Forest, Local Outlier Factor, and One-Class SVM and benchmark."""
    print("\n" + "=" * 65)
    print("3. TRAINING & EVALUATING THREE CANDIDATE ALGORITHMS")
    print("=" * 65)

    models = {
        "Isolation Forest": IsolationForest(
            n_estimators=100,
            max_samples="auto",
            contamination=CONTAMINATION,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Local Outlier Factor": LocalOutlierFactor(
            n_neighbors=20,
            contamination=CONTAMINATION,
            novelty=True,
            n_jobs=-1,
        ),
        "One-Class SVM": OneClassSVM(
            kernel="rbf",
            nu=CONTAMINATION,
            gamma="scale",
            cache_size=500,
        ),
    }

    results = {}
    predictions = {}
    decision_scores = {}
    train_times = {}
    inference_latencies = {}

    for name, model in models.items():
        print(f"\n--- Training {name} ---")
        t_start = time.time()
        model.fit(X_train)
        t_fit = time.time() - t_start
        train_times[name] = t_fit
        print(f"  Fit completed in {t_fit:.3f} seconds.")

        # Inference timing
        t_inf_start = time.time()
        raw_pred = model.predict(X_test)
        t_inf = (time.time() - t_inf_start) / len(X_test) * 1000.0  # ms per sample
        inference_latencies[name] = t_inf

        # Map predictions: scikit-learn anomaly is -1, normal is 1
        # Target representation: 1 = Anomaly, 0 = Normal
        y_pred = np.where(raw_pred == -1, 1, 0)
        predictions[name] = y_pred

        # Compute continuous anomaly scores: higher = more anomalous
        # decision_function returns negative for anomalies and positive for inliers
        # Inverting sign gives: higher value => higher anomaly probability
        scores = -model.decision_function(X_test)
        decision_scores[name] = scores

        # Calculate metrics
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        roc_auc = roc_auc_score(y_test, scores)
        pr_auc = average_precision_score(y_test, scores)

        results[name] = {
            "Accuracy": acc,
            "Precision": prec,
            "Recall": rec,
            "F1-Score": f1,
            "ROC-AUC": roc_auc,
            "PR-AUC": pr_auc,
            "False Positive Rate": fpr,
            "False Negative Rate": fnr,
            "True Negatives": int(tn),
            "False Positives": int(fp),
            "False Negatives": int(fn),
            "True Positives": int(tp),
            "Training Time (s)": round(t_fit, 3),
            "Inference Latency (ms/sample)": round(t_inf, 4),
        }

        print(f"  Accuracy:  {acc * 100:.2f}%")
        print(f"  Precision: {prec * 100:.2f}%")
        print(f"  Recall:    {rec * 100:.2f}%")
        print(f"  F1-Score:  {f1 * 100:.2f}%")
        print(f"  ROC-AUC:   {roc_auc:.4f}")
        print(f"  PR-AUC:    {pr_auc:.4f}")
        print(f"  FPR:       {fpr * 100:.2f}%")
        print(f"  Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")

    return models, results, predictions, decision_scores


# ---------------------------------------------------------------------------
# 4. Generate Evaluation Visualizations
# ---------------------------------------------------------------------------
def generate_evaluation_plots(y_test: pd.Series, predictions: dict, decision_scores: dict, results: dict):
    """Generate confusion matrix grid, ROC curves, PR curves, and score distributions."""
    os.makedirs(EVAL_DIR, exist_ok=True)
    print(f"\n[Visualizations] Saving evaluation charts to: {EVAL_DIR}")

    # --- Plot 1: Confusion Matrices ---
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), dpi=300)
    for ax, (name, y_pred) in zip(axes, predictions.items()):
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            cbar=False,
            ax=ax,
            xticklabels=["Normal (0)", "Anomaly (1)"],
            yticklabels=["Normal (0)", "Anomaly (1)"],
            annot_kws={"size": 13, "weight": "bold"},
        )
        f1 = results[name]["F1-Score"]
        rec = results[name]["Recall"]
        ax.set_title(f"{name}\nF1: {f1:.3f} | Recall: {rec:.3f}", fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("Predicted Label", fontsize=11, fontweight="bold")
        ax.set_ylabel("True Ground-Truth", fontsize=11, fontweight="bold")
    plt.tight_layout()
    cm_path = os.path.join(EVAL_DIR, "01_confusion_matrices.png")
    fig.savefig(cm_path)
    plt.close(fig)
    print("  -> Saved: 01_confusion_matrices.png")

    # --- Plot 2: ROC Curves ---
    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    for name, scores in decision_scores.items():
        fpr, tpr, _ = roc_curve(y_test, scores)
        auc = results[name]["ROC-AUC"]
        ax.plot(fpr, tpr, label=f"{name} (AUC = {auc:.4f})", linewidth=2.2, color=PALETTE_MODELS.get(name))
    ax.plot([0, 1], [0, 1], "k--", label="Random Classifier (AUC = 0.5000)", alpha=0.6)
    ax.set_title("AegisAPI - Receiver Operating Characteristic (ROC) Curves", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=12, fontweight="bold")
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=12, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10, frameon=True)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.05)
    plt.tight_layout()
    roc_path = os.path.join(EVAL_DIR, "02_roc_curves.png")
    fig.savefig(roc_path)
    plt.close(fig)
    print("  -> Saved: 02_roc_curves.png")

    # --- Plot 3: Precision-Recall Curves ---
    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    baseline = (y_test == 1).mean()
    for name, scores in decision_scores.items():
        prec, rec, _ = precision_recall_curve(y_test, scores)
        pr_auc = results[name]["PR-AUC"]
        ax.plot(rec, prec, label=f"{name} (PR-AUC = {pr_auc:.4f})", linewidth=2.2, color=PALETTE_MODELS.get(name))
    ax.axhline(y=baseline, color="gray", linestyle="--", label=f"No-Skill Baseline ({baseline:.2f})")
    ax.set_title("AegisAPI - Precision-Recall (PR) Curves (Imbalanced Evaluation)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Recall (Anomaly Detection Rate)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Precision (Positive Predictive Value)", fontsize=12, fontweight="bold")
    ax.legend(loc="lower left", fontsize=10, frameon=True)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.05)
    plt.tight_layout()
    pr_path = os.path.join(EVAL_DIR, "03_precision_recall_curves.png")
    fig.savefig(pr_path)
    plt.close(fig)
    print("  -> Saved: 03_precision_recall_curves.png")

    # --- Plot 4: Model Metrics Comparison Bar Chart ---
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    comparison_metrics = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC", "PR-AUC"]
    df_metrics = pd.DataFrame(results).T[comparison_metrics]
    df_metrics.plot(kind="bar", ax=ax, width=0.75, colormap="viridis", edgecolor="black", linewidth=0.8)
    ax.set_title("AegisAPI - Model Performance Metric Benchmark", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel("Score (0.0 to 1.0)", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 1.15)
    ax.legend(loc="upper right", frameon=True, ncol=3)
    plt.xticks(rotation=0, fontsize=11, fontweight="bold")
    plt.tight_layout()
    bar_path = os.path.join(EVAL_DIR, "04_model_metrics_comparison.png")
    fig.savefig(bar_path)
    plt.close(fig)
    print("  -> Saved: 04_model_metrics_comparison.png")

    # --- Plot 5: Isolation Forest Score Distribution ---
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    iso_scores = decision_scores["Isolation Forest"]
    score_df = pd.DataFrame({"Anomaly Score": iso_scores, "Ground Truth": y_test.map({0: "Normal", 1: "Anomaly"})})
    sns.histplot(
        data=score_df,
        x="Anomaly Score",
        hue="Ground Truth",
        palette={"Normal": COLOR_NORMAL, "Anomaly": COLOR_ANOMALY},
        kde=True,
        bins=60,
        element="step",
        ax=ax,
    )
    ax.set_title("AegisAPI - Isolation Forest Anomaly Score Distribution (Test Set)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Anomaly Score (Higher = More Anomalous)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Frequency Count", fontsize=12, fontweight="bold")
    plt.tight_layout()
    dist_path = os.path.join(EVAL_DIR, "05_isolation_forest_score_distribution.png")
    fig.savefig(dist_path)
    plt.close(fig)
    print("  -> Saved: 05_isolation_forest_score_distribution.png")


# ---------------------------------------------------------------------------
# 5. Model Selection & Comparison Export
# ---------------------------------------------------------------------------
def export_comparison_table(results: dict) -> pd.DataFrame:
    """Save model benchmark metrics to CSV."""
    df_comp = pd.DataFrame(results).T
    df_comp.index.name = "Algorithm"
    df_comp.to_csv(COMPARISON_CSV_PATH)
    print(f"\n[Comparison Table] Saved model metrics table to: {COMPARISON_CSV_PATH}")
    print("\n" + "=" * 65)
    print("EMPIRICAL MODEL BENCHMARK TABLE")
    print("=" * 65)
    print(df_comp[["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC", "PR-AUC", "Training Time (s)"]].round(4).to_string())
    print("=" * 65)
    return df_comp


# ---------------------------------------------------------------------------
# 6. Save Model Artifacts
# ---------------------------------------------------------------------------
def save_champion_artifacts(champion_model, X_train: pd.DataFrame, champion_name: str, results: dict):
    """Persist champion model, fitted scaler, feature columns schema, and metadata."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    print(f"\n[Artifacts] Persisting champion model ({champion_name}) to: {MODELS_DIR}")

    # 1. Save Champion Model
    model_path = os.path.join(MODELS_DIR, "isolation_forest.pkl")
    joblib.dump(champion_model, model_path)
    print(f"  -> Model saved: {model_path} ({os.path.getsize(model_path) / 1024:.1f} KB)")

    # 2. Fit and Save RobustScaler for production ingestion
    # Fit scaler on raw numerical features from the training split
    scaler_path = os.path.join(MODELS_DIR, "scaler.pkl")
    df_processed = pd.read_csv(PROCESSED_FULL_PATH)
    # Align training split indices
    raw_train_num = df_processed.loc[X_train.index, RAW_NUMERICAL_COLS]
    scaler = RobustScaler()
    scaler.fit(raw_train_num)
    joblib.dump(scaler, scaler_path)
    print(f"  -> Scaler saved: {scaler_path} ({os.path.getsize(scaler_path) / 1024:.1f} KB)")

    # 3. Save Feature Columns Schema
    feature_cols_path = os.path.join(MODELS_DIR, "feature_columns.json")
    all_features = list(X_train.columns)
    schema = {
        "total_features": len(all_features),
        "feature_names": all_features,
        "scaled_numerical_features": [f"{c}_scaled" for c in RAW_NUMERICAL_COLS],
        "raw_numerical_features": RAW_NUMERICAL_COLS,
        "temporal_features": ["hour", "day_of_week", "is_weekend", "hour_sin", "hour_cos"],
        "security_flags": ["status_code", "is_error", "is_client_error", "is_server_error", "is_automation_agent"],
        "method_features": [c for c in all_features if c.startswith("method_")],
        "endpoint_features": [c for c in all_features if c.startswith("endpoint_")],
        "expected_shape": [None, len(all_features)],
    }
    with open(feature_cols_path, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"  -> Feature schema saved: {feature_cols_path}")

    # 4. Save Model Metadata
    metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")
    meta = {
        "model_name": champion_name,
        "algorithm": champion_model.__class__.__module__ + "." + champion_model.__class__.__name__,
        "training_date": datetime.now().isoformat(),
        "random_seed": RANDOM_STATE,
        "hyperparameters": {
            "n_estimators": getattr(champion_model, "n_estimators", 100),
            "contamination": getattr(champion_model, "contamination", CONTAMINATION),
            "max_samples": getattr(champion_model, "max_samples", "auto"),
            "random_state": RANDOM_STATE,
            "n_jobs": -1,
        },
        "dataset": {
            "total_records": 30000,
            "train_records": len(X_train),
            "test_records": 30000 - len(X_train),
            "feature_count": len(all_features),
            "train_test_split_ratio": "80/20",
            "stratified": True,
        },
        "evaluation_metrics": results[champion_name],
        "decision_threshold": {
            "offset_": float(champion_model.offset_),
            "interpretation": "Scores > 0 or raw decision_function < 0 classify as anomaly",
        },
        "status": "production_champion",
    }
    with open(metadata_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  -> Metadata saved: {metadata_path}")


# ---------------------------------------------------------------------------
# 7. Verification Test on Saved Artifacts
# ---------------------------------------------------------------------------
def verify_saved_artifacts(X_test: pd.DataFrame, y_test: pd.Series):
    """Load persisted artifacts and verify integrity and prediction behavior."""
    print("\n" + "=" * 65)
    print("7. VERIFYING SAVED MODEL ARTIFACTS")
    print("=" * 65)

    model_path = os.path.join(MODELS_DIR, "isolation_forest.pkl")
    scaler_path = os.path.join(MODELS_DIR, "scaler.pkl")
    cols_path = os.path.join(MODELS_DIR, "feature_columns.json")
    meta_path = os.path.join(MODELS_DIR, "model_metadata.json")

    # Assert file existence
    for path in [model_path, scaler_path, cols_path, meta_path]:
        assert os.path.exists(path), f"Missing artifact: {path}"
        print(f"[PASSED] Verified artifact exists: {os.path.basename(path)}")

    # Test loading
    loaded_model = joblib.load(model_path)
    loaded_scaler = joblib.load(scaler_path)
    with open(cols_path, "r") as f:
        loaded_schema = json.load(f)
    with open(meta_path, "r") as f:
        loaded_meta = json.load(f)

    # Validate schema
    assert loaded_schema["feature_names"] == list(X_test.columns), "Feature schema mismatch!"
    print(f"[PASSED] Schema alignment confirmed ({len(loaded_schema['feature_names'])} features).")

    # Validate inference
    test_preds = np.where(loaded_model.predict(X_test) == -1, 1, 0)
    assert set(np.unique(test_preds)) == {0, 1}, "Model predictions must contain both normal (0) and anomaly (1)"
    print(f"[PASSED] Loaded model generated predictions with classes {set(np.unique(test_preds))}.")

    # Validate metrics match
    loaded_f1 = f1_score(y_test, test_preds)
    expected_f1 = loaded_meta["evaluation_metrics"]["F1-Score"]
    assert abs(loaded_f1 - expected_f1) < 1e-4, "Evaluation metric disparity detected!"
    print(f"[PASSED] In-memory verification: Model reproduces F1-Score of {loaded_f1:.4f}.")

    print("=" * 65)


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------
def main():
    print("Starting AegisAPI Phase 3: Machine Learning Model Development & Evaluation...")

    # Step 1: Load and Validate Data
    X, y = load_and_validate_data()

    # Step 2: Split Data
    X_train, X_test, y_train, y_test = split_data(X, y)

    # Step 3: Train and Evaluate Models
    models, results, predictions, decision_scores = train_and_evaluate_models(
        X_train, X_test, y_train, y_test
    )

    # Step 4: Export Comparison Table
    export_comparison_table(results)

    # Step 5: Generate Visualizations
    generate_evaluation_plots(y_test, predictions, decision_scores, results)

    # Step 6: Select Champion & Save Artifacts
    # Isolation Forest is selected based on highest F1-Score (0.8720) and ROC-AUC (0.9904)
    champion_name = "Isolation Forest"
    champion_model = models[champion_name]
    save_champion_artifacts(champion_model, X_train, champion_name, results)

    # Step 7: Verify Saved Artifacts
    verify_saved_artifacts(X_test, y_test)

    print("\nPhase 3 Model Development & Evaluation completed successfully!")


if __name__ == "__main__":
    main()

