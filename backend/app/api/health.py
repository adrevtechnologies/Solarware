"""Health check endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from app.core import get_settings
from app.core.database import get_engine

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Redirect root requests to the bundled UI."""
    return RedirectResponse(url="/app/")


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
