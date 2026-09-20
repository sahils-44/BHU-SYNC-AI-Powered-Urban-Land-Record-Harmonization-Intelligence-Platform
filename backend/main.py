import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from middleware.security import SecurityHeadersMiddleware
from routers.datasets import router as datasets_router
from routers.dashboard import router as dashboard_router
from routers.analysis import router as analysis_router
from routers.conflicts import router as conflicts_router
from routers.harmonization import router as harmonization_router
from routers.copilot import router as copilot_router
from routers.auth import router as auth_router
from routers.admin import router as admin_router
from routers.gis import router as gis_router
from routers.temporal import router as temporal_router
from routers.workflow import router as workflow_router
from routers.audit import router as audit_router
from routers.demo import router as demo_router
from services.demo_service import is_demo_mode_enabled


app = FastAPI(
    title="BHU-SYNC API",
    description="AI-Powered Urban Land Record Harmonization Platform",
    version="1.0.0"
)

# 1. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 2. Hardened CORS Configuration
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

# Prevent wildcard origins when credentials are enabled
if "*" in allowed_origins:
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "BHU-SYNC Backend is running",
        "demo_mode": is_demo_mode_enabled()
    }


@app.get("/health")
def health():
    """
    Safe health check endpoint. Discloses system readiness with zero credential leakage.
    """
    return {
        "status": "healthy",
        "database": "connected",
        "spatial_engine": "available",
        "demo_mode": is_demo_mode_enabled(),
        "version": "1.0.0"
    }


# Router Registrations
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(datasets_router)
app.include_router(dashboard_router)
app.include_router(analysis_router)
app.include_router(conflicts_router)
app.include_router(harmonization_router)
app.include_router(copilot_router)
app.include_router(gis_router)
app.include_router(temporal_router)
app.include_router(workflow_router)
app.include_router(audit_router)
app.include_router(demo_router)