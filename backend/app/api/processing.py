"""API routes for processing and discovery."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
import uuid
from app.services.prospect_discovery import ProspectDiscoveryService, get_processing_status as get_status_snapshot
from app.core.logging import logger

router = APIRouter(prefix="/api/process", tags=["processing"])


@router.post("/search-area/{search_area_id}")
async def process_search_area(
    search_area_id: str,
    background_tasks: BackgroundTasks,
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
    
    # Start processing in background
    service = ProspectDiscoveryService()
    ProspectDiscoveryService._set_status(
        search_area_id,
        search_area_id=search_area_id,
        status="queued",
        message="Processing has been queued",
    )
    background_tasks.add_task(
        service.process_search_area,
        search_area_id,
        generate_visualizations,
        enrich_contacts,
        generate_packs,
    )
    
    logger.info(f"Processing started for search area: {search_area_id}")
    
    return {
        "status": "processing_started",
        "search_area_id": search_area_id,
        "message": "Processing has been queued. Check status for updates."
    }


@router.get("/status/{search_area_id}")
async def get_processing_status(search_area_id: str):
    """Get processing status for a search area."""
    try:
        uuid.UUID(search_area_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid search area ID format")
    
    return get_status_snapshot(search_area_id)
