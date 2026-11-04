"""
AegisAPI - Traffic & Anomaly Telemetry Event Log Endpoints
Reads persisted traffic records and anomaly predictions from SQLite.
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AnomalyEvent, TrafficEvent
from app.services.database_service import database_service
from app.services.traffic_service import traffic_service

router = APIRouter(tags=["Telemetry & Anomaly Logs"])


@router.get(
    "/traffic",
    response_model=List[TrafficEvent],
    summary="Get Recent Traffic Events",
    description="Retrieves chronological recent API traffic events from SQLite database with pagination.",
)
def get_traffic(
    limit: int = Query(default=50, ge=1, le=500, description="Number of records to retrieve"),
    offset: int = Query(default=0, ge=0, description="Offset pagination index"),
    db: Session = Depends(get_db),
):
    """Retrieve recent API traffic logs from SQLite (newest first)."""
    db_records = database_service.get_recent_traffic(db, limit=limit, offset=offset)
    if db_records:
        return [TrafficEvent.model_validate(rec) for rec in db_records]

    # Fallback to in-memory buffer if database is empty
    return traffic_service.get_recent_traffic(limit=limit, offset=offset)


@router.get(
    "/anomalies",
    response_model=List[AnomalyEvent],
    summary="Get Detected Anomaly Incidents",
    description="Retrieves security incidents and anomalous predictions from SQLite database.",
)
def get_anomalies(
    limit: int = Query(default=50, ge=1, le=500, description="Number of anomaly incidents to retrieve"),
    offset: int = Query(default=0, ge=0, description="Offset pagination index"),
    db: Session = Depends(get_db),
):
    """Retrieve detected anomalies flagged by the model from SQLite (newest first)."""
    db_anomalies = database_service.get_recent_anomalies(db, limit=limit, offset=offset)
    if db_anomalies:
        return [AnomalyEvent.model_validate(anom) for anom in db_anomalies]

    # Fallback to in-memory buffer if database is empty
    return traffic_service.get_recent_anomalies(limit=limit, offset=offset)
