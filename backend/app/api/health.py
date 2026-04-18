"""Health check endpoints."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from ..core import get_settings
from ..core.database import get_engine

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Simple root endpoint for uptime checks and browser opens."""
    return {
        "service": "Solarware API",
        "status": "ok",
        "health": "/health",
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "environment": get_settings().ENVIRONMENT,
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check - includes database."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "ready",
            "database": "connected",
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "error",
                "error": str(e),
            },
        )
