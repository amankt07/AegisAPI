"""
AegisAPI - Dashboard Telemetry Statistics Endpoints
"""
from fastapi import APIRouter
from app.schemas import DashboardStatistics
from app.services.traffic_service import traffic_service

router = APIRouter(tags=["Statistics & KPIs"])


@router.get(
    "/statistics",
    response_model=DashboardStatistics,
    summary="Get Aggregated Dashboard Statistics",
    description="Returns high-level security metrics: total requests, anomaly count, error rate, and threat tiers.",
)
async def get_statistics():
    """
    Computes and delivers real-time aggregated metrics:
    - Total processed requests
    - Normal vs. anomalous request counts and percentage
    - Average latency in milliseconds
    - HTTP error counts (status codes >= 400)
    - Threat tier breakdown and top anomalous endpoints
    """
    return traffic_service.get_statistics()

