"""
AegisAPI Route Modules
Exports modular FastAPI sub-routers.
"""
from app.routes.health import router as health_router
from app.routes.prediction import router as prediction_router
from app.routes.traffic import router as traffic_router
from app.routes.statistics import router as statistics_router
from app.routes.model_info import router as model_info_router

__all__ = [
    "health_router",
    "prediction_router",
    "traffic_router",
    "statistics_router",
    "model_info_router",
]
