"""API initialization."""

from .health import router as health_router
from .search_real import router as search_real_router
from .area_mass_search import router as area_mass_search_router

__all__ = [
    "health_router",
    "search_real_router",
    "area_mass_search_router",
]
