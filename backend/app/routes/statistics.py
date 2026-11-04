"""
AegisAPI - Dashboard Telemetry Statistics Endpoints
Calculates aggregated security metrics directly from the SQLite database.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DashboardStatistics
from app.services.database_service import database_service
from app.services.traffic_service import traffic_service

router = APIRouter(tags=["Statistics & KPIs"])


@router.get(
    "/statistics",
    response_model=DashboardStatistics,
    summary="Get Aggregated Dashboard Statistics",
    description="Returns high-level security metrics calculated from SQLite: total requests, anomaly count, error rate, and threat tiers.",
)
def get_statistics(db: Session = Depends(get_db)):
    """
    Computes real-time aggregated metrics directly from SQLite database:
    - Total processed requests
    - Normal vs. anomalous request counts and percentage
    - Average latency in milliseconds
    - HTTP error counts (status codes >= 400)
    - Threat tier breakdown and top anomalous endpoints
    """
    stats = database_service.calculate_statistics(db)
    if stats.total_processed_requests > 0:
        return stats

    # Fallback to in-memory stats if database is empty
    return traffic_service.get_statistics()
