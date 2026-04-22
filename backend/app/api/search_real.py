"""Google-only search and mail-pack endpoints."""
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..analysis.mailing_pack import MailingPackGenerator
from ..analysis.visualization import VizGenerator
from ..core.config import get_settings
from ..integrations.google_places import GooglePlacesClient
from ..schemas.area_mass_search import AreaMassSearchRequest
from ..services.area_mass_search import AreaMassSearchService
from ..services.email_service import EmailService
from ..services.google_geocode_service import (
    geocode_address_google,
    get_bounding_box,
    reverse_geocode,
    suggest_areas_google,
    suggest_cities_google,
)
from ..services.satellite_service import get_satellite_image_url
from ..services.solar_calculations import get_solar_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])

# In-memory lead registry for selected-session flows.
_LEAD_REGISTRY: dict[str, "SolarProspect"] = {}


class SearchRequest(BaseModel):
    country: str = "South Africa"
    province: str = ""
    city: str = ""
    suburb: str = ""
    street_name: Optional[str] = None
    street_number: Optional[str] = None
    postcode: Optional[str] = None
    radius_m: int = 1500
    min_roof_sqm: Optional[int] = None
    include_residential: bool = False


class AreaSearchRequest(BaseModel):
    place_id: str
    query: str
    lat: float
    lng: float
    radius_m: int = 1500


class PropertySearchRequest(BaseModel):
    place_id: str
    query: str


class PropertySearchResponse(BaseModel):
    lead_id: str
    name: str
    address: str
    roof_area_sqm: float
    panel_count: int
    capacity_kw: float
    annual_kwh: float
    savings_year: float
    building_type: str
    score: int
    lat: float
    lng: float


class AreaLead(BaseModel):
    lead_id: str
    name: str
    address: str
    roof_area_sqm: float
    building_type: str
    score: int
    lat: float
    lng: float


class AreaSearchResponse(BaseModel):
    count: int
    results: List[AreaLead]


class SolarProspect(BaseModel):
    lead_id: str
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
    savings_potential_display: str
    solar_score: int
    lead_grade: Optional[str] = None
    satellite_image_url: Optional[str] = None
    latitude: float
    longitude: float
    roof_polygon: Optional[List[Tuple[float, float]]] = None
    image_bbox: Optional[Tuple[float, float, float, float]] = None


class SearchResponse(BaseModel):
    results: List[SolarProspect]
    count: int
    search_area: str
    message: str


class MailPackRequest(BaseModel):
    prospect: SolarProspect


class LeadMailPackRequest(BaseModel):
    lead_id: str


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


class LeadEnrichRequest(BaseModel):
    prospect: SolarProspect


class AreaSuggestRequest(BaseModel):
    country: Optional[str] = "South Africa"
    province: Optional[str] = None
    city: Optional[str] = None
    query: Optional[str] = None


class AreaSuggestResponse(BaseModel):
    areas: List[str]


class CitySuggestRequest(BaseModel):
    country: Optional[str] = "South Africa"
    province: Optional[str] = None
    query: Optional[str] = None


class CitySuggestResponse(BaseModel):
    cities: List[str]


def _norm_text(value: Optional[str]) -> str:
    if not value:
        return ""
    normalized = "".join(ch.lower() for ch in value if ch.isalnum() or ch.isspace()).strip()
    words = normalized.split()
    replacements = {
        "st": "street",
        "str": "street",
        "strt": "street",
        "rd": "road",
        "ave": "avenue",
        "av": "avenue",
        "blvd": "boulevard",
        "dr": "drive",
        "ln": "lane",
        "ctr": "center",
        "ct": "court",
        "hwy": "highway",
    }
    canonical = [replacements.get(word, word) for word in words]
    return " ".join(canonical).strip()


def _norm_house_number(value: Optional[str]) -> str:
    if not value:
        return ""
    return "".join(ch.lower() for ch in value if ch.isalnum()).strip()


def _address_matches_request(
    candidate_street: Optional[str],
    candidate_number: Optional[str],
    candidate_full_address: Optional[str],
    requested_street: Optional[str],
    requested_number: Optional[str],
) -> bool:
    req_street = _norm_text(requested_street)
    req_num = _norm_house_number(requested_number)
    if not req_street:
        return False

    cand_street = _norm_text(candidate_street)
    cand_full = _norm_text(candidate_full_address)

    street_match = False
    if cand_street:
        street_match = req_street in cand_street or cand_street in req_street
    if not street_match and cand_full:
        street_match = req_street in cand_full
    if not street_match:
        req_tokens = {t for t in req_street.split() if len(t) >= 3}
        cand_tokens = {t for t in cand_street.split() if len(t) >= 3}
        full_tokens = {t for t in cand_full.split() if len(t) >= 3}
        all_tokens = cand_tokens | full_tokens
        if req_tokens and req_tokens.issubset(all_tokens):
            street_match = True
    if not street_match:
        return False

    if not req_num:
        return True

    cand_num = _norm_house_number(candidate_number)
    if cand_num:
        return cand_num == req_num

    # Fall back to full address text when house number is not split into components.
    return req_num in _norm_house_number(candidate_full_address)


def _build_exact_queries(request: SearchRequest) -> List[str]:
    number = (request.street_number or "").strip()
    street = (request.street_name or "").strip()
    suburb = (request.suburb or "").strip()
    city = (request.city or "").strip()
    province = (request.province or "").strip()
    postcode = (request.postcode or "").strip()
    country = (request.country or "South Africa").strip()

    base = f"{number} {street}".strip()
    candidates = [
        ", ".join([p for p in [base, suburb, city, province, postcode, country] if p]),
        ", ".join([p for p in [base, suburb, city, province, country] if p]),
        ", ".join([p for p in [base, city, province, country] if p]),
        ", ".join([p for p in [base, suburb, country] if p]),
        ", ".join([p for p in [base, country] if p]),
    ]

    seen = set()
    out: List[str] = []
    for item in candidates:
        q = item.strip()
        if not q:
            continue
        k = q.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(q)
    return out


def _parse_inline_street(value: Optional[str]) -> Tuple[str, str]:
    """Best-effort parse for inline address text like '98 Richmond Street'."""
    raw = (value or "").strip().split(",")[0].strip()
    if not raw:
        return "", ""

    # number + street-name tokens
    match = re.match(r"^\s*(\d+[a-zA-Z]?)\s+(.+?)\s*$", raw)
    if not match:
        return "", ""

    number = match.group(1).strip()
    street = match.group(2).strip()
    if len(street) < 3:
        return "", ""

    return number, street


def _resolve_exact_address_geocode(request: SearchRequest):
    street = (request.street_name or "").strip()
    number = (request.street_number or "").strip()

    nearest_geo = None
    for query in _build_exact_queries(request):
        geo = geocode_address_google(query, country=request.country or "South Africa")
        if not geo:
            continue

        if nearest_geo is None:
            nearest_geo = geo

        if _address_matches_request(
            geo.street,
            geo.house_number,
            geo.address,
            street,
            number,
        ):
            return geo, True

    # Structured retry path to improve component-level matching quality.
    structured_geo = geocode_address_google(
        f"{number} {street}".strip(),
        city=request.city or "",
        province=request.province or "",
        suburb=request.suburb or "",
        postcode=request.postcode or "",
        country=request.country or "South Africa",
    )
    if structured_geo:
        if nearest_geo is None:
            nearest_geo = structured_geo
        if _address_matches_request(
            structured_geo.street,
            structured_geo.house_number,
            structured_geo.address,
            street,
            number,
        ):
            return structured_geo, True

    return nearest_geo, False


def _lead_grade_from_score(score: int) -> str:
    if score >= 88:
        return "A+ HOT LEAD"
    if score >= 76:
        return "A GOOD LEAD"
    if score >= 60:
        return "B MEDIUM"
    return "C LOW"


def _to_public_output_url(path_value: Optional[str]) -> Optional[str]:
    if not path_value:
        return None
    path_obj = Path(path_value)
    settings = get_settings()
    output_root = Path(settings.OUTPUT_BASE_PATH).resolve()

    try:
        resolved = path_obj.resolve(strict=False)
    except Exception:
        return None

    if not str(resolved).startswith(str(output_root)):
        return None

    rel = resolved.relative_to(output_root).as_posix()
    return f"/output/{rel}"


def _safe(value, default):
    return value if value is not None else default


def _estimate_roof_for_place(types: List[str], name: Optional[str], votes: Optional[int]) -> float:
    t = set(types or [])
    label = (name or "").lower()

    if {"shopping_mall", "supermarket", "department_store"}.intersection(t):
        return 2400.0
    if {"warehouse", "industrial", "factory"}.intersection(t):
        return 1800.0
    if {"school", "university", "hospital"}.intersection(t):
        return 1200.0
    if {"store", "point_of_interest"}.intersection(t):
        if (votes or 0) > 200:
            return 900.0
        if "center" in label or "centre" in label:
            return 1100.0
        return 650.0
    return 500.0


def _register_lead(prospect: SolarProspect) -> None:
    if prospect.lead_id:
        _LEAD_REGISTRY[prospect.lead_id] = prospect


async def _build_mailpack_from_prospect(base_prospect: SolarProspect) -> MailPackResponse:
    # Lazy-enrich on selection before expensive pack generation.
    prospect = _enrich_prospect_lazy(base_prospect)

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
        logger.warning("Mockup generation failed for %s: %s", prospect.lead_id, viz_error)

    if mockup_path:
        try:
            before_after_path = await VizGenerator.generate_before_after(
                before_image_path=prospect.satellite_image_url,
                mockup_image_path=mockup_path,
            )
        except Exception as compare_error:
            logger.warning("Before/after generation failed for %s: %s", prospect.lead_id, compare_error)

    pack = MailingPackGenerator.generate(
        prospect={
            "id": prospect.lead_id,
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


def _enrich_prospect_lazy(prospect: SolarProspect) -> SolarProspect:
    """Lazy enrichment for a single selected lead; failures stay local to each task."""
    settings = get_settings()
    places = GooglePlacesClient(settings.GOOGLE_SERVER_KEY or settings.GOOGLE_MAPS_API_KEY)

    # Base values from the scan result.
    website = prospect.website
    phone = prospect.phone
    email = prospect.email
    business_name = prospect.business_name
    address = prospect.address
    building_type = prospect.building_type or "commercial"
    roof_area_sqm = float(max(prospect.roof_area_sqm or 0.0, 120.0))

    # Task 1: place details lookup for this one lead.
    try:
        if prospect.lead_id and not prospect.lead_id.startswith("google-"):
            details = places.place_details(prospect.lead_id) or {}
            website = _safe(details.get("website"), website)
            phone = _safe(details.get("formatted_phone_number") or details.get("international_phone_number"), phone)
            business_name = _safe(details.get("name"), business_name)
            address = _safe(details.get("formatted_address"), address)
            if details.get("types"):
                building_type = details.get("types")[0] or building_type
    except Exception as details_error:
        logger.warning("Lead details enrichment failed for %s: %s", prospect.lead_id, details_error)

    # Task 2: website email scrape (single lead only).
    try:
        if not email and website:
            email = places.discover_website_email(website)
    except Exception as scrape_error:
        logger.warning("Lead website scrape failed for %s: %s", prospect.lead_id, scrape_error)

    # Task 3: solar report recompute from current lead values.
    try:
        solar = get_solar_stats(roof_area_sqm, building_type, province=prospect.city or "")
    except Exception as solar_error:
        logger.warning("Lead solar enrichment failed for %s: %s", prospect.lead_id, solar_error)
        solar = {
            "roof_area_sqm": roof_area_sqm,
            "estimated_panel_count": prospect.estimated_panel_count,
            "capacity_low_kw": prospect.capacity_low_kw,
            "capacity_high_kw": prospect.capacity_high_kw,
            "annual_kwh_mid": prospect.annual_kwh,
            "savings_low": prospect.savings_low,
            "savings_high": prospect.savings_high,
            "solar_score": prospect.solar_score,
        }

    # Task 4: image generation url for this one lead.
    image_url = prospect.satellite_image_url
    try:
        image_url = get_satellite_image_url(prospect.latitude, prospect.longitude)
    except Exception as image_error:
        logger.warning("Lead image enrichment failed for %s: %s", prospect.lead_id, image_error)

    score = int(_safe(solar.get("solar_score"), prospect.solar_score))
    return SolarProspect(
        lead_id=prospect.lead_id,
        address=address,
        suburb=prospect.suburb,
        city=prospect.city,
        business_name=business_name,
        building_type=building_type,
        website=website,
        phone=phone,
        email=email,
        contact_person=prospect.contact_person,
        roof_area_sqm=float(_safe(solar.get("roof_area_sqm"), roof_area_sqm)),
        estimated_panel_count=int(_safe(solar.get("estimated_panel_count"), prospect.estimated_panel_count)),
        capacity_low_kw=float(_safe(solar.get("capacity_low_kw"), prospect.capacity_low_kw)),
        capacity_high_kw=float(_safe(solar.get("capacity_high_kw"), prospect.capacity_high_kw)),
        annual_kwh=float(_safe(solar.get("annual_kwh_mid"), prospect.annual_kwh)),
        savings_low=float(_safe(solar.get("savings_low"), prospect.savings_low)),
        savings_high=float(_safe(solar.get("savings_high"), prospect.savings_high)),
        savings_potential_display=(
            f"R {int(float(_safe(solar.get('savings_low'), prospect.savings_low)))//1000}k - "
            f"R {int(float(_safe(solar.get('savings_high'), prospect.savings_high)))//1000}k / year"
        ),
        solar_score=score,
        lead_grade=_lead_grade_from_score(score),
        satellite_image_url=image_url,
        latitude=prospect.latitude,
        longitude=prospect.longitude,
        roof_polygon=prospect.roof_polygon,
        image_bbox=prospect.image_bbox,
    )


@router.post("/areas/suggest", response_model=AreaSuggestResponse)
async def suggest_areas(request: AreaSuggestRequest) -> AreaSuggestResponse:
    areas = suggest_areas_google(
        query=request.query or "",
        city=request.city or "",
        province=request.province or "",
        country=request.country or "South Africa",
        limit=12,
    )
    return AreaSuggestResponse(areas=areas)


@router.post("/cities/suggest", response_model=CitySuggestResponse)
async def suggest_cities(request: CitySuggestRequest) -> CitySuggestResponse:
    cities = suggest_cities_google(
        query=request.query or "",
        province=request.province or "",
        country=request.country or "South Africa",
        limit=12,
    )
    return CitySuggestResponse(cities=cities)


@router.post("/search", response_model=SearchResponse)
async def search_real_prospects(request: SearchRequest) -> SearchResponse:
    try:
        min_roof = request.min_roof_sqm if request.min_roof_sqm is not None else 120

        raw_suburb = (request.suburb or "").strip()
        inline_number, inline_street = _parse_inline_street(raw_suburb)
        effective_street_name = (request.street_name or "").strip() or inline_street
        effective_street_number = (request.street_number or "").strip() or inline_number
        effective_suburb = raw_suburb
        if inline_street and "," in raw_suburb:
            tail = raw_suburb.split(",", 1)[1].strip()
            if tail:
                effective_suburb = tail
        if inline_street and effective_suburb.lower() == f"{inline_number} {inline_street}".strip().lower():
            # If user typed a full address into suburb/query field, keep suburb empty for cleaner geocoding.
            effective_suburb = ""

        has_street = bool(effective_street_name)
        if has_street:
            query = ", ".join(
                [
                    p
                    for p in [
                        " ".join(
                            [
                                effective_street_number,
                                effective_street_name,
                            ]
                        ).strip(),
                        effective_suburb,
                        (request.city or "").strip(),
                        (request.province or "").strip(),
                        (request.postcode or "").strip(),
                        (request.country or "South Africa").strip(),
                    ]
                    if p
                ]
            )

            exact_request = SearchRequest(
                country=request.country,
                province=request.province,
                city=request.city,
                suburb=effective_suburb,
                street_name=effective_street_name,
                street_number=effective_street_number,
                postcode=request.postcode,
                radius_m=request.radius_m,
                min_roof_sqm=request.min_roof_sqm,
                include_residential=request.include_residential,
            )

            geo, is_exact_match = _resolve_exact_address_geocode(exact_request)
            if not geo:
                return SearchResponse(results=[], count=0, search_area=query, message="Address not found.")

            if not is_exact_match:
                return SearchResponse(
                    results=[],
                    count=0,
                    search_area=query,
                    message=(
                        "Closest address was found but street/number did not match exactly. "
                        "Please confirm the exact street number and suburb."
                    ),
                )

            roof_sqm = float(max(min_roof, 120))
            solar = get_solar_stats(roof_sqm, "residential", province=request.province or "")

            response = SearchResponse(
                results=[
                    SolarProspect(
                        lead_id=f"google-{geo.latitude:.6f}-{geo.longitude:.6f}",
                        address=geo.address,
                        suburb=geo.suburb,
                        city=geo.city,
                        business_name=None,
                        building_type="residential",
                        roof_area_sqm=solar["roof_area_sqm"],
                        estimated_panel_count=solar["estimated_panel_count"],
                        capacity_low_kw=solar["capacity_low_kw"],
                        capacity_high_kw=solar["capacity_high_kw"],
                        annual_kwh=solar["annual_kwh_mid"],
                        savings_low=solar["savings_low"],
                        savings_high=solar["savings_high"],
                        savings_potential_display=f"R {int(solar['savings_low'])//1000}k - R {int(solar['savings_high'])//1000}k / year",
                        solar_score=solar["solar_score"],
                        lead_grade=_lead_grade_from_score(solar["solar_score"]),
                        satellite_image_url=None,
                        latitude=geo.latitude,
                        longitude=geo.longitude,
                    )
                ],
                count=1,
                search_area=geo.address,
                message="Matched address via fast scan. Open a lead for full enrichment.",
            )
            return response

        center_query = ", ".join(
            [
                (request.suburb or "").strip(),
                (request.city or "").strip(),
                (request.province or "").strip(),
                (request.country or "South Africa").strip(),
            ]
        ).strip(", ")

        area_req = AreaMassSearchRequest(
            query=center_query,
            radius_m=max(300, request.radius_m),
            tile_size_m=500,
            page=1,
            page_size=25,
            fast_scan=True,
        )
        service = AreaMassSearchService()
        try:
            ranked, _, _ = service.search_area(area_req)
        except ValueError as resolve_error:
            logger.warning("Area search bounds resolution failed for '%s': %s", center_query, resolve_error)
            # Fallback for typed-area frontend flow: use text search even when area bounds cannot resolve.
            settings = get_settings()
            places = GooglePlacesClient(settings.GOOGLE_SERVER_KEY or settings.GOOGLE_MAPS_API_KEY)
            text_rows = places.search_text(center_query, max_pages=1)

            fallback_results: List[SolarProspect] = []
            for row in text_rows:
                try:
                    geometry = (row.get("geometry") or {}).get("location") or {}
                    lat = geometry.get("lat")
                    lng = geometry.get("lng")
                    if lat is None or lng is None:
                        continue

                    pid = row.get("place_id") or f"text-{lat}-{lng}"
                    business_type = ((row.get("types") or ["commercial"])[0])
                    base_roof = 650.0
                    if "warehouse" in (row.get("types") or []) or "industrial" in (row.get("types") or []):
                        base_roof = 1800.0
                    elif "shopping_mall" in (row.get("types") or []) or "supermarket" in (row.get("types") or []):
                        base_roof = 2400.0

                    if base_roof < min_roof:
                        continue

                    stats = get_solar_stats(base_roof, business_type, province=request.province or "")
                    fallback_results.append(
                        SolarProspect(
                            lead_id=pid,
                            address=row.get("formatted_address") or row.get("name") or center_query,
                            suburb=request.suburb or None,
                            city=request.city or None,
                            business_name=row.get("name"),
                            building_type=business_type,
                            website=None,
                            phone=None,
                            email=None,
                            roof_area_sqm=stats["roof_area_sqm"],
                            estimated_panel_count=stats["estimated_panel_count"],
                            capacity_low_kw=stats["capacity_low_kw"],
                            capacity_high_kw=stats["capacity_high_kw"],
                            annual_kwh=stats["annual_kwh_mid"],
                            savings_low=stats["savings_low"],
                            savings_high=stats["savings_high"],
                            savings_potential_display=(
                                f"R {int(stats['savings_low'])//1000}k - "
                                f"R {int(stats['savings_high'])//1000}k / year"
                            ),
                            solar_score=stats["solar_score"],
                            lead_grade=_lead_grade_from_score(stats["solar_score"]),
                            satellite_image_url=None,
                            latitude=float(lat),
                            longitude=float(lng),
                        )
                    )
                except Exception as fallback_row_error:
                    logger.warning("Skipping fallback text lead due to parse error: %s", fallback_row_error)
                    continue

            return SearchResponse(
                results=fallback_results,
                count=len(fallback_results),
                search_area=center_query,
                message=(
                    f"Found {len(fallback_results)} leads in {center_query}. "
                    "Fallback text scan was used for this area."
                    if fallback_results
                    else (
                        "Area could not be resolved to a search region. "
                        "Please refine suburb/city and try again."
                    )
                ),
            )

        results: List[SolarProspect] = []
        for row in ranked:
            try:
                if row.estimated_roof_sqm < min_roof:
                    continue
                stats = get_solar_stats(row.estimated_roof_sqm, row.business_type, province=request.province or "")
                results.append(
                    SolarProspect(
                        lead_id=row.place_id,
                        address=row.address,
                        suburb=request.suburb or None,
                        city=request.city or None,
                        business_name=row.name,
                        building_type=row.business_type,
                        website=None,
                        phone=None,
                        email=None,
                        roof_area_sqm=stats["roof_area_sqm"],
                        estimated_panel_count=stats["estimated_panel_count"],
                        capacity_low_kw=stats["capacity_low_kw"],
                        capacity_high_kw=stats["capacity_high_kw"],
                        annual_kwh=stats["annual_kwh_mid"],
                        savings_low=stats["savings_low"],
                        savings_high=stats["savings_high"],
                        savings_potential_display=f"R {int(stats['savings_low'])//1000}k - R {int(stats['savings_high'])//1000}k / year",
                        solar_score=stats["solar_score"],
                        lead_grade=_lead_grade_from_score(stats["solar_score"]),
                        satellite_image_url=None,
                        latitude=row.lat,
                        longitude=row.lng,
                    )
                )
            except Exception as row_error:
                logger.warning("Skipping failed lead %s during fast scan: %s", row.place_id, row_error)
                continue

        return SearchResponse(
            results=results,
            count=len(results),
            search_area=center_query,
            message=(
                f"Found {len(results)} leads in {center_query}. "
                "Select a lead to run full enrichment and mail-pack generation."
            ),
        )
    except Exception as e:
        logger.error("Search error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/area-search", response_model=AreaSearchResponse)
async def area_search(request: AreaSearchRequest) -> AreaSearchResponse:
    """Lightweight area lead generation. No enrichment, scraping, or mail-pack work here."""
    try:
        radius = max(300, min(int(request.radius_m or 1500), 4000))
        area_req = AreaMassSearchRequest(
            place_id=request.place_id,
            query=(request.query or "").strip(),
            center_lat=request.lat,
            center_lng=request.lng,
            radius_m=radius,
            tile_size_m=500,
            page=1,
            page_size=30,
            fast_scan=True,
        )

        service = AreaMassSearchService()
        try:
            ranked, _, _ = service.search_area(area_req)
        except ValueError:
            settings = get_settings()
            places = GooglePlacesClient(settings.GOOGLE_SERVER_KEY or settings.GOOGLE_MAPS_API_KEY)
            ranked = places.search_nearby(
                lat=request.lat,
                lng=request.lng,
                radius=radius,
                keyword=(request.query or "").strip(),
                max_pages=1,
            )

        leads: List[AreaLead] = []
        for row in ranked:
            try:
                if isinstance(row, dict):
                    geometry = (row.get("geometry") or {}).get("location") or {}
                    lat_val = geometry.get("lat")
                    lng_val = geometry.get("lng")
                    if lat_val is None or lng_val is None:
                        continue

                    place_id = row.get("place_id") or f"nearby-{lat_val}-{lng_val}"
                    name = row.get("name") or "Unknown"
                    address = row.get("formatted_address") or row.get("vicinity") or name
                    types = row.get("types") or []
                    building_type = types[0] if types else "commercial"
                    roof_seed = _estimate_roof_for_place(types, name, row.get("user_ratings_total"))
                    lead_score = 0
                else:
                    place_id = row.place_id
                    name = row.name or "Unknown"
                    address = row.address or ""
                    lat_val = row.lat
                    lng_val = row.lng
                    building_type = row.business_type or "commercial"
                    roof_seed = row.estimated_roof_sqm or 0.0
                    lead_score = row.lead_score or 0

                roof_sqm = float(max(roof_seed, 120.0))
                score = int(get_solar_stats(roof_sqm, building_type).get("solar_score", lead_score))
                leads.append(
                    AreaLead(
                        lead_id=place_id,
                        name=name,
                        address=address,
                        roof_area_sqm=round(roof_sqm, 1),
                        building_type=building_type,
                        score=score,
                        lat=lat_val,
                        lng=lng_val,
                    )
                )

                solar = get_solar_stats(roof_sqm, building_type)
                _register_lead(
                    SolarProspect(
                        lead_id=place_id,
                        address=address,
                        suburb=None,
                        city=None,
                        business_name=name,
                        building_type=building_type,
                        roof_area_sqm=roof_sqm,
                        estimated_panel_count=int(solar.get("estimated_panel_count", 0)),
                        capacity_low_kw=float(solar.get("capacity_low_kw", 0.0)),
                        capacity_high_kw=float(solar.get("capacity_high_kw", 0.0)),
                        annual_kwh=float(solar.get("annual_kwh_mid", 0.0)),
                        savings_low=float(solar.get("savings_low", 0.0)),
                        savings_high=float(solar.get("savings_high", 0.0)),
                        savings_potential_display=(
                            f"R {int(float(solar.get('savings_low', 0)))//1000}k - "
                            f"R {int(float(solar.get('savings_high', 0)))//1000}k / year"
                        ),
                        solar_score=score,
                        lead_grade=_lead_grade_from_score(score),
                        satellite_image_url=None,
                        latitude=lat_val,
                        longitude=lng_val,
                    )
                )
            except Exception as row_error:
                if isinstance(row, dict):
                    row_id = row.get("place_id", "unknown")
                else:
                    row_id = getattr(row, "place_id", "unknown")
                logger.warning("Skipping bad area-search row %s: %s", row_id, row_error)
                continue

        return AreaSearchResponse(count=len(leads), results=leads)
    except Exception as e:
        logger.error("Area search failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Area search failed: {str(e)}")


@router.post("/property-search", response_model=PropertySearchResponse)
async def property_search(request: PropertySearchRequest) -> PropertySearchResponse:
    try:
        settings = get_settings()
        api_key = settings.GOOGLE_SERVER_KEY or settings.GOOGLE_MAPS_API_KEY
        if not api_key:
            raise HTTPException(status_code=503, detail="Google Places key is not configured")

        # Use the Places API (New) v1, consistent with /api/places/autocomplete and /api/places/{id}.
        place_resp = requests.get(
            f"https://places.googleapis.com/v1/places/{request.place_id}",
            headers={
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": (
                    "id,displayName,formattedAddress,location,"
                    "types,userRatingCount,websiteUri,"
                    "nationalPhoneNumber,internationalPhoneNumber"
                ),
            },
            params={"languageCode": "en"},
            timeout=10,
        )
        if place_resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Property not found")
        if place_resp.status_code >= 400:
            logger.error("Places API error %s: %s", place_resp.status_code, place_resp.text)
            raise HTTPException(status_code=502, detail="Places API request failed")

        details = place_resp.json()
        location = details.get("location") or {}
        lat = location.get("latitude")
        lng = location.get("longitude")
        if lat is None or lng is None:
            raise HTTPException(status_code=422, detail="Property coordinates unavailable")

        types = details.get("types") or []
        votes = details.get("userRatingCount")
        display_name = details.get("displayName") or {}
        name = display_name.get("text") or request.query or "Selected Property"
        address = details.get("formattedAddress") or request.query
        building_type = types[0] if types else "commercial"
        roof_sqm = _estimate_roof_for_place(types, name, votes)
        solar = get_solar_stats(roof_sqm, building_type)
        score = int(solar.get("solar_score", 0))

        lead_id = request.place_id
        prospect = SolarProspect(
            lead_id=lead_id,
            address=address,
            suburb=None,
            city=None,
            business_name=name,
            building_type=building_type,
            website=details.get("websiteUri"),
            phone=details.get("nationalPhoneNumber") or details.get("internationalPhoneNumber"),
            roof_area_sqm=float(solar.get("roof_area_sqm", roof_sqm)),
            estimated_panel_count=int(solar.get("estimated_panel_count", 0)),
            capacity_low_kw=float(solar.get("capacity_low_kw", 0.0)),
            capacity_high_kw=float(solar.get("capacity_high_kw", 0.0)),
            annual_kwh=float(solar.get("annual_kwh_mid", 0.0)),
            savings_low=float(solar.get("savings_low", 0.0)),
            savings_high=float(solar.get("savings_high", 0.0)),
            savings_potential_display=(
                f"R {int(float(solar.get('savings_low', 0)))//1000}k - "
                f"R {int(float(solar.get('savings_high', 0)))//1000}k / year"
            ),
            solar_score=score,
            lead_grade=_lead_grade_from_score(score),
            satellite_image_url=None,
            latitude=float(lat),
            longitude=float(lng),
        )
        _register_lead(prospect)

        return PropertySearchResponse(
            lead_id=lead_id,
            name=name,
            address=address,
            roof_area_sqm=float(solar.get("roof_area_sqm", roof_sqm)),
            panel_count=int(solar.get("estimated_panel_count", 0)),
            capacity_kw=float(solar.get("capacity_mid_kw", 0.0)),
            annual_kwh=float(solar.get("annual_kwh_mid", 0.0)),
            savings_year=float(solar.get("savings_mid", 0.0)),
            building_type=building_type,
            score=score,
            lat=float(lat),
            lng=float(lng),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Property search failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Property search failed: {str(e)}")


@router.post("/mailpack", response_model=MailPackResponse)
async def generate_mail_pack_by_lead(request: LeadMailPackRequest) -> MailPackResponse:
    try:
        prospect = _LEAD_REGISTRY.get(request.lead_id)
        if not prospect:
            raise HTTPException(status_code=404, detail="Lead not found. Re-run search and select the lead again.")
        return await _build_mailpack_from_prospect(prospect)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Mail pack generation failed for lead_id %s: %s", request.lead_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Mail pack generation failed: {str(e)}")


@router.post("/search/mail-pack", response_model=MailPackResponse)
async def generate_mail_pack(request: MailPackRequest) -> MailPackResponse:
    try:
        _register_lead(request.prospect)
        return await _build_mailpack_from_prospect(request.prospect)
    except Exception as e:
        logger.error("Mail pack generation failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Mail pack generation failed: {str(e)}")


@router.post("/search/mail-pack/send")
async def send_mail_pack(request: MailPackSendRequest):
    try:
        email_service = EmailService()
        if not email_service.is_configured():
            raise HTTPException(
                status_code=503,
                detail=(
                    "Email service not configured. Set SMTP credentials or SENDGRID_API_KEY in backend environment."
                ),
            )

        result = await email_service.send_cold_email(
            recipient_email=request.recipient_email,
            subject=request.mailing_pack.get("email_subject", "Solar savings opportunity"),
            body=request.mailing_pack.get("email_body", ""),
            recipient_name=request.mailing_pack.get("contact_name"),
        )

        if result.get("success"):
            return {
                "status": "sent",
                "recipient_email": request.recipient_email,
                "provider": result.get("provider"),
                "message_id": result.get("message_id"),
            }

        raise HTTPException(status_code=502, detail=result.get("error") or "Email sending failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Mail pack send failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Mail pack send failed: {str(e)}")


@router.post("/search/lead/enrich", response_model=SolarProspect)
async def enrich_single_lead(request: LeadEnrichRequest) -> SolarProspect:
    try:
        return _enrich_prospect_lazy(request.prospect)
    except Exception as e:
        logger.error("Single-lead enrichment failed: %s", str(e), exc_info=True)
        # Never break UX flow; return original prospect if enrichment fails.
        return request.prospect
