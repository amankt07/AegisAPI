"""
SQLAlchemy ORM models for AegisAPI.
Defines database schemas for API traffic records, anomaly incidents, and threat metrics.
"""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func
from app.database import Base


class TrafficLog(Base):
    """
    Represents an ingested API traffic event with metadata for anomaly inspection.
    """
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ip_address = Column(String(45), index=True, nullable=False)
    endpoint = Column(String(255), index=True, nullable=False)
    http_method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    request_size_bytes = Column(Integer, default=0)
    response_size_bytes = Column(Integer, default=0)
    user_agent = Column(String(255), nullable=True)

    # Anomaly detection results
    is_anomaly = Column(Boolean, default=False, index=True)
    anomaly_score = Column(Float, nullable=True)
    threat_category = Column(String(50), nullable=True)  # e.g., RateSpike, DataExfiltration, UnusualEndpoint

