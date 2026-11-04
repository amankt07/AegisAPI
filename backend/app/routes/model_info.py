"""
AegisAPI - Machine Learning Model Information & Metadata Endpoints
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas import ModelInfoResponse
from app.services.model_service import model_service

router = APIRouter(tags=["Model Metadata"])


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    summary="Get Production Model Information",
    description="Returns metadata about the active ML model, evaluation benchmarks, hyperparameters, and feature contract.",
)
async def get_model_info():
    """
    Exposes transparent model audit metadata:
    - Active algorithm name and hyperparameters
    - Training date and 80/20 train/test split configuration
    - Empirical evaluation metrics (Precision, Recall, F1, ROC-AUC, PR-AUC)
    - Full 42-feature schema contract
    - Continuous anomaly score interpretation guide
    """
    if not model_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model metadata is unavailable: {model_service.error_message}",
        )

    try:
        info = model_service.get_model_info()
        return ModelInfoResponse(**info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model metadata: {str(e)}",
        )

