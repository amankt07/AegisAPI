"""
AegisAPI - Anomaly Detection Prediction Endpoints
Provides real-time single-record and batch traffic anomaly classification.
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas import (
    BatchPredictionResponse,
    BatchTrafficInput,
    PredictionResponse,
    TrafficRecordInput,
)
from app.services.model_service import model_service
from app.services.traffic_service import traffic_service

router = APIRouter(tags=["Prediction & Anomaly Detection"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect Single Traffic Record",
    description="Validates incoming API telemetry, executes the Isolation Forest model, and returns anomaly classification.",
)
async def predict_single(record: TrafficRecordInput):
    """
    Ingests and analyzes a single API traffic record in real time.
    Flags volumetric bursts, brute-force patterns, 5xx server failures,
    abnormal latencies, or suspicious payload transfers.
    """
    if not model_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Machine learning inference engine is unavailable: {model_service.error_message}",
        )

    try:
        prediction = model_service.predict_single(record)
        # Record into memory telemetry buffer
        traffic_service.record_event(record, prediction)
        return prediction
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error during feature processing: {str(e)}",
        )


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect Batch Traffic Records",
    description="Evaluates up to 500 API traffic logs in a vectorized high-throughput inference call.",
)
async def predict_batch(payload: BatchTrafficInput):
    """
    Performs vectorized anomaly detection across multiple traffic records.
    Returns per-record anomaly classifications and aggregated threat counts.
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch inference failed: {str(e)}",
        )

