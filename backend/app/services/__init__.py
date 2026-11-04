"""
AegisAPI Application Services
Houses ML model inference and traffic store services.
"""
from app.services.model_service import ModelService, model_service
from app.services.traffic_service import TrafficService, traffic_service

__all__ = ["ModelService", "model_service", "TrafficService", "traffic_service"]
