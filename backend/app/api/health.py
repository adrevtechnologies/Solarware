"""Health check endpoints."""
from fastapi import APIRouter
from app.core import get_settings
from app.core.database import get_engine

router = APIRouter(tags=["health"])


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
            conn.execute("SELECT 1")
        
        return {
            "status": "ready",
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "database": "error",
            "error": str(e),
        }, 503
