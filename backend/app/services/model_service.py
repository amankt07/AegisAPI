"""
AegisAPI - Machine Learning Model Integration Service
Loads production model artifacts from models/, applies strict preprocessing identical
to training, and performs real-time multivariate anomaly inference.
"""
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd

from app.schemas import PredictionResponse, TrafficRecordInput


class ModelService:
    """
    Singleton service responsible for loading the champion model artifact,
    preprocessor scaler, and feature schema contract for real-time inference.
    """

    def __init__(self, models_dir: Optional[str] = None):
        if models_dir is None:
            # Check environment variable first, otherwise resolve models/ relative to backend/app/services/
            env_models_dir = os.getenv("MODELS_DIR")
            if env_models_dir and os.path.exists(env_models_dir):
                self.models_dir = os.path.abspath(env_models_dir)
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                self.models_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "models"))
        else:
            self.models_dir = models_dir

        self.model: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.schema: Optional[Dict[str, Any]] = None
        self.metadata: Optional[Dict[str, Any]] = None
        self.is_loaded: bool = False
        self.error_message: Optional[str] = None

        self.load_artifacts()

    def load_artifacts(self):
        """Load and validate all production artifacts."""
        try:
            meta_path = os.path.join(self.models_dir, "model_metadata.json")
            schema_path = os.path.join(self.models_dir, "feature_columns.json")
            scaler_path = os.path.join(self.models_dir, "scaler.pkl")

            if not os.path.exists(meta_path):
                raise FileNotFoundError(f"Model metadata not found at {meta_path}")
            if not os.path.exists(schema_path):
                raise FileNotFoundError(f"Feature schema not found at {schema_path}")
            if not os.path.exists(scaler_path):
                raise FileNotFoundError(f"Scaler artifact not found at {scaler_path}")

            with open(meta_path, "r") as f:
                self.metadata = json.load(f)
            with open(schema_path, "r") as f:
                self.schema = json.load(f)

            self.scaler = joblib.load(scaler_path)

            # Dynamically determine the champion model filename
            algorithm = self.metadata.get("algorithm", "")
            if "IsolationForest" in algorithm:
                model_filename = "isolation_forest.pkl"
            elif "LocalOutlierFactor" in algorithm:
                model_filename = "local_outlier_factor.pkl"
            elif "OneClassSVM" in algorithm:
                model_filename = "one_class_svm.pkl"
            else:
                model_filename = "isolation_forest.pkl"

            model_path = os.path.join(self.models_dir, model_filename)
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Champion model artifact not found at {model_path}")

            self.model = joblib.load(model_path)
            self.is_loaded = True
            self.error_message = None
        except Exception as e:
            self.is_loaded = False
            self.error_message = str(e)
            self.model = None
            self.scaler = None
            self.schema = None
            self.metadata = None

    def _transform_records_to_features(self, records: List[TrafficRecordInput]) -> pd.DataFrame:
        """
        Apply identical transformations used in Phase 2 & 3:
        1. Numerical scaling via RobustScaler
        2. Cyclical temporal trigonometric encodings (hour_sin, hour_cos)
        3. Security status and automation user-agent detection
        4. One-hot method & endpoint alignment
        """
        if not self.is_loaded or self.schema is None or self.scaler is None:
            raise RuntimeError(f"ModelService artifacts not loaded: {self.error_message}")

        feature_names = self.schema["feature_names"]
        raw_num_cols = self.schema["raw_numerical_features"]
        scaled_num_cols = self.schema["scaled_numerical_features"]

        n_samples = len(records)
        X_df = pd.DataFrame(0.0, index=range(n_samples), columns=feature_names)

        # Build raw numerical matrix
        raw_num_data = []
        now_utc = datetime.now(timezone.utc)

        automation_signatures = ["curl", "requests", "go-http-client", "hydra", "postman", "apache-httpclient"]

        for idx, rec in enumerate(records):
            # Domain interactions
            failure_rate = float(rec.failed_requests) / (float(rec.requests_per_minute) + 1.0)
            total_bytes = float(rec.request_size_bytes + rec.response_size_bytes)
            byte_ratio = float(rec.response_size_bytes) / (float(rec.request_size_bytes) + 1.0)

            raw_num_data.append([
                rec.response_time_ms,
                rec.request_size_bytes,
                rec.response_size_bytes,
                rec.requests_per_minute,
                rec.failed_requests,
                failure_rate,
                total_bytes,
                byte_ratio,
            ])

            # Temporal calculations
            ts = rec.timestamp if rec.timestamp is not None else now_utc
            hour = ts.hour
            dow = ts.weekday()  # 0=Monday, 6=Sunday
            is_weekend = 1 if dow >= 5 else 0

            X_df.loc[idx, "hour"] = float(hour)
            X_df.loc[idx, "day_of_week"] = float(dow)
            X_df.loc[idx, "is_weekend"] = float(is_weekend)
            X_df.loc[idx, "hour_sin"] = float(np.sin(2 * np.pi * hour / 24.0))
            X_df.loc[idx, "hour_cos"] = float(np.cos(2 * np.pi * hour / 24.0))

            # Security flags
            sc = rec.status_code
            X_df.loc[idx, "status_code"] = float(sc)
            X_df.loc[idx, "is_error"] = 1.0 if sc >= 400 else 0.0
            X_df.loc[idx, "is_client_error"] = 1.0 if 400 <= sc < 500 else 0.0
            X_df.loc[idx, "is_server_error"] = 1.0 if sc >= 500 else 0.0

            ua = (rec.user_agent or "").lower()
            is_auto = 1.0 if any(sig in ua for sig in automation_signatures) else 0.0
            X_df.loc[idx, "is_automation_agent"] = is_auto

            # One-hot methods
            method_col = f"method_{rec.http_method.upper()}"
            if method_col in X_df.columns:
                X_df.loc[idx, method_col] = 1.0

            # One-hot endpoints
            endpoint_col = f"endpoint_{rec.endpoint}"
            if endpoint_col in X_df.columns:
                X_df.loc[idx, endpoint_col] = 1.0

        # Apply RobustScaler transform
        raw_num_df = pd.DataFrame(raw_num_data, columns=raw_num_cols)
        scaled_array = self.scaler.transform(raw_num_df)

        for i, col in enumerate(scaled_num_cols):
            X_df[col] = scaled_array[:, i]

        return X_df

    def _determine_threat_tier(self, score: float) -> str:
        """
        Categorizes continuous anomaly score into actionable security tiers:
        - Safe: Normal baseline behavior
        - Low Threat: Minor variance, warrants observation
        - Medium Threat: Clear anomaly (e.g. brute force / 500 crash)
        - High Threat: Intense volumetric spike or aggressive exfiltration
        - Critical Threat: Severe infrastructure hazard
        """
        if score < 0.0:
            return "Safe"
        elif score < 0.07:
            return "Low Threat"
        elif score < 0.15:
            return "Medium Threat"
        elif score < 0.25:
            return "High Threat"
        else:
            return "Critical Threat"

    def predict_single(self, record: TrafficRecordInput) -> PredictionResponse:
        """Process and score a single incoming traffic record."""
        if not self.is_loaded:
            raise RuntimeError(f"Model service is unavailable: {self.error_message}")

        X_df = self._transform_records_to_features([record])

        # scikit-learn anomaly prediction: -1 = Anomaly, 1 = Normal
        raw_pred = self.model.predict(X_df)[0]
        is_anomaly = 1 if raw_pred == -1 else 0
        prediction_label = "Anomaly" if is_anomaly == 1 else "Normal"

        # Continuous score: -1 * decision_function (higher = more anomalous)
        # Note: decision_function returns positive for inliers, negative for outliers
        # Negating it makes positive scores indicate anomalies
        anomaly_score = round(float(-self.model.decision_function(X_df)[0]), 4)
        threat_level = self._determine_threat_tier(anomaly_score)

        model_name = self.metadata.get("model_name", "Isolation Forest") if self.metadata else "Isolation Forest"
        ts = record.timestamp if record.timestamp is not None else datetime.now(timezone.utc)

        return PredictionResponse(
            is_anomaly=is_anomaly,
            prediction_label=prediction_label,
            anomaly_score=anomaly_score,
            threat_level=threat_level,
            model_name=model_name,
            timestamp=ts,
            details={
                "endpoint": record.endpoint,
                "http_method": record.http_method,
                "status_code": record.status_code,
                "response_time_ms": record.response_time_ms,
                "raw_decision_score": -anomaly_score,
                "score_direction": "higher_is_more_anomalous",
            },
        )

    def predict_batch(self, records: List[TrafficRecordInput]) -> Tuple[List[PredictionResponse], int]:
        """Perform high-throughput vector inference on a batch of traffic records."""
        if not self.is_loaded:
            raise RuntimeError(f"Model service is unavailable: {self.error_message}")

        if not records:
            return [], 0

        X_df = self._transform_records_to_features(records)
        raw_preds = self.model.predict(X_df)
        raw_scores = -self.model.decision_function(X_df)

        model_name = self.metadata.get("model_name", "Isolation Forest") if self.metadata else "Isolation Forest"
        now_utc = datetime.now(timezone.utc)

        responses: List[PredictionResponse] = []
        anomaly_count = 0

        for idx, rec in enumerate(records):
            is_anom = 1 if raw_preds[idx] == -1 else 0
            if is_anom == 1:
                anomaly_count += 1
            pred_label = "Anomaly" if is_anom == 1 else "Normal"
            score = round(float(raw_scores[idx]), 4)
            threat = self._determine_threat_tier(score)
            ts = rec.timestamp if rec.timestamp is not None else now_utc

            responses.append(
                PredictionResponse(
                    is_anomaly=is_anom,
                    prediction_label=pred_label,
                    anomaly_score=score,
                    threat_level=threat,
                    model_name=model_name,
                    timestamp=ts,
                    details={
                        "endpoint": rec.endpoint,
                        "http_method": rec.http_method,
                        "status_code": rec.status_code,
                        "response_time_ms": rec.response_time_ms,
                    },
                )
            )

        return responses, anomaly_count

    def get_model_info(self) -> Dict[str, Any]:
        """Return production model metadata and schema summary."""
        if not self.is_loaded or self.metadata is None or self.schema is None:
            raise RuntimeError("Model service artifacts are not loaded.")

        return {
            "model_name": self.metadata.get("model_name", "Isolation Forest"),
            "algorithm": self.metadata.get("algorithm", "sklearn.ensemble.IsolationForest"),
            "training_date": self.metadata.get("training_date", "Unknown"),
            "feature_count": self.schema.get("total_features", 42),
            "train_test_split": self.metadata.get("dataset", {}).get("train_test_split_ratio", "80/20"),
            "status": self.metadata.get("status", "production_champion"),
            "hyperparameters": self.metadata.get("hyperparameters", {}),
            "evaluation_metrics": self.metadata.get("evaluation_metrics", {}),
            "score_interpretation": (
                "Continuous Anomaly Score = -1 * decision_function(X). "
                "Negative values indicate normal baseline traffic. "
                "Values >= 0 indicate anomalous deviations. Higher values represent severe threats."
            ),
            "feature_names": self.schema.get("feature_names", []),
        }


# Global model service instance
model_service = ModelService()

