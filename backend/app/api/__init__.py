"""API initialization."""
from .health import router as health_router
from .search_real import router as search_real_router

__all__ = [
    "health_router",
    "search_real_router",
]
