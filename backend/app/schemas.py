"""
AegisAPI - Pydantic Request & Response Validation Schemas
Defines structured data contracts for telemetry ingestion, ML prediction,
analytics, and health observability.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TrafficRecordInput(BaseModel):
    """
    Schema representing an incoming API traffic telemetry record for inspection.
    """
    endpoint: str = Field(..., description="API route path, e.g. /api/v1/products", min_length=1)
    http_method: str = Field(..., description="HTTP Method: GET, POST, PUT, DELETE")
    status_code: int = Field(..., ge=100, le=599, description="HTTP response status code")
    response_time_ms: float = Field(..., ge=0.0, description="Latency in milliseconds")
    request_size_bytes: int = Field(default=0, ge=0, description="Inbound request payload size in bytes")
    response_size_bytes: int = Field(default=0, ge=0, description="Outbound response payload size in bytes")
    requests_per_minute: int = Field(default=1, ge=0, description="Rolling request frequency from source IP")
    failed_requests: int = Field(default=0, ge=0, description="Failed request count in evaluation window")
    user_agent: Optional[str] = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        description="Client user agent string",
    )
    source_ip: Optional[str] = Field(
        default="127.0.0.1",
        description="Synthetic client IP address (used for logging and telemetry, not model training)",
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Event timestamp. If omitted, current server UTC time is applied.",
    )

    @field_validator("http_method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        normalized = v.strip().upper()
        if normalized not in valid_methods:
            raise ValueError(f"Invalid HTTP method '{v}'. Must be one of: {sorted(valid_methods)}")
        return normalized

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint": "/api/v1/products",
                "http_method": "GET",
                "status_code": 200,
                "response_time_ms": 68.42,
                "request_size_bytes": 180,
                "response_size_bytes": 3400,
                "requests_per_minute": 14,
                "failed_requests": 0,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "source_ip": "192.168.1.45",
            }
        }
    )


class BatchTrafficInput(BaseModel):
    """Schema for submitting multiple traffic records in a single payload."""
    records: List[TrafficRecordInput] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="List of traffic records (Maximum 500 records per batch)",
    )


class PredictionResponse(BaseModel):
    """Schema returned after real-time anomaly detection inference."""
    is_anomaly: int = Field(..., description="0 for normal traffic, 1 for detected anomaly")
    prediction_label: str = Field(..., description="'Normal' or 'Anomaly'")
    anomaly_score: float = Field(
        ...,
        description="Continuous anomaly score. Positive values indicate anomalous deviation; higher values represent severe outliers.",
    )
    threat_level: str = Field(
        ...,
        description="Categorized threat tier: Safe, Low Threat, Medium Threat, High Threat, or Critical Threat",
    )
    model_name: str = Field(..., description="Name of the champion model generating the decision")
    timestamp: datetime = Field(..., description="Inference timestamp")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Supplemental scoring context (offset, features evaluated, endpoint)",
    )


class BatchPredictionResponse(BaseModel):
    """Aggregated response for batch anomaly inference."""
    total_records: int
    anomalies_detected: int
    anomaly_rate_percent: float
    model_name: str
    predictions: List[PredictionResponse]


class TrafficEvent(BaseModel):
    """Schema representing a stored historical traffic event."""
    id: int
    timestamp: datetime
    source_ip: str
    endpoint: str
    http_method: str
    status_code: int
    response_time_ms: float
    request_size_bytes: int
    response_size_bytes: int
    requests_per_minute: int
    failed_requests: int
    user_agent: str
    is_anomaly: int
    prediction_label: str
    anomaly_score: float
    threat_level: str


class AnomalyEvent(BaseModel):
    """Schema representing an incident-flagged anomalous event."""
    id: int
    timestamp: datetime
    source_ip: str
    endpoint: str
    http_method: str
    status_code: int
    response_time_ms: float
    request_size_bytes: int
    response_size_bytes: int
    requests_per_minute: int
    failed_requests: int
    anomaly_score: float
    threat_level: str


class DashboardStatistics(BaseModel):
    """Real-time aggregated KPIs for dashboard telemetry."""
    total_processed_requests: int
    normal_requests: int
    anomalous_requests: int
    anomaly_percentage: float
    average_response_time_ms: float
    http_error_count: int
    threat_level_distribution: Dict[str, int]
    top_anomalous_endpoints: Dict[str, int]


class ModelInfoResponse(BaseModel):
    """Detailed metadata concerning the active production model artifact."""
    model_name: str
    algorithm: str
    training_date: str
    feature_count: int
    train_test_split: str
    status: str
    hyperparameters: Dict[str, Any]
    evaluation_metrics: Dict[str, Any]
    score_interpretation: str
    feature_names: List[str]


class HealthResponse(BaseModel):
    """Backend service health check response."""
    status: str
    service: str
    version: str
    model_loaded: bool
    model_name: Optional[str] = None
    feature_count: Optional[int] = None
