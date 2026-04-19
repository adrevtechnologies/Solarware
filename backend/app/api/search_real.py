"""
REAL Search Engine - No fake data, no placeholders
Uses live APIs: Nominatim + Overpass + Solar calculations
"""
import logging
import json
import hashlib
import math
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Tuple
from ..services.nominatim_service import (
    geocode_address,
    geocode_address_google,
    suggest_areas_google,
    reverse_geocode,
    get_bounding_box,
)
from ..services.overpass_service import (
    query_commercial_buildings,
    filter_nearby_buildings,
    query_exact_address_points,
)
from ..services.solar_calculations import get_solar_stats
from ..services.satellite_service import get_satellite_image_url, get_satellite_image_url_for_polygon
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
    radius_m: int = 500  # 250, 500, 1000
    
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
    roof_polygon: Optional[List[Tuple[float, float]]] = None
    image_bbox: Optional[Tuple[float, float, float, float]] = None  # min_lat, max_lat, min_lon, max_lon


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


class AreaSuggestRequest(BaseModel):
    country: Optional[str] = "South Africa"
    province: Optional[str] = None
    city: Optional[str] = None
    query: Optional[str] = None


class AreaSuggestResponse(BaseModel):
    areas: List[str]


KNOWN_AREA_CENTERS = {
    ("south africa", "western cape", "cape town", "goodwood"): (-33.9165, 18.5670, "Goodwood, Cape Town, Western Cape"),
}


def _known_center_from_context(
    country: Optional[str],
    province: Optional[str],
    city: Optional[str],
    suburb: Optional[str],
) -> Optional[Tuple[float, float, str]]:
    key = (
        (country or "").strip().lower(),
        (province or "").strip().lower(),
        (city or "").strip().lower(),
        (suburb or "").strip().lower(),
    )
    return KNOWN_AREA_CENTERS.get(key)


def _point_in_polygon(lat: float, lon: float, polygon: List[Tuple[float, float]]) -> bool:
    if len(polygon) < 3:
        return False
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        yi, xi = polygon[i]
        yj, xj = polygon[j]
        intersects = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def _meters_per_degree(lat: float) -> Tuple[float, float]:
    return 111_000.0, 111_000.0 * math.cos(math.radians(lat))


def _distance_point_segment_m(
    point_lat: float,
    point_lon: float,
    a_lat: float,
    a_lon: float,
    b_lat: float,
    b_lon: float,
) -> float:
    m_lat, m_lon = _meters_per_degree(point_lat)
    px, py = point_lon * m_lon, point_lat * m_lat
    ax, ay = a_lon * m_lon, a_lat * m_lat
    bx, by = b_lon * m_lon, b_lat * m_lat
    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    ab2 = abx * abx + aby * aby
    if ab2 <= 0:
        return math.sqrt((px - ax) ** 2 + (py - ay) ** 2)
    t = max(0.0, min(1.0, (apx * abx + apy * aby) / ab2))
    cx, cy = ax + t * abx, ay + t * aby
    return math.sqrt((px - cx) ** 2 + (py - cy) ** 2)


def _distance_point_polygon_m(lat: float, lon: float, polygon: List[Tuple[float, float]]) -> float:
    if not polygon:
        return float("inf")
    if _point_in_polygon(lat, lon, polygon):
        return 0.0

    min_distance = float("inf")
    closed = polygon + [polygon[0]]
    for i in range(len(closed) - 1):
        a_lat, a_lon = closed[i]
        b_lat, b_lon = closed[i + 1]
        d = _distance_point_segment_m(lat, lon, a_lat, a_lon, b_lat, b_lon)
        if d < min_distance:
            min_distance = d
    return min_distance


def _select_exact_target_building(buildings, lat: float, lon: float, max_distance_m: float = 30.0):
    if not buildings:
        return None

    scored = []
    for b in buildings:
        d = _distance_point_polygon_m(lat, lon, b.nodes)
        scored.append((d, b))

    scored.sort(key=lambda item: item[0])
    best_distance, best_building = scored[0]
    if best_distance > max_distance_m:
        return None
    return best_building


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return "".join(ch for ch in value.lower() if ch.isalnum() or ch.isspace()).strip()


def _normalize_house_number(value: Optional[str]) -> str:
    if not value:
        return ""
    return "".join(ch for ch in value.lower() if ch.isalnum()).strip()


def _address_text_matches_request(
    full_address: Optional[str],
    requested_street: Optional[str],
    requested_number: Optional[str],
) -> bool:
    if not full_address or not requested_street or not requested_number:
        return False

    text = _normalize_text(full_address)
    street = _normalize_text(requested_street)
    number = _normalize_house_number(requested_number)
    if not street or not number:
        return False

    return (street in text) and (number in _normalize_house_number(text))


def _reverse_point_matches_request(
    lat: float,
    lon: float,
    requested_street: Optional[str],
    requested_number: Optional[str],
) -> bool:
    rg = reverse_geocode(lat, lon) or {}
    if _exact_address_match(
        rg.get("street"),
        rg.get("house_number"),
        requested_street,
        requested_number,
    ):
        return True

    return _address_text_matches_request(
        rg.get("address"),
        requested_street,
        requested_number,
    )


def _address_tag_matches(
    buildings,
    street_number: Optional[str],
    street_name: Optional[str],
):
    if not street_number or not street_name:
        return []

    target_number = _normalize_text(street_number)
    target_street = _normalize_text(street_name)
    matches = []
    for building in buildings:
        b_number = _normalize_text(getattr(building, "house_number", None))
        b_street = _normalize_text(getattr(building, "street", None))
        if not b_number or not b_street:
            continue
        if b_number == target_number and (target_street in b_street or b_street in target_street):
            matches.append(building)
    return matches


def _nearest_building_with_distance(buildings, lat: float, lon: float):
    if not buildings:
        return None, float("inf")
    scored = [(_distance_point_polygon_m(lat, lon, b.nodes), b) for b in buildings]
    scored.sort(key=lambda item: item[0])
    return scored[0][1], scored[0][0]


def _street_match(value: Optional[str], target: Optional[str]) -> bool:
    if not value or not target:
        return False
    a = _normalize_text(value)
    b = _normalize_text(target)
    return a == b or a in b or b in a


def _exact_address_match(
    candidate_street: Optional[str],
    candidate_number: Optional[str],
    requested_street: Optional[str],
    requested_number: Optional[str],
) -> bool:
    if not _street_match(candidate_street, requested_street):
        return False

    requested_number_norm = _normalize_house_number(requested_number)
    if not requested_number_norm:
        return True

    candidate_number_norm = _normalize_house_number(candidate_number)
    return bool(candidate_number_norm) and candidate_number_norm == requested_number_norm


def _find_exact_building_by_reverse_address(
    buildings,
    lat: float,
    lon: float,
    requested_street: Optional[str],
    requested_number: Optional[str],
):
    if not buildings or not requested_street:
        return None, float("inf")

    scored = sorted(
        [(_distance_point_polygon_m(lat, lon, b.nodes), b) for b in buildings],
        key=lambda item: item[0],
    )

    for distance_m, building in scored[:80]:
        rg = reverse_geocode(building.latitude, building.longitude) or {}
        if _exact_address_match(
            rg.get("street"),
            rg.get("house_number"),
            requested_street,
            requested_number,
        ):
            return building, distance_m

    return None, float("inf")


def _nearest_building_on_requested_street(
    buildings,
    lat: float,
    lon: float,
    requested_street: Optional[str],
):
    if not buildings or not requested_street:
        return None, float("inf")

    scored = sorted(
        [(_distance_point_polygon_m(lat, lon, b.nodes), b) for b in buildings],
        key=lambda item: item[0],
    )

    # First pass: explicit OSM addr:street tags on buildings.
    tagged = [(d, b) for d, b in scored if _street_match(getattr(b, "street", None), requested_street)]
    if tagged:
        return tagged[0][1], tagged[0][0]

    # Second pass: reverse-geocode top nearest candidates and enforce street match.
    for d, b in scored[:15]:
        rg = reverse_geocode(b.latitude, b.longitude) or {}
        if _street_match(rg.get("street"), requested_street):
            return b, d

    return None, float("inf")


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
        "mode": (
            "address"
            if (
                (request.street_number and request.street_number.strip())
                and (request.street_name and request.street_name.strip())
            )
            else "area"
        ),
        "country": request.country,
        "province": request.province,
        "city": request.city,
        "suburb": request.suburb,
        "street_number": request.street_number,
        "street_name": request.street_name,
        "radius_m": request.radius_m,
        "min_roof_sqm": request.min_roof_sqm,
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


@router.post("/areas/suggest", response_model=AreaSuggestResponse)
async def suggest_areas(request: AreaSuggestRequest) -> AreaSuggestResponse:
    """Suggest area/suburb names using Google Places API for dropdown usage."""
    areas = suggest_areas_google(
        query=request.query or "",
        city=request.city or "",
        province=request.province or "",
        country=request.country or "South Africa",
        limit=12,
    )
    return AreaSuggestResponse(areas=areas)


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
        query_str: Optional[str] = None
        exact_match_note: Optional[str] = None
        geocode_is_house_precise = False

        # STEP 1: Validate required context fields for V1.
        if not request.country or not request.province or not request.city or not request.suburb:
            return SearchResponse(
                results=[],
                count=0,
                search_area="",
                message="Country, province/state, city, and area/suburb are required.",
            )

        has_street_number = bool(request.street_number and request.street_number.strip())
        has_street_name = bool(request.street_name and request.street_name.strip())

        if has_street_number != has_street_name:
            return SearchResponse(
                results=[],
                count=0,
                search_area="",
                message=(
                    "Provide full street address (number and street) for exact search, "
                    "or leave address blank for area search."
                ),
            )

        is_exact_address = has_street_number and has_street_name
        logger.info("Search request: exact_address=%s", is_exact_address)

        if is_exact_address:
            query_str = f"{request.street_number or ''} {request.street_name}".strip()
            area_anchor = geocode_address(
                request.suburb,
                city=request.city,
                province=request.province,
                suburb=request.suburb,
                postcode="",
                country=request.country,
            )
            geo = geocode_address(
                query_str,
                city=request.city,
                province=request.province,
                suburb=request.suburb,
                postcode="",
                country=request.country,
            )

            # Prefer house-level geocoding when Google Maps key is configured.
            google_geo = geocode_address_google(
                query_str,
                city=request.city,
                province=request.province,
                suburb=request.suburb,
                postcode="",
                country=request.country,
            )
            if google_geo:
                # Use Google result when Nominatim misses house-number precision.
                if not geo or not _exact_address_match(
                    geo.street,
                    geo.house_number,
                    request.street_name,
                    request.street_number,
                ):
                    geo = google_geo
                    exact_match_note = (
                        f"Matched exact address {request.street_number or ''} {request.street_name} via Google geocoder."
                    )

            geocode_is_house_precise = bool(
                geo
                and _exact_address_match(
                    geo.street,
                    geo.house_number,
                    request.street_name,
                    request.street_number,
                )
            )

            if not geocode_is_house_precise and geo:
                geocode_is_house_precise = _address_text_matches_request(
                    geo.address,
                    request.street_name,
                    request.street_number,
                )

            if not geo:
                return SearchResponse(
                    results=[],
                    count=0,
                    search_area=query_str,
                    message="Address not found. Check street spelling and try again.",
                )

            if geo is not None:
                center_lat, center_lon = geo.latitude, geo.longitude
                radius_km = max(0.15, request.radius_m / 1000.0)
                search_area = geo.address

                # When geocoder resolves only street-level (no house-number precision),
                # widen search slightly but keep center anchored to exact geocode point.
                if request.street_number and not _exact_address_match(
                    geo.street,
                    geo.house_number,
                    request.street_name,
                    request.street_number,
                ):
                    radius_km = max(0.35, radius_km)

            # If geocoder returns only a street-level point, try exact addr tags from Overpass.
            if request.street_number and request.street_name:
                exact_addr_bbox = get_bounding_box(
                    center_lat,
                    center_lon,
                    max(0.35, request.radius_m / 1000.0),
                )
                exact_points = query_exact_address_points(
                    exact_addr_bbox[0],
                    exact_addr_bbox[1],
                    exact_addr_bbox[2],
                    exact_addr_bbox[3],
                    request.street_number,
                    request.street_name,
                )
                if not exact_points and area_anchor is not None:
                    # If geocoder point is off, retry exact OSM tags around selected suburb/city center.
                    area_bbox = get_bounding_box(
                        area_anchor.latitude,
                        area_anchor.longitude,
                        max(1.0, request.radius_m / 1000.0),
                    )
                    exact_points = query_exact_address_points(
                        area_bbox[0],
                        area_bbox[1],
                        area_bbox[2],
                        area_bbox[3],
                        request.street_number,
                        request.street_name,
                    )
                if exact_points:
                    center_lat, center_lon = exact_points[0]
                    radius_km = 0.12
                    geocode_is_house_precise = True
                    exact_match_note = (
                        f"Matched exact OSM address tags for {request.street_number} {request.street_name}."
                    )
        else:
            geo = geocode_address(
                request.suburb,
                city=request.city,
                province=request.province,
                postcode="",
                country=request.country,
            )
            if not geo:
                geo = geocode_address_google(
                    request.suburb,
                    city=request.city,
                    province=request.province,
                    suburb=request.suburb,
                    postcode="",
                    country=request.country,
                )
            if not geo:
                known_center = _known_center_from_context(
                    request.country,
                    request.province,
                    request.city,
                    request.suburb,
                )
                if not known_center:
                    return SearchResponse(
                        results=[],
                        count=0,
                        search_area=request.suburb,
                        message="Area not found. Check spelling and try again.",
                    )
                center_lat, center_lon, known_label = known_center
                radius_km = max(0.5, request.radius_m / 1000.0)
                search_area = known_label
                geo = None

            if geo is not None:
                center_lat, center_lon = geo.latitude, geo.longitude
                radius_km = max(0.5, request.radius_m / 1000.0)
                search_area = f"{request.suburb}, {request.city}, {request.province}"

        # STEP 2: QUERY OVERPASS FOR REAL BUILDINGS
        include_residential = is_exact_address

        logger.info(
            "Querying Overpass API for %s buildings near %s",
            "all addressable" if include_residential else "commercial",
            search_area,
        )
        
        min_lat, max_lat, min_lon, max_lon = get_bounding_box(center_lat, center_lon, radius_km)

        buildings = query_commercial_buildings(
            min_lat,
            max_lat,
            min_lon,
            max_lon,
            include_residential=include_residential,
            include_all_buildings=is_exact_address,
            min_polygon_area_sqm=20.0 if is_exact_address else 100.0,
        )

        if is_exact_address and not buildings:
            # Exact address can miss on tiny radius; retry wider before declaring no match.
            wider_radius_km = max(0.5, radius_km * 2)
            min_lat, max_lat, min_lon, max_lon = get_bounding_box(center_lat, center_lon, wider_radius_km)
            buildings = query_commercial_buildings(
                min_lat,
                max_lat,
                min_lon,
                max_lon,
                include_residential=True,
                include_all_buildings=True,
                min_polygon_area_sqm=20.0,
            )

        if is_exact_address:
            target_building = None
            tag_matched = _address_tag_matches(
                buildings,
                request.street_number,
                request.street_name,
            )
            if tag_matched:
                target_building, nearest_distance_m = _nearest_building_with_distance(
                    tag_matched,
                    center_lat,
                    center_lon,
                )
                exact_match_note = (
                    f"Matched exact OSM address tags for {request.street_number} {request.street_name}."
                )

        if is_exact_address and not target_building:
            # Only trust nearest-footprint selection when geocoder is house-number precise.
            if geocode_is_house_precise:
                target_building = _select_exact_target_building(
                    buildings,
                    center_lat,
                    center_lon,
                    max_distance_m=35.0,
                )

            if not target_building:
                reverse_match_building, reverse_match_distance_m = _find_exact_building_by_reverse_address(
                    buildings,
                    center_lat,
                    center_lon,
                    request.street_name,
                    request.street_number,
                )
                if reverse_match_building:
                    target_building = reverse_match_building
                    exact_match_note = (
                        f"Matched exact address {request.street_number or ''} {request.street_name} "
                        f"via reverse-geocoded building footprint ({reverse_match_distance_m:.0f}m from geocode point)."
                    )

            if not target_building:
                if (
                    geocode_is_house_precise
                    and geo is not None
                    and (
                        _reverse_point_matches_request(
                            center_lat,
                            center_lon,
                            request.street_name,
                            request.street_number,
                        )
                        or _address_text_matches_request(
                            geo.address,
                            request.street_name,
                            request.street_number,
                        )
                    )
                ):
                    fallback_image_url = get_satellite_image_url(center_lat, center_lon)
                    geo_result = reverse_geocode(center_lat, center_lon) or {}
                    fallback_address = geo_result.get("address") or geo.address or query_str or "Exact address"
                    point_pad_lat = 0.00025
                    point_pad_lon = 0.00025

                    fallback_prospect = SolarProspect(
                        osm_id=f"exact-point:{center_lat:.6f},{center_lon:.6f}",
                        address=fallback_address,
                        suburb=geo_result.get("suburb") or geo.suburb,
                        city=geo_result.get("city") or geo.city,
                        business_name=None,
                        building_type="exact_address_unmapped",
                        website=None,
                        phone=None,
                        email=None,
                        contact_person=None,
                        roof_area_sqm=0.0,
                        estimated_panel_count=0,
                        capacity_low_kw=0.0,
                        capacity_high_kw=0.0,
                        annual_kwh=0.0,
                        savings_low=0.0,
                        savings_high=0.0,
                        savings_potential_display="Unavailable - mapped roof footprint not found",
                        solar_score=0,
                        satellite_image_url=fallback_image_url,
                        latitude=center_lat,
                        longitude=center_lon,
                        roof_polygon=None,
                        image_bbox=(
                            center_lat - point_pad_lat,
                            center_lat + point_pad_lat,
                            center_lon - point_pad_lon,
                            center_lon + point_pad_lon,
                        ),
                    )

                    return SearchResponse(
                        results=[fallback_prospect],
                        count=1,
                        search_area=search_area,
                        message="Exact address found. No mapped roof footprint available, so image is centered on the exact address point.",
                    )

                return SearchResponse(
                    results=[],
                    count=0,
                    search_area=search_area,
                    message="No building footprint found for exact address.",
                )
            buildings = [target_building]
        
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
        if not is_exact_address:
            buildings = filter_nearby_buildings(buildings, center_lat, center_lon, radius_km)
        
        candidates_before_roof_filter = list(buildings)

        effective_min_roof_sqm = (
            request.min_roof_sqm
            if request.min_roof_sqm is not None
            else (20 if is_exact_address else 120)
        )
        buildings = [b for b in buildings if b.roof_area_sqm >= effective_min_roof_sqm]

        if is_exact_address and not buildings and candidates_before_roof_filter:
            buildings = candidates_before_roof_filter[:1]

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

                image_bbox = None
                if getattr(building, "nodes", None):
                    image_url = get_satellite_image_url_for_polygon(building.nodes)
                    lats = [n[0] for n in building.nodes]
                    lons = [n[1] for n in building.nodes]
                    pad_lat = (max(lats) - min(lats)) * 0.35 or 0.00012
                    pad_lon = (max(lons) - min(lons)) * 0.35 or 0.00012
                    image_bbox = (
                        min(lats) - pad_lat,
                        max(lats) + pad_lat,
                        min(lons) - pad_lon,
                        max(lons) + pad_lon,
                    )
                else:
                    image_url = get_satellite_image_url(
                        building.latitude,
                        building.longitude
                    )

                # Reverse geocode for full address
                geo_result = reverse_geocode(building.latitude, building.longitude)
                if geo_result and geo_result.get("address"):
                    address = geo_result.get("address")
                elif getattr(building, "street", None):
                    street_bits = [
                        getattr(building, "house_number", None),
                        getattr(building, "street", None),
                    ]
                    address = " ".join([bit for bit in street_bits if bit])
                else:
                    address = building.name or "Mapped commercial building in selected area"

                is_residential_result = building.building_type == "residential"
                business_name = None if is_residential_result else building.name
                website = None if is_residential_result else building.website
                phone = None if is_residential_result else building.phone
                email = None if is_residential_result else building.email
                contact_person = None if is_residential_result else building.contact_person

                # Format savings display
                savings_low = int(solar["savings_low"])
                savings_high = int(solar["savings_high"])
                savings_display = f"R {savings_low/1000:.0f}k - R {savings_high/1000:.0f}k / year"

                prospect = SolarProspect(
                    osm_id=building.osm_id,
                    address=address,
                    suburb=geo_result.get("suburb") if geo_result else None,
                    city=geo_result.get("city") if geo_result else None,
                    business_name=business_name,
                    building_type=building.building_type,
                    website=website,
                    phone=phone,
                    email=email,
                    contact_person=contact_person,
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
                    roof_polygon=building.nodes if getattr(building, "nodes", None) else None,
                    image_bbox=image_bbox,
                )
                
                results.append(prospect)

            except Exception as e:
                logger.error(f"Error processing building {building.osm_id}: {e}")
                continue

        logger.info(f"Search completed: {len(results)} prospects found in {search_area}")
        
        response_message = (
            exact_match_note
            if (is_exact_address and exact_match_note)
            else f"Found {len(results)} properties with solar potential in {search_area}"
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

        mockup_path: Optional[str] = None
        before_after_path: Optional[str] = None

        try:
            mockup_path = await VizGenerator.generate_mockup(
                satellite_image_path=prospect.satellite_image_url,
                panel_count=prospect.estimated_panel_count,
                roof_area_sqm=prospect.roof_area_sqm,
                system_capacity_kw=prospect.capacity_high_kw,
                roof_polygon=prospect.roof_polygon,
                image_bbox=prospect.image_bbox,
            )
        except Exception as viz_error:
            logger.warning("Mockup generation failed for %s: %s", prospect.osm_id, viz_error)

        if mockup_path:
            try:
                before_after_path = await VizGenerator.generate_before_after(
                    before_image_path=prospect.satellite_image_url,
                    mockup_image_path=mockup_path,
                )
            except Exception as compare_error:
                logger.warning("Before/after generation failed for %s: %s", prospect.osm_id, compare_error)

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
            after_image_url=_to_public_output_url(mockup_path) or prospect.satellite_image_url,
            before_after_image_url=_to_public_output_url(before_after_path) or prospect.satellite_image_url,
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
