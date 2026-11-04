"""
AegisAPI - Relational Database Service Layer
Implements transactional operations for saving API traffic logs and ML anomaly predictions,
fetching historical telemetry feeds, computing dynamic statistics, and querying model metadata.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models import AnomalyPrediction, ModelInformation, TrafficEvent
from app.schemas import DashboardStatistics, PredictionResponse, TrafficRecordInput


class DatabaseService:
    """
    Encapsulates all SQLAlchemy ORM database queries and transactional persistence.
    """

    @staticmethod
    def save_traffic_and_prediction(
        db: Session, record: TrafficRecordInput, prediction: PredictionResponse
    ) -> Tuple[TrafficEvent, AnomalyPrediction]:
        """
        Atomically saves a TrafficEvent and its corresponding AnomalyPrediction
        within a single database transaction. Rolls back on error.
        """
        try:
            event_ts = record.timestamp or prediction.timestamp or datetime.now(timezone.utc)

            traffic_event = TrafficEvent(
                timestamp=event_ts,
                source_ip=record.source_ip or "127.0.0.1",
                endpoint=record.endpoint,
                http_method=record.http_method,
                status_code=record.status_code,
                response_time_ms=record.response_time_ms,
                request_size_bytes=record.request_size_bytes,
                response_size_bytes=record.response_size_bytes,
                requests_per_minute=record.requests_per_minute,
                failed_requests=record.failed_requests,
                user_agent=record.user_agent or "Unknown",
            )
            db.add(traffic_event)
            db.flush()  # Populates traffic_event.id for foreign key

            anomaly_prediction = AnomalyPrediction(
                traffic_event_id=traffic_event.id,
                timestamp=prediction.timestamp or event_ts,
                is_anomaly=bool(prediction.is_anomaly == 1),
                prediction_label=prediction.prediction_label,
                anomaly_score=prediction.anomaly_score,
                model_name=prediction.model_name,
            )
            db.add(anomaly_prediction)
            db.commit()

            db.refresh(traffic_event)
            db.refresh(anomaly_prediction)
            return traffic_event, anomaly_prediction
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def save_batch_traffic_and_predictions(
        db: Session, items: List[Tuple[TrafficRecordInput, PredictionResponse]]
    ) -> Tuple[int, int]:
        """
        Persists a batch of traffic events and predictions.
        Uses savepoints per item to isolate individual record errors without corrupting the batch.
        Returns (successful_records, failed_records).
        """
        success_count = 0
        fail_count = 0

        for record, prediction in items:
            try:
                # Use a savepoint for per-record isolation
                with db.begin_nested():
                    event_ts = record.timestamp or prediction.timestamp or datetime.now(timezone.utc)
                    traffic_event = TrafficEvent(
                        timestamp=event_ts,
                        source_ip=record.source_ip or "127.0.0.1",
                        endpoint=record.endpoint,
                        http_method=record.http_method,
                        status_code=record.status_code,
                        response_time_ms=record.response_time_ms,
                        request_size_bytes=record.request_size_bytes,
                        response_size_bytes=record.response_size_bytes,
                        requests_per_minute=record.requests_per_minute,
                        failed_requests=record.failed_requests,
                        user_agent=record.user_agent or "Unknown",
                    )
                    db.add(traffic_event)
                    db.flush()

                    anomaly_prediction = AnomalyPrediction(
                        traffic_event_id=traffic_event.id,
                        timestamp=prediction.timestamp or event_ts,
                        is_anomaly=bool(prediction.is_anomaly == 1),
                        prediction_label=prediction.prediction_label,
                        anomaly_score=prediction.anomaly_score,
                        model_name=prediction.model_name,
                    )
                    db.add(anomaly_prediction)
                success_count += 1
            except Exception:
                fail_count += 1

        db.commit()
        return success_count, fail_count

    @staticmethod
    def get_recent_traffic(db: Session, limit: int = 50, offset: int = 0) -> List[TrafficEvent]:
        """
        Retrieves recent traffic events sorted chronologically (newest first),
        eagerly joining the corresponding prediction.
        """
        return (
            db.query(TrafficEvent)
            .options(joinedload(TrafficEvent.prediction))
            .order_by(TrafficEvent.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_recent_anomalies(db: Session, limit: int = 50, offset: int = 0) -> List[AnomalyPrediction]:
        """
        Retrieves recent anomalous predictions (is_anomaly == True),
        eagerly joining the parent TrafficEvent for telemetry details.
        """
        return (
            db.query(AnomalyPrediction)
            .options(joinedload(AnomalyPrediction.traffic_event))
            .filter(AnomalyPrediction.is_anomaly == True)
            .order_by(AnomalyPrediction.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def calculate_statistics(db: Session) -> DashboardStatistics:
        """
        Executes SQL aggregate functions over SQLite tables to calculate
        live operational security telemetry.
        """
        total_requests = db.query(func.count(TrafficEvent.id)).scalar() or 0
        anomalous_requests = (
            db.query(func.count(AnomalyPrediction.id))
            .filter(AnomalyPrediction.is_anomaly == True)
            .scalar()
            or 0
        )
        normal_requests = max(0, total_requests - anomalous_requests)
        anomaly_pct = round((anomalous_requests / total_requests * 100.0), 2) if total_requests > 0 else 0.0

        avg_latency = db.query(func.avg(TrafficEvent.response_time_ms)).scalar() or 0.0
        avg_latency = round(float(avg_latency), 2)

        http_errors = (
            db.query(func.count(TrafficEvent.id))
            .filter(TrafficEvent.status_code >= 400)
            .scalar()
            or 0
        )

        # Threat tier categorization using SQL expressions
        # Safe (< 0.0), Low [0.0, 0.07), Medium [0.07, 0.15), High [0.15, 0.25), Critical (>= 0.25)
        threat_distribution = {
            "Safe": db.query(func.count(AnomalyPrediction.id)).filter(AnomalyPrediction.anomaly_score < 0.0).scalar() or 0,
            "Low Threat": db.query(func.count(AnomalyPrediction.id)).filter(AnomalyPrediction.anomaly_score >= 0.0, AnomalyPrediction.anomaly_score < 0.07).scalar() or 0,
            "Medium Threat": db.query(func.count(AnomalyPrediction.id)).filter(AnomalyPrediction.anomaly_score >= 0.07, AnomalyPrediction.anomaly_score < 0.15).scalar() or 0,
            "High Threat": db.query(func.count(AnomalyPrediction.id)).filter(AnomalyPrediction.anomaly_score >= 0.15, AnomalyPrediction.anomaly_score < 0.25).scalar() or 0,
            "Critical Threat": db.query(func.count(AnomalyPrediction.id)).filter(AnomalyPrediction.anomaly_score >= 0.25).scalar() or 0,
        }

        # Top 5 anomalous endpoints
        top_endpoints_query = (
            db.query(TrafficEvent.endpoint, func.count(TrafficEvent.id))
            .join(AnomalyPrediction, TrafficEvent.id == AnomalyPrediction.traffic_event_id)
            .filter(AnomalyPrediction.is_anomaly == True)
            .group_by(TrafficEvent.endpoint)
            .order_by(func.count(TrafficEvent.id).desc())
            .limit(5)
            .all()
        )
        top_endpoints = {ep: count for ep, count in top_endpoints_query}

        return DashboardStatistics(
            total_processed_requests=total_requests,
            normal_requests=normal_requests,
            anomalous_requests=anomalous_requests,
            anomaly_percentage=anomaly_pct,
            average_response_time_ms=avg_latency,
            http_error_count=http_errors,
            recent_traffic_volume=total_requests,
            threat_level_distribution=threat_distribution,
            top_anomalous_endpoints=top_endpoints,
        )

    @staticmethod
    def get_active_model_info(db: Session, fallback_metadata: Optional[dict] = None) -> Optional[ModelInformation]:
        """
        Retrieves the active champion model audit record from SQLite.
        If not yet seeded, synchronizes using fallback metadata.
        """
        model_info = (
            db.query(ModelInformation)
            .filter(ModelInformation.is_active == True)
            .order_by(ModelInformation.id.desc())
            .first()
        )
        if model_info:
            return model_info

        # Seed if fallback provided
        if fallback_metadata:
            model_info = ModelInformation(
                model_name=fallback_metadata.get("model_name", "Isolation Forest"),
                algorithm=fallback_metadata.get("algorithm", "sklearn.ensemble._iforest.IsolationForest"),
                training_date=str(fallback_metadata.get("training_date", "")),
                training_records=fallback_metadata.get("dataset", {}).get("train_records", 24000),
                feature_count=fallback_metadata.get("dataset", {}).get("feature_count", 42),
                evaluation_metrics=fallback_metadata.get("evaluation_metrics", {}),
                is_active=True,
            )
            db.add(model_info)
            db.commit()
            db.refresh(model_info)
            return model_info

        return None


database_service = DatabaseService()

