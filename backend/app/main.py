"""Main FastAPI application."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core import get_settings, setup_database, logger
from app.core.errors import SolarwareError
from app.models import SearchArea, Prospect  # Import models to register with Base
from app.api import search_areas, prospects, processing, health
from app.api.search_real import router as search_real_router

# Setup database
try:
    setup_database()
except Exception as e:
    logger.error(f"Database setup failed: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan hooks."""
    logger.info(f"Solarware API starting - Environment: {settings.ENVIRONMENT}")
    yield
    logger.info("Solarware API shutting down")

# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
)

# Configure CORS
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
allow_all_origins = "*" in cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else cors_origins,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated proposal assets.
output_dir = Path(settings.OUTPUT_BASE_PATH).resolve()
output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(output_dir)), name="output")


# Exception handlers
@app.exception_handler(SolarwareError)
async def solarware_exception_handler(request: Request, exc: SolarwareError):
    """Handle Solarware exceptions."""
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(health.router)
app.include_router(search_areas.router)
app.include_router(prospects.router)
app.include_router(processing.router)
app.include_router(search_real_router)
