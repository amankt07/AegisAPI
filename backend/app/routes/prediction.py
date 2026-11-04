"""
AegisAPI - Anomaly Detection Prediction Endpoints
Provides real-time single-record and batch traffic anomaly classification
with persistent SQLite database storage.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    BatchPredictionResponse,
    BatchTrafficInput,
    PredictionResponse,
    TrafficRecordInput,
)
from app.services.database_service import database_service
from app.services.model_service import model_service
from app.services.traffic_service import traffic_service

router = APIRouter(tags=["Prediction & Anomaly Detection"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect Single Traffic Record",
    description="Validates incoming API telemetry, executes the Isolation Forest model, and persists record and prediction in SQLite.",
)
def predict_single(record: TrafficRecordInput, db: Session = Depends(get_db)):
    """
    Ingests and analyzes a single API traffic record in real time.
    Executes ML inference, stores the traffic event and its anomaly prediction
    atomically in SQLite, and returns classification diagnostics.
    """
    if not model_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Machine learning inference engine is unavailable: {model_service.error_message}",
        )

    try:
        # Run ML inference
        prediction = model_service.predict_single(record)

        # Transactional SQLite persistence
        database_service.save_traffic_and_prediction(db, record, prediction)

        # Synchronize in-memory telemetry buffer
        traffic_service.record_event(record, prediction)

        return prediction
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference or persistence error: {str(e)}",
        )


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect Batch Traffic Records",
    description="Evaluates up to 500 API traffic logs in a vectorized call and transactionally saves records into SQLite.",
)
def predict_batch(payload: BatchTrafficInput, db: Session = Depends(get_db)):
    """
    Performs vectorized anomaly detection across multiple traffic records.
    Persists all records and predictions into SQLite using per-record savepoints.
    """
    if not model_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Machine learning inference engine is unavailable: {model_service.error_message}",
        )

    records = payload.records
    if not records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch cannot be empty.",
        )

    try:
        predictions, anomaly_count = model_service.predict_batch(records)

        # Transactional SQLite batch persistence
        paired = list(zip(records, predictions))
        success_count, fail_count = database_service.save_batch_traffic_and_predictions(db, paired)

        # Synchronize in-memory buffer
        traffic_service.record_batch(records, predictions)

        total = len(records)
        rate = round((anomaly_count / total * 100.0), 2) if total > 0 else 0.0
        model_name = (
            model_service.metadata.get("model_name", "Isolation Forest")
            if model_service.metadata
            else "Isolation Forest"
        )

        return BatchPredictionResponse(
            total_records=total,
            anomalies_detected=anomaly_count,
            anomaly_rate_percent=rate,
            model_name=model_name,
            predictions=predictions,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch inference or persistence failed: {str(e)}",
        )
