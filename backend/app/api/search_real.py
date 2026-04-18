"""
REAL Search Engine - No fake data, no placeholders
Uses live APIs: Nominatim + Overpass + Solar calculations
"""
import logging
import json
import hashlib
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
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
from ..analysis.visualization import VizGenerator
from ..analysis.mailing_pack import MailingPackGenerator
from ..services.email_service import EmailService
from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


class SearchRequest(BaseModel):
    """V1 search request: area search with optional exact street address."""
    
    # Address mode
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    suburb: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = "South Africa"
    postcode: Optional[str] = None
    radius_m: int = 500  # 250, 500, 1000
    
    # Building type filters
    building_types: Optional[List[str]] = None  # warehouse, retail, office, school, etc
    include_residential: bool = False
    exact_address: bool = False
    
    # Roof filters
    min_roof_sqm: Optional[int] = None


class SolarProspect(BaseModel):
    """Real prospect from OSM - NO fake data"""
    osm_id: str
    address: str
    suburb: Optional[str]
    city: Optional[str]
    business_name: Optional[str]
    building_type: str
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    roof_area_sqm: float
    estimated_panel_count: int
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


class MailPackRequest(BaseModel):
    prospect: SolarProspect


class MailPackResponse(BaseModel):
    id: str
    before_image_url: str
    after_image_url: str
    before_after_image_url: str
    pdf_url: str
    email_subject: str
    email_body: str
    outreach_email: str


class MailPackSendRequest(BaseModel):
    mailing_pack: dict
    recipient_email: str


def _to_public_output_url(file_path: str | None) -> str | None:
    if not file_path:
        return None

    normalized = file_path.replace("\\", "/")
    if normalized.startswith("output/"):
        return f"/{normalized}"

    output_root = Path(get_settings().OUTPUT_BASE_PATH).resolve().as_posix()
    if normalized.startswith(output_root):
        rel = normalized[len(output_root):].lstrip("/")
        return f"/output/{rel}"

    marker = "/output/"
    idx = normalized.find(marker)
    if idx >= 0:
        return normalized[idx:]
    return None


def _cache_file_for_request(request: SearchRequest) -> Path:
    cache_root = Path(get_settings().OUTPUT_BASE_PATH).resolve() / "cache"
    cache_root.mkdir(parents=True, exist_ok=True)

    key_data = {
        "country": request.country,
        "province": request.province,
        "city": request.city,
        "suburb": request.suburb,
        "street_number": request.street_number,
        "street_name": request.street_name,
        "exact_address": request.exact_address,
        "postcode": request.postcode,
        "min_roof_sqm": request.min_roof_sqm,
        "include_residential": request.include_residential,
    }
    key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode("utf-8")).hexdigest()[:20]
    return cache_root / f"search_{key}.json"


def _load_cached_results(request: SearchRequest) -> Optional[SearchResponse]:
    cache_file = _cache_file_for_request(request)
    if not cache_file.exists():
        return None
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
        return SearchResponse(**payload)
    except Exception:
        return None


def _save_cached_results(request: SearchRequest, response: SearchResponse) -> None:
    cache_file = _cache_file_for_request(request)
    cache_file.write_text(response.model_dump_json(indent=2), encoding="utf-8")


@router.post("/search")
async def search_real_prospects(
    request: SearchRequest,
) -> SearchResponse:
    """
    REAL SEARCH ENGINE
    
    V1 behavior:
    - If street address provided: exact address search only
    - If street address empty: area search within selected city/province/country
    
    1. Geocode location using Nominatim
    2. Query Overpass API for buildings (commercial by default)
    3. Calculate solar stats for each building
    4. Return REAL prospects with real addresses
    
    NO placeholder data. NO fake results.
    If no buildings found, say so.
    """
    
    try:
        # STEP 1: Validate required context fields for V1.
        if not request.country or not request.province or not request.city or not request.suburb:
            return SearchResponse(
                results=[],
                count=0,
                search_area="",
                message="Country, province/state, city, and area/suburb are required.",
            )

        is_exact_address = bool(
            request.exact_address and request.street_name and request.street_name.strip()
        )
        logger.info("Search request: exact_address=%s", is_exact_address)

        if is_exact_address:
            query_str = f"{request.street_number or ''} {request.street_name}".strip()
            geo = geocode_address(
                query_str,
                city=request.city,
                province=request.province,
                suburb=request.suburb,
                postcode=request.postcode or "",
                country=request.country,
            )
            if not geo:
                return SearchResponse(
                    results=[],
                    count=0,
                    search_area=query_str,
                    message="Address not found. Check street spelling and try again.",
                )

            center_lat, center_lon = geo.latitude, geo.longitude
            radius_km = max(0.15, request.radius_m / 1000.0)
            search_area = geo.address
        else:
            geo = geocode_address(
                request.suburb,
                city=request.city,
                province=request.province,
                postcode=request.postcode or "",
                country=request.country,
            )
            if not geo:
                return SearchResponse(
                    results=[],
                    count=0,
                    search_area=request.suburb,
                    message="Area not found. Check spelling and try again.",
                )

            center_lat, center_lon = geo.latitude, geo.longitude
            radius_km = max(0.5, request.radius_m / 1000.0)
            search_area = f"{request.suburb}, {request.city}, {request.province}"

        # STEP 2: QUERY OVERPASS FOR REAL BUILDINGS
        include_residential = bool(request.include_residential)

        logger.info(
            "Querying Overpass API for %s buildings near %s",
            "commercial + residential" if include_residential else "commercial",
            search_area,
        )
        
        min_lat, max_lat, min_lon, max_lon = get_bounding_box(center_lat, center_lon, radius_km)

        buildings = query_commercial_buildings(
            min_lat,
            max_lat,
            min_lon,
            max_lon,
            include_residential=include_residential,
        )

        # If exact-address search is too narrow, auto-fallback to area scope.
        if not buildings and is_exact_address:
            logger.info("Exact-address search returned no buildings, falling back to area scope")
            area_geo = geocode_address(
                request.suburb,
                city=request.city,
                province=request.province,
                postcode=request.postcode or "",
                country=request.country,
            )
            if area_geo:
                center_lat, center_lon = area_geo.latitude, area_geo.longitude
                search_area = f"{request.suburb}, {request.city}, {request.province}"
                radius_km = max(0.5, request.radius_m / 1000.0)
                min_lat, max_lat, min_lon, max_lon = get_bounding_box(center_lat, center_lon, radius_km)
                buildings = query_commercial_buildings(
                    min_lat,
                    max_lat,
                    min_lon,
                    max_lon,
                    include_residential=include_residential,
                )
        
        if not buildings:
            cached = _load_cached_results(request)
            if cached:
                return SearchResponse(
                    results=cached.results,
                    count=cached.count,
                    search_area=cached.search_area,
                    message=f"Live map source timed out. Showing last successful results for {cached.search_area}.",
                )

            return SearchResponse(
                results=[],
                count=0,
                search_area=search_area,
                message="No suitable properties found in this area. Try increasing radius or changing location."
            )

        # Filter by radius and building type
        buildings = filter_nearby_buildings(buildings, center_lat, center_lon, radius_km)
        
        if request.building_types:
            buildings = [b for b in buildings if b.building_type in request.building_types]

        effective_min_roof_sqm = (
            request.min_roof_sqm
            if request.min_roof_sqm is not None
            else (60 if include_residential else 150)
        )
        buildings = [b for b in buildings if b.roof_area_sqm >= effective_min_roof_sqm]

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
                    website=building.website,
                    phone=building.phone,
                    email=building.email,
                    contact_person=building.contact_person,
                    roof_area_sqm=solar["roof_area_sqm"],
                    estimated_panel_count=solar["estimated_panel_count"],
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
        
        response_message = f"Found {len(results)} properties with solar potential in {search_area}"
        if is_exact_address and request.street_name and search_area.startswith(f"{request.suburb},"):
            response_message = (
                f"No viable commercial roofs at exact address. Showing nearby area results for {search_area}."
            )

        response = SearchResponse(
            results=results,
            count=len(results),
            search_area=search_area,
            message=response_message,
        )
        _save_cached_results(request, response)
        return response

    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/search/mail-pack", response_model=MailPackResponse)
async def generate_mail_pack(request: MailPackRequest) -> MailPackResponse:
    """Generate heavy mail pack assets on demand for one selected result."""
    try:
        prospect = request.prospect

        mockup_path = await VizGenerator.generate_mockup(
            satellite_image_path=prospect.satellite_image_url,
            panel_count=prospect.estimated_panel_count,
            roof_area_sqm=prospect.roof_area_sqm,
            system_capacity_kw=prospect.capacity_high_kw,
        )

        before_after_path = await VizGenerator.generate_before_after(
            before_image_path=prospect.satellite_image_url,
            mockup_image_path=mockup_path,
        )

        pack = MailingPackGenerator.generate(
            prospect={
                "id": prospect.osm_id,
                "address": prospect.address,
                "business_name": prospect.business_name,
                "business_type": prospect.building_type,
                "website": prospect.website,
                "phone": prospect.phone,
                "email": prospect.email,
                "contact_name": prospect.contact_person,
                "roof_area_sqm": prospect.roof_area_sqm,
                "estimated_panel_count": prospect.estimated_panel_count,
                "estimated_system_capacity_kw": prospect.capacity_high_kw,
                "estimated_annual_production_kwh": prospect.annual_kwh,
                "savings_low": prospect.savings_low,
                "savings_high": prospect.savings_high,
                "solar_score": prospect.solar_score,
            },
            contact={
                "contact_name": prospect.contact_person,
                "email": prospect.email,
                "phone": prospect.phone,
            },
            satellite_image_path=prospect.satellite_image_url,
            mockup_image_path=mockup_path,
            before_after_image_path=before_after_path,
        )

        return MailPackResponse(
            id=pack["id"],
            before_image_url=prospect.satellite_image_url,
            after_image_url=_to_public_output_url(mockup_path) or "",
            before_after_image_url=_to_public_output_url(before_after_path) or "",
            pdf_url=_to_public_output_url(pack.get("pdf_path")) or "",
            email_subject=pack["email_subject"],
            email_body=pack["email_body"],
            outreach_email=pack["outreach"]["cold_email"],
        )
    except Exception as e:
        logger.error("Mail pack generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Mail pack generation failed: {e}")


@router.post("/search/mail-pack/send")
async def send_mail_pack_email(request: MailPackSendRequest):
    """Send outreach email using SMTP when configured."""
    try:
        result = await EmailService.send_pack_email(
            mailing_pack=request.mailing_pack,
            recipient_email=request.recipient_email,
            dry_run=False,
            via="smtp",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")
