"""API routes for processing and discovery."""
from fastapi import APIRouter, HTTPException
import uuid
from ..services.prospect_discovery import ProspectDiscoveryService, get_processing_status as get_status_snapshot
from ..core.logging import logger

router = APIRouter(prefix="/api/process", tags=["processing"])


@router.post("/search-area/{search_area_id}")
async def process_search_area(
    search_area_id: str,
    generate_visualizations: bool = True,
    enrich_contacts: bool = True,
    generate_packs: bool = True,
):
    """Process a search area to discover prospects.
    
    This endpoint triggers background processing for:
    - Satellite image retrieval
    - Building detection
    - Contact enrichment
    - Solar analysis
    - Visualization generation
    - Mailing pack generation
    """
    try:
        # Validate UUID
        uuid.UUID(search_area_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid search area ID format")
    
    try:
        service = ProspectDiscoveryService()
        await service.process_search_area(
            search_area_id,
            generate_visualizations,
            enrich_contacts,
            generate_packs,
        )
        logger.info(f"Processing completed for search area: {search_area_id}")
        return get_status_snapshot(search_area_id)
    except Exception as e:
        logger.error(f"Processing start failed for {search_area_id}: {str(e)}", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/status/{search_area_id}")
async def get_processing_status(search_area_id: str):
    """Get processing status for a search area."""
    try:
        uuid.UUID(search_area_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid search area ID format")
    
    return get_status_snapshot(search_area_id)
