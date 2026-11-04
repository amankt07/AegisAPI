"""
AegisAPI - Intelligent API Traffic Anomaly Detection & Threat Monitoring Platform
FastAPI Application Entrypoint
Integrates ML inference, traffic event store, health monitoring, and analytics.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes import (
    health_router,
    model_info_router,
    prediction_router,
    statistics_router,
    traffic_router,
)
from app.services.model_service import model_service

app = FastAPI(
    title="AegisAPI",
    description=(
        "**AegisAPI – Intelligent API Traffic Anomaly Detection & Threat Monitoring Platform**\n\n"
        "Machine Learning-powered API telemetry security service. "
        "Utilizes an unsupervised Isolation Forest model to intercept volumetric bursts, "
        "brute-force attacks, 5xx server crash cascades, abnormal execution delays, "
        "and data exfiltration dumps in real time."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Cross-Origin Resource Sharing (CORS) Configuration
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits frontend development across Vite ports (e.g., http://localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router Registration
# ---------------------------------------------------------------------------
app.include_router(health_router)
app.include_router(prediction_router)
app.include_router(traffic_router)
app.include_router(statistics_router)
app.include_router(model_info_router)


# ---------------------------------------------------------------------------
# Root Discovery Endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["Root"])
async def root():
    """Service discovery route providing quick links to documentation and status."""
    return {
        "service": "AegisAPI Telemetry & Anomaly Detection Backend",
        "version": "0.1.0",
        "status": "online",
        "documentation": "/docs",
        "redoc": "/redoc",
        "health_check": "/health",
        "model_loaded": model_service.is_loaded,
        "active_model": (
            model_service.metadata.get("model_name", "Isolation Forest")
            if model_service.is_loaded and model_service.metadata
            else None
        ),
    }


# ---------------------------------------------------------------------------
# Global Exception Handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors cleanly without exposing internals."""
    errors = []
    for error in exc.errors():
        field = " -> ".join([str(loc) for loc in error.get("loc", [])])
        msg = error.get("msg", "Invalid value")
        errors.append({"field": field, "error": msg})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Request validation failed. Ensure required fields meet type and range constraints.",
            "details": errors,
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handles domain validation exceptions as 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": "error", "message": str(exc)},
    )
