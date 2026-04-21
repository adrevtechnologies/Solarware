"""Google-only search and mail-pack endpoints."""
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..analysis.mailing_pack import MailingPackGenerator
from ..analysis.visualization import VizGenerator
from ..core.config import get_settings
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
    satellite_image_url: str
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


class CitySuggestRequest(BaseModel):
    country: Optional[str] = "South Africa"
    province: Optional[str] = None
    query: Optional[str] = None


class CitySuggestResponse(BaseModel):
    cities: List[str]


def _norm_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return "".join(ch.lower() for ch in value if ch.isalnum() or ch.isspace()).strip()


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

        has_street = bool((request.street_name or "").strip())
        if has_street:
            query = ", ".join(
                [
                    p
                    for p in [
                        " ".join(
                            [
                                (request.street_number or "").strip(),
                                (request.street_name or "").strip(),
                            ]
                        ).strip(),
                        (request.suburb or "").strip(),
                        (request.city or "").strip(),
                        (request.province or "").strip(),
                        (request.postcode or "").strip(),
                        (request.country or "South Africa").strip(),
                    ]
                    if p
                ]
            )

            geo, is_exact_match = _resolve_exact_address_geocode(request)
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
            image_url = get_satellite_image_url(geo.latitude, geo.longitude)

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
                        satellite_image_url=image_url,
                        latitude=geo.latitude,
                        longitude=geo.longitude,
                    )
                ],
                count=1,
                search_area=geo.address,
                message="Matched address via Google geocode.",
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
            page_size=40,
        )
        service = AreaMassSearchService()
        ranked, _, _ = service.search_area(area_req)

        results: List[SolarProspect] = []
        for row in ranked:
            if row.estimated_roof_sqm < min_roof:
                continue
            stats = get_solar_stats(row.estimated_roof_sqm, row.business_type, province=request.province or "")
            image_url = get_satellite_image_url(row.lat, row.lng)
            rev = reverse_geocode(row.lat, row.lng) or {}
            results.append(
                SolarProspect(
                    lead_id=row.place_id,
                    address=row.address,
                    suburb=rev.get("suburb"),
                    city=rev.get("city") or request.city,
                    business_name=row.name,
                    building_type=row.business_type,
                    website=row.website,
                    phone=row.phone,
                    email=row.email,
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
                    satellite_image_url=image_url,
                    latitude=row.lat,
                    longitude=row.lng,
                )
            )

        return SearchResponse(
            results=results,
            count=len(results),
            search_area=center_query,
            message=f"Found {len(results)} properties with solar potential in {center_query}",
        )
    except Exception as e:
        logger.error("Search error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/search/mail-pack", response_model=MailPackResponse)
async def generate_mail_pack(request: MailPackRequest) -> MailPackResponse:
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
