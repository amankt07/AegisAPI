"""
AegisAPI - Intelligent API Traffic Anomaly Detection & Threat Monitoring Platform
FastAPI Application Entrypoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AegisAPI",
    description="Intelligent API Traffic Anomaly Detection & Threat Monitoring Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Cross-Origin Resource Sharing (CORS) for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify backend service status.
    """
    return {
        "status": "healthy",
        "service": "AegisAPI Backend",
        "version": "0.1.0",
    }

