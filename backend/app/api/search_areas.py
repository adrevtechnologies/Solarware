"""API routes for search areas."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
import uuid
from sqlalchemy.orm import Session

from ..core import get_db
from ..models import SearchArea
from ..schemas import SearchAreaCreate, SearchAreaResponse
from ..utils import validate_search_bounds
from ..utils.address_geocoder import AddressGeocoder
from ..core.errors import ValidationError

router = APIRouter(prefix="/api/search-areas", tags=["search-areas"])


@router.post("", response_model=SearchAreaResponse)
def create_search_area(
    area: SearchAreaCreate,
    db: Session = Depends(get_db)
):
    """Create a new search area (address-based or coordinate-based)."""
    
    # Handle address-based search
    if any([area.street, area.area, area.district, area.city]):
        geocoded = AddressGeocoder.geocode_address(
            street=area.street,
            area=area.area,
            district=area.district,
            city=area.city,
            region=area.region,
            country=area.country,
        )
        
        bounds = geocoded.get("bounds", {})
        min_latitude = bounds.get("min_latitude", 40.7)
        max_latitude = bounds.get("max_latitude", 40.8)
        min_longitude = bounds.get("min_longitude", -74.0)
        max_longitude = bounds.get("max_longitude", -73.9)
        
        # Use geocoded address as area name
        area_name = area.name or geocoded.get("full_address", "Search Area")
        
    # Handle coordinate-based search (legacy)
    elif all([area.min_latitude, area.max_latitude, area.min_longitude, area.max_longitude]):
        min_latitude = area.min_latitude
        max_latitude = area.max_latitude
        min_longitude = area.min_longitude
        max_longitude = area.max_longitude
        area_name = area.name or "Coordinate-based Search"
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either address fields (street/area/city) or geographic coordinates (latitude/longitude)"
        )
    
    # Validate bounds
    try:
        validate_search_bounds(min_latitude, max_latitude, min_longitude, max_longitude)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create search area
    db_area = SearchArea(
        name=area_name,
        country=area.country,
        region=area.region,
        min_latitude=min_latitude,
        max_latitude=max_latitude,
        min_longitude=min_longitude,
        max_longitude=max_longitude,
        min_roof_area_sqft=area.min_roof_area_sqft,
    )
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    
    return db_area


@router.get("", response_model=List[SearchAreaResponse])
def list_search_areas(
    country: str = Query(None),
    db: Session = Depends(get_db)
):
    """List search areas with optional filtering."""
    query = db.query(SearchArea)
    
    if country:
        query = query.filter(SearchArea.country == country.upper())
    
    return query.all()


@router.get("/{area_id}", response_model=SearchAreaResponse)
def get_search_area(
    area_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific search area."""
    try:
        area_uuid = uuid.UUID(area_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid area ID format")
    
    area = db.query(SearchArea).filter(SearchArea.id == area_uuid).first()
    
    if not area:
        raise HTTPException(status_code=404, detail="Search area not found")
    
    return area


@router.put("/{area_id}", response_model=SearchAreaResponse)
def update_search_area(
    area_id: str,
    area_update: SearchAreaCreate,
    db: Session = Depends(get_db)
):
    """Update a search area."""
    try:
        area_uuid = uuid.UUID(area_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid area ID format")
    
    area = db.query(SearchArea).filter(SearchArea.id == area_uuid).first()
    
    if not area:
        raise HTTPException(status_code=404, detail="Search area not found")
    
    try:
        validate_search_bounds(
            area_update.min_latitude,
            area_update.max_latitude,
            area_update.min_longitude,
            area_update.max_longitude,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    for key, value in area_update.model_dump().items():
        setattr(area, key, value)
    
    db.commit()
    db.refresh(area)
    
    return area
