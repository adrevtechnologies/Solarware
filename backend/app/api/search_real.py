"""
REAL Search Engine - No fake data, no placeholders
Uses live APIs: Nominatim + Overpass + Solar calculations
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
import asyncio
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.nominatim_service import (
    geocode_address,
    reverse_geocode,
    get_bounding_box,
)
from ..services.overpass_service import (
    query_commercial_buildings,
    filter_nearby_buildings,
)
from ..services.solar_calculations import get_solar_stats
from ..services.satellite_service import get_satellite_image_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


class SearchRequest(BaseModel):
    """Real search request - no fake modes"""
    mode: str  # address | area | city | province | country
    
    # Address mode
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    suburb: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postcode: Optional[str] = None
    radius_m: int = 500  # 250, 500, 1000
    
    # Building type filters
    building_types: Optional[List[str]] = None  # warehouse, retail, office, school, etc
    
    # Roof filters
    min_roof_sqm: Optional[int] = 150


class SolarProspect(BaseModel):
    """Real prospect from OSM - NO fake data"""
    osm_id: str
    address: str
    suburb: Optional[str]
    city: Optional[str]
    business_name: Optional[str]
    building_type: str
    roof_area_sqm: float
    capacity_low_kw: float
    capacity_high_kw: float
    annual_kwh: float
    savings_low: float
    savings_high: float
    savings_potential_display: str  # "R xxx k – R xxx k / year"
    solar_score: int
    satellite_image_url: str
    latitude: float
    longitude: float


class SearchResponse(BaseModel):
    results: List[SolarProspect]
    count: int
    search_area: str
    message: str


@router.post("/search")
async def search_real_prospects(
    request: SearchRequest,
    db: Session = Depends(get_db)
) -> SearchResponse:
    """
    REAL SEARCH ENGINE
    
    Priority: Address > Area > City > Province > Country
    
    1. Geocode location using Nominatim
    2. Query Overpass API for commercial buildings only
    3. Calculate solar stats for each building
    4. Return REAL prospects with real addresses
    
    NO placeholder data. NO fake results.
    If no buildings found, say so.
    """
    
    try:
        # STEP 1: GEOCODE INPUT
        logger.info(f"Search request: mode={request.mode}")
        
        if request.mode == "address" and request.street_name:
            # Geocode specific address
            query_str = f"{request.street_number or ''} {request.street_name}".strip()
            geo = geocode_address(
                query_str,
                city=request.city or "",
                province=request.province or ""
            )
            if not geo:
                return SearchResponse(
                    results=[],
                    count=0,
                    search_area=query_str,
                    message="Address not found. Try another address or a broader search."
                )
            
            center_lat, center_lon = geo.latitude, geo.longitude
            radius_km = request.radius_m / 1000.0
            search_area = geo.address
            
        elif request.mode == "area" and request.suburb:
            # Geocode suburb/area
            geo = geocode_address(
                request.suburb,
                city=request.city or "",
                province=request.province or ""
            )
            if not geo:
                return SearchResponse(
                    results=[],
                    count=0,
                    search_area=request.suburb,
                    message="Area not found. Check spelling and try again."
                )
            
            center_lat, center_lon = geo.latitude, geo.longitude
            radius_km = request.radius_m / 1000.0
            search_area = geo.address
            
        elif request.mode == "city" and request.city:
            # Geocode city
            geo = geocode_address(
                request.city,
                province=request.province or ""
            )
            if not geo:
                return SearchResponse(
                    results=[],
                    count=0,
                    search_area=request.city,
                    message="City not found."
                )
            
            center_lat, center_lon = geo.latitude, geo.longitude
            radius_km = 5.0  # Larger search for city
            search_area = f"{request.city}, {request.province or 'South Africa'}"
            
        elif request.mode == "province" and request.province:
            # Geocode province (search all)
            geo = geocode_address(request.province, "", "")
            if not geo:
                return SearchResponse(
                    results=[],
                    count=0,
                    search_area=request.province,
                    message="Province not found."
                )
            
            center_lat, center_lon = geo.latitude, geo.longitude
            radius_km = 20.0  # Huge search for province
            search_area = request.province
            
        else:
            return SearchResponse(
                results=[],
                count=0,
                search_area="",
                message="Invalid search parameters. Provide address, area, city, or province."
            )

        # STEP 2: QUERY OVERPASS FOR REAL BUILDINGS
        logger.info(f"Querying Overpass API for commercial buildings near {search_area}")
        
        min_lat, max_lat, min_lon, max_lon = get_bounding_box(center_lat, center_lon, radius_km)
        
        buildings = query_commercial_buildings(min_lat, max_lat, min_lon, max_lon)
        
        if not buildings:
            return SearchResponse(
                results=[],
                count=0,
                search_area=search_area,
                message="No suitable commercial prospects found in this area. Try increasing radius or changing location."
            )

        # Filter by radius and building type
        buildings = filter_nearby_buildings(buildings, center_lat, center_lon, radius_km)
        
        if request.building_types:
            buildings = [b for b in buildings if b.building_type in request.building_types]

        if request.min_roof_sqm:
            buildings = [b for b in buildings if b.roof_area_sqm >= request.min_roof_sqm]

        if not buildings:
            return SearchResponse(
                results=[],
                count=0,
                search_area=search_area,
                message="No buildings match your filters."
            )

        # STEP 3: CALCULATE SOLAR STATS FOR EACH BUILDING
        logger.info(f"Calculating solar stats for {len(buildings)} buildings")
        
        results = []
        for building in buildings[:500]:  # Limit to 500 results
            try:
                # Get solar calculations
                solar = get_solar_stats(
                    building.roof_area_sqm,
                    building.building_type,
                    province=request.province
                )

                # Get satellite image
                image_url = get_satellite_image_url(
                    building.latitude,
                    building.longitude
                )

                # Reverse geocode for full address
                geo_result = reverse_geocode(building.latitude, building.longitude)
                address = geo_result.get("address") if geo_result else f"{building.latitude}, {building.longitude}"

                # Format savings display
                savings_low = int(solar["savings_low"])
                savings_high = int(solar["savings_high"])
                savings_display = f"R {savings_low/1000:.0f}k – R {savings_high/1000:.0f}k / year"

                prospect = SolarProspect(
                    osm_id=building.osm_id,
                    address=address,
                    suburb=geo_result.get("suburb") if geo_result else None,
                    city=geo_result.get("city") if geo_result else None,
                    business_name=building.name,
                    building_type=building.building_type,
                    roof_area_sqm=solar["roof_area_sqm"],
                    capacity_low_kw=solar["capacity_low_kw"],
                    capacity_high_kw=solar["capacity_high_kw"],
                    annual_kwh=solar["annual_kwh_mid"],
                    savings_low=solar["savings_low"],
                    savings_high=solar["savings_high"],
                    savings_potential_display=savings_display,
                    solar_score=solar["solar_score"],
                    satellite_image_url=image_url,
                    latitude=building.latitude,
                    longitude=building.longitude,
                )
                
                results.append(prospect)

            except Exception as e:
                logger.error(f"Error processing building {building.osm_id}: {e}")
                continue

        logger.info(f"Search completed: {len(results)} prospects found in {search_area}")
        
        return SearchResponse(
            results=results,
            count=len(results),
            search_area=search_area,
            message=f"Found {len(results)} commercial buildings with solar potential in {search_area}"
        )

    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
