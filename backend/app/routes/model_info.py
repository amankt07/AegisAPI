"""
AegisAPI - Machine Learning Model Information & Metadata Endpoints
Delivers active model audit metadata synchronized from SQLite and model_metadata.json.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ModelInfoResponse
from app.services.database_service import database_service
from app.services.model_service import model_service

router = APIRouter(tags=["Model Metadata"])


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    summary="Get Production Model Information",
    description="Returns metadata about the active ML model, evaluation benchmarks, hyperparameters, and feature contract.",
)
def get_model_info(db: Session = Depends(get_db)):
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
        # Retrieve from SQLite with fallback to loaded memory metadata
        db_model_info = database_service.get_active_model_info(
            db, fallback_metadata=model_service.metadata
        )

        base_info = model_service.get_model_info()

        if db_model_info:
            return ModelInfoResponse(
                model_name=db_model_info.model_name,
                algorithm=db_model_info.algorithm,
                training_date=str(db_model_info.training_date or base_info.get("training_date")),
                feature_count=db_model_info.feature_count or base_info.get("feature_count", 42),
                train_test_split=base_info.get("train_test_split", "80/20"),
                status="production_champion" if db_model_info.is_active else "inactive",
                hyperparameters=base_info.get("hyperparameters", {}),
                evaluation_metrics=db_model_info.evaluation_metrics or base_info.get("evaluation_metrics", {}),
                score_interpretation=base_info.get("score_interpretation", ""),
                feature_names=base_info.get("feature_names", []),
            )

        return ModelInfoResponse(**base_info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model metadata: {str(e)}",
        )
