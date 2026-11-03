"""
Pydantic schemas for data validation, API request/response serialization,
and ML inference payloads.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TrafficLogCreate(BaseModel):
    """Schema for incoming API traffic logs to be analyzed and recorded."""
    ip_address: str = Field(..., description="Client IP address")
    endpoint: str = Field(..., description="Target API route / path")
    http_method: str = Field(..., description="HTTP Method (GET, POST, etc.)")
    status_code: int = Field(..., description="HTTP response status code")
    response_time_ms: float = Field(..., description="Latency in milliseconds")
    request_size_bytes: int = Field(default=0, description="Size of incoming payload in bytes")
    response_size_bytes: int = Field(default=0, description="Size of outgoing payload in bytes")
    user_agent: Optional[str] = Field(default=None, description="Client user-agent string")


class TrafficLogResponse(TrafficLogCreate):
    """Schema for returning recorded traffic log with anomaly classification."""
    id: int
    timestamp: datetime
    is_anomaly: bool
    anomaly_score: Optional[float] = None
    threat_category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AnomalyPredictionRequest(BaseModel):
    """Schema for submitting feature vector directly for real-time anomaly inference."""
    response_time_ms: float
    request_size_bytes: int
    response_size_bytes: int
    status_code: int
    request_rate_1m: Optional[float] = 0.0


class AnomalyPredictionResponse(BaseModel):
    """Schema for ML anomaly detection response."""
    is_anomaly: bool
    anomaly_score: float
    threat_level: str  # Low, Medium, High, Critical

