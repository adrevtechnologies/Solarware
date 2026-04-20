"""API endpoints for PHASE 4 area mass search."""
from fastapi import APIRouter, HTTPException

from ..schemas.area_mass_search import AreaMassSearchRequest, AreaMassSearchResponse
from ..services.area_mass_search import AreaMassSearchService

router = APIRouter(prefix="/api/area-mass-search", tags=["area-mass-search"])


@router.post("", response_model=AreaMassSearchResponse)
def area_mass_search(request: AreaMassSearchRequest):
    service = AreaMassSearchService()
    try:
        ranked, total, export_url = service.search_area(request)
        start = (request.page - 1) * request.page_size
        end = start + request.page_size
        paged = ranked[start:end]
        return AreaMassSearchResponse(
            results=paged,
            count=len(paged),
            total=total,
            page=request.page,
            page_size=request.page_size,
            export_csv_url=export_url,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Area mass search failed: {e}")
