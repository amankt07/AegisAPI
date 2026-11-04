"""
AegisAPI - Health & System Status Endpoints
"""
from fastapi import APIRouter
from app.schemas import HealthResponse
from app.services.model_service import model_service

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Backend Health & Model Status",
    description="Returns backend service health status, API version, and ML model loading state.",
)
async def get_health():
    """Health check endpoint to verify service and machine learning model availability."""
    model_name = (
        model_service.metadata.get("model_name", "Isolation Forest")
        if model_service.is_loaded and model_service.metadata
        else None
    )
    feature_count = (
        model_service.schema.get("total_features", 42)
        if model_service.is_loaded and model_service.schema
        else None
    )

    return HealthResponse(
        status="healthy" if model_service.is_loaded else "degraded",
        service="AegisAPI Backend",
        version="0.1.0",
        model_loaded=model_service.is_loaded,
        model_name=model_name,
        feature_count=feature_count,
    )

