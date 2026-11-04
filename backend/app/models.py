"""
AegisAPI - SQLAlchemy ORM Database Models
Defines schema definitions for traffic events, anomaly predictions, and model audit records.
"""
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class TrafficEvent(Base):
    """
    Represents an ingested API traffic record.
    Stores telemetry dimensions including latency, payload sizes, velocity, and status codes.
    """
    __tablename__ = "traffic_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    source_ip = Column(String(45), index=True, nullable=False, default="127.0.0.1")
    endpoint = Column(String(255), index=True, nullable=False)
    http_method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Float, nullable=False)
    request_size_bytes = Column(Integer, default=0, nullable=False)
    response_size_bytes = Column(Integer, default=0, nullable=False)
    requests_per_minute = Column(Integer, default=1, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)
    user_agent = Column(String(500), nullable=True)

    # 1-to-1 relationship with AnomalyPrediction
    prediction = relationship(
        "AnomalyPrediction",
        back_populates="traffic_event",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Virtual properties for seamless Pydantic serialization
    @property
    def is_anomaly(self) -> int:
        return 1 if (self.prediction and self.prediction.is_anomaly) else 0

    @property
    def prediction_label(self) -> str:
        return self.prediction.prediction_label if self.prediction else "Normal"

    @property
    def anomaly_score(self) -> float:
        return self.prediction.anomaly_score if self.prediction else 0.0

    @property
    def threat_level(self) -> str:
        if not self.prediction:
            return "Safe"
        score = self.prediction.anomaly_score
        if score < 0.0:
            return "Safe"
        elif score < 0.07:
            return "Low Threat"
        elif score < 0.15:
            return "Medium Threat"
        elif score < 0.25:
            return "High Threat"
        else:
            return "Critical Threat"


class AnomalyPrediction(Base):
    """
    Represents an ML model anomaly classification result linked to a TrafficEvent.
    """
    __tablename__ = "anomaly_predictions"

    id = Column(Integer, primary_key=True, index=True)
    traffic_event_id = Column(
        Integer,
        ForeignKey("traffic_events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    is_anomaly = Column(Boolean, nullable=False, index=True, default=False)
    prediction_label = Column(String(50), nullable=False)
    anomaly_score = Column(Float, nullable=False)
    model_name = Column(String(100), nullable=False, default="Isolation Forest")

    # Relationship back to TrafficEvent
    traffic_event = relationship("TrafficEvent", back_populates="prediction")

    # Virtual properties delegating to TrafficEvent for AnomalyEvent schema serialization
    @property
    def source_ip(self) -> str:
        return self.traffic_event.source_ip if self.traffic_event else "127.0.0.1"

    @property
    def endpoint(self) -> str:
        return self.traffic_event.endpoint if self.traffic_event else ""

    @property
    def http_method(self) -> str:
        return self.traffic_event.http_method if self.traffic_event else ""

    @property
    def status_code(self) -> int:
        return self.traffic_event.status_code if self.traffic_event else 200

    @property
    def response_time_ms(self) -> float:
        return self.traffic_event.response_time_ms if self.traffic_event else 0.0

    @property
    def request_size_bytes(self) -> int:
        return self.traffic_event.request_size_bytes if self.traffic_event else 0

    @property
    def response_size_bytes(self) -> int:
        return self.traffic_event.response_size_bytes if self.traffic_event else 0

    @property
    def requests_per_minute(self) -> int:
        return self.traffic_event.requests_per_minute if self.traffic_event else 0

    @property
    def failed_requests(self) -> int:
        return self.traffic_event.failed_requests if self.traffic_event else 0

    @property
    def threat_level(self) -> str:
        score = self.anomaly_score
        if score < 0.0:
            return "Safe"
        elif score < 0.07:
            return "Low Threat"
        elif score < 0.15:
            return "Medium Threat"
        elif score < 0.25:
            return "High Threat"
        else:
            return "Critical Threat"


class ModelInformation(Base):
    """
    Stores metadata, hyperparameters, and evaluation metrics for active and historical ML models.
    """
    __tablename__ = "model_information"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    algorithm = Column(String(255), nullable=False)
    training_date = Column(String(100), nullable=True)
    training_records = Column(Integer, nullable=True)
    feature_count = Column(Integer, nullable=True)
    evaluation_metrics = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
