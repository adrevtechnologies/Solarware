"""API routes for prospects."""
import logging
from pathlib import Path
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..analysis.mailing_pack import MailingPackGenerator
from ..analysis.visualization import VizGenerator
from ..core import get_db
from ..core.config import get_settings
from ..models import Contact, Prospect
from ..schemas import ContactResponse, ProspectResponse

router = APIRouter(prefix="/api/prospects", tags=["prospects"])
logger = logging.getLogger(__name__)


def _to_public_output_url(file_path: str | None) -> str | None:
    """Convert local output file path to a public backend URL path."""
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


@router.get("")
def list_prospects(
    search_area_id: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List prospects with lightweight ranking/contact fields for the lead dashboard."""
    try:
        query = db.query(Prospect)

        if search_area_id:
            # search_area_id is now a string, not UUID, so we don't need to convert
            query = query.filter(Prospect.search_area_id == search_area_id)

        prospects = query.offset(skip).limit(limit).all()
    except SQLAlchemyError:
        logger.exception("Prospect query failed")
        return []
    except Exception:
        logger.exception("Unexpected error while loading prospects")
        return []

    prospect_ids = [p.id for p in prospects]
    try:
        contacts = db.query(Contact).filter(Contact.prospect_id.in_(prospect_ids)).all() if prospect_ids else []
    except SQLAlchemyError:
        logger.exception("Contact query failed; returning prospects without contact enrichment")
        contacts = []

    contact_map = {c.prospect_id: c for c in contacts}

    rows = []
    for prospect in prospects:
        try:
            contact = contact_map.get(prospect.id)
            suitability_score = int(round((getattr(prospect, "solar_confidence", 0.0) or 0.0) * 100))
            contact_name = contact.contact_name if contact else None
            has_verified_contact = bool(contact and (contact.email or contact.phone))
            if not has_verified_contact:
                contact_name = "Needs Research"
            rows.append(
                {
                    "id": str(prospect.id),
                    "search_area_id": str(prospect.search_area_id),
                    "latitude": getattr(prospect, "latitude", None),
                    "longitude": getattr(prospect, "longitude", None),
                    "address": getattr(prospect, "address", None),
                    "building_name": getattr(prospect, "building_name", None),
                    "business_name": getattr(prospect, "business_name", None),
                    "business_type": getattr(prospect, "business_type", None),
                    "roof_area_sqft": getattr(prospect, "roof_area_sqft", None),
                    "roof_area_sqm": getattr(prospect, "roof_area_sqm", None),
                    "has_existing_solar": getattr(prospect, "has_existing_solar", False),
                    "estimated_panel_count": getattr(prospect, "estimated_panel_count", None),
                    "estimated_system_capacity_kw": getattr(prospect, "estimated_system_capacity_kw", None),
                    "estimated_annual_production_kwh": getattr(prospect, "estimated_annual_production_kwh", None),
                    "estimated_annual_savings_usd": getattr(prospect, "estimated_annual_savings_usd", None),
                    "annual_savings_rands": getattr(prospect, "annual_savings_rands", None),
                    "solar_confidence": getattr(prospect, "solar_confidence", None),
                    "suitability_score": suitability_score,
                    "contact_name": contact_name,
                    "contact_title": contact.title if contact else None,
                    "contact_email": contact.email if contact else None,
                    "contact_phone": contact.phone if contact else None,
                    "contact_data_complete": contact.data_complete if contact else False,
                    "created_at": getattr(prospect, "created_at", None),
                }
            )
        except Exception:
            logger.exception("Failed to serialize prospect row")
            continue

    try:
        rows.sort(key=lambda item: item["suitability_score"], reverse=True)
    except Exception:
        logger.exception("Failed to sort prospects list")
    return rows


@router.get("/export-csv")
async def export_prospects_csv(db: Session = Depends(get_db)):
    """Export prospects as CSV."""
    import csv
    from io import StringIO

    from fastapi.responses import StreamingResponse

    prospects = db.query(Prospect).all()

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "address",
            "business_name",
            "business_type",
            "roof_area_sqft",
            "system_capacity_kw",
            "suitability_score",
            "created_at",
        ],
    )

    writer.writeheader()
    for prospect in prospects:
        writer.writerow(
            {
                "address": prospect.address,
                "business_name": prospect.business_name,
                "business_type": prospect.business_type,
                "roof_area_sqft": prospect.roof_area_sqft,
                "system_capacity_kw": prospect.estimated_system_capacity_kw,
                "suitability_score": int(round((prospect.solar_confidence or 0.0) * 100)),
                "created_at": prospect.created_at,
            }
        )

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=prospects.csv"},
    )


@router.get("/{prospect_id}", response_model=ProspectResponse)
def get_prospect(prospect_id: str, db: Session = Depends(get_db)):
    """Get a specific prospect."""
    try:
        prospect_uuid = uuid.UUID(prospect_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid prospect ID format") from exc

    prospect = db.query(Prospect).filter(Prospect.id == prospect_uuid).first()

    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    return prospect


@router.get("/{prospect_id}/contact", response_model=ContactResponse)
def get_prospect_contact(prospect_id: str, db: Session = Depends(get_db)):
    """Get contact information for a prospect."""
    try:
        prospect_uuid = uuid.UUID(prospect_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid prospect ID format") from exc

    contact = db.query(Contact).filter(Contact.prospect_id == prospect_uuid).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact information not found")

    return contact


@router.post("/{prospect_id}/proposal")
async def generate_proposal(prospect_id: str, db: Session = Depends(get_db)):
    """Generate proposal assets and outreach copy for one lead."""
    try:
        prospect_uuid = uuid.UUID(prospect_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid prospect ID format") from exc

    prospect = db.query(Prospect).filter(Prospect.id == prospect_uuid).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    contact = db.query(Contact).filter(Contact.prospect_id == prospect_uuid).first()
    suitability_score = int(round((prospect.solar_confidence or 0.0) * 100))

    mockup_path = await VizGenerator.generate_mockup(
        satellite_image_path=prospect.satellite_image_url,
        panel_count=prospect.estimated_panel_count or 0,
        roof_area_sqm=prospect.roof_area_sqm or 0,
        system_capacity_kw=prospect.estimated_system_capacity_kw or 0.0,
    )

    before_after_path = await VizGenerator.generate_before_after(
        before_image_path=prospect.satellite_image_url,
        mockup_image_path=mockup_path,
    )

    pack = MailingPackGenerator.generate(
        prospect={
            "id": prospect.id,
            "address": prospect.address,
            "business_name": prospect.business_name,
            "roof_area_sqft": prospect.roof_area_sqft,
            "roof_area_sqm": prospect.roof_area_sqm,
            "estimated_panel_count": prospect.estimated_panel_count,
            "estimated_system_capacity_kw": prospect.estimated_system_capacity_kw,
            "estimated_annual_production_kwh": prospect.estimated_annual_production_kwh,
            "solar_confidence": prospect.solar_confidence,
        },
        contact={
            "contact_name": contact.contact_name if contact else None,
            "email": contact.email if contact else None,
            "phone": contact.phone if contact else None,
        },
        satellite_image_path=prospect.satellite_image_url,
        mockup_image_path=mockup_path,
    )

    return {
        "prospect_id": str(prospect.id),
        "suitability_score": suitability_score,
        "satellite_image": prospect.satellite_image_url,
        "mockup_image": _to_public_output_url(mockup_path),
        "before_after_image": _to_public_output_url(before_after_path),
        "sales_message": (
            f"{prospect.business_name or 'This site'} has a {suitability_score}/100 rooftop suitability score "
            "and is a strong candidate for a commercial solar discovery call."
        ),
        "outreach": pack.get("outreach", {}),
        "mailing_pack": pack,
    }
