"""
AegisAPI - Traffic & Anomaly Telemetry Event Log Endpoints
"""
from typing import List
from fastapi import APIRouter, Query
from app.schemas import AnomalyEvent, TrafficEvent
from app.services.traffic_service import traffic_service

router = APIRouter(tags=["Telemetry & Anomaly Logs"])


@router.get(
    "/traffic",
    response_model=List[TrafficEvent],
    summary="Get Recent Traffic Events",
    description="Retrieves chronological recent API traffic events with model anomaly classifications.",
)
async def get_traffic(
    limit: int = Query(default=50, ge=1, le=500, description="Number of records to retrieve"),
    offset: int = Query(default=0, ge=0, description="Offset pagination index"),
):
    """Retrieve recent API traffic logs (newest first)."""
    return traffic_service.get_recent_traffic(limit=limit, offset=offset)


@router.get(
    "/anomalies",
    response_model=List[AnomalyEvent],
    summary="Get Detected Anomaly Incidents",
    description="Retrieves security incidents and flagged anomalous traffic events.",
)
async def get_anomalies(
    limit: int = Query(default=50, ge=1, le=500, description="Number of anomaly incidents to retrieve"),
    offset: int = Query(default=0, ge=0, description="Offset pagination index"),
):
    """Retrieve detected anomalies flagged by the model (newest first)."""
    return traffic_service.get_recent_anomalies(limit=limit, offset=offset)

