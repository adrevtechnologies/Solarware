"""API initialization."""
from .health import router as health_router
from .search_areas import router as search_areas_router
from .prospects import router as prospects_router
from .processing import router as processing_router
from .search import router as search_router

__all__ = [
    "health_router",
    "search_areas_router", 
    "prospects_router",
    "processing_router",
    "search_router",
]
