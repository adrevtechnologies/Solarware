"""
Search API endpoint for finding solar leads based on location and filters
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import logging
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Prospect, Contact

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


class FilterParams(BaseModel):
    minRoofSize: Optional[int] = None
    maxRoofSize: Optional[int] = None
    businessOnly: Optional[bool] = None
    warehousesOnly: Optional[bool] = None
    schoolsOnly: Optional[bool] = None
    hasContactInfo: Optional[bool] = None
    highSolarScore: Optional[bool] = None


class SearchRequest(BaseModel):
    mode: str  # 'country' | 'province' | 'city' | 'area' | 'address'
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None
    street: Optional[str] = None
    postalCode: Optional[str] = None
    filters: Optional[FilterParams] = None


class ProspectResponse(BaseModel):
    id: str
    address: str
    business_name: Optional[str] = None
    property_type: Optional[str] = None
    roof_size_sqft: int
    solar_score: int
    contact_status: str
    phone: Optional[str] = None
    email: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[ProspectResponse]
    count: int


@router.post("/search")
async def search_prospects(request: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    """
    Search for solar prospects based on location and optional filters.
    
    Search modes:
    - 'country': Search all prospects in a country
    - 'province': Search prospects in a province
    - 'city': Search prospects in a city
    - 'area': Search prospects in an area/suburb
    - 'address': Search for a specific address
    
    Optional filters can be applied to narrow results.
    """
    try:
        query = db.query(Prospect)

        # Location-based search
        if request.mode == 'address' and request.street:
            # Search by exact street address
            query = query.filter(Prospect.address.ilike(f"%{request.street}%"))
        elif request.mode == 'city' and request.city:
            # Search by city name in address
            query = query.filter(Prospect.address.ilike(f"%{request.city}%"))
        elif request.mode == 'area' and request.area:
            # Search by area/suburb name in address
            query = query.filter(Prospect.address.ilike(f"%{request.area}%"))
        # For country and province modes, just return all prospects
        # since the database doesn't have detailed location mappings
        
        # Apply optional filters
        if request.filters:
            if request.filters.minRoofSize:
                query = query.filter(Prospect.roof_area_sqft >= request.filters.minRoofSize)

            if request.filters.maxRoofSize:
                query = query.filter(Prospect.roof_area_sqft <= request.filters.maxRoofSize)

            if request.filters.highSolarScore:
                query = query.filter(Prospect.solar_confidence >= 0.80)

            if request.filters.hasContactInfo:
                # Must have either contact email or contact phone
                prospects_with_contact = db.query(Contact.prospect_id).filter(
                    (Contact.email.isnot(None)) | (Contact.phone.isnot(None))
                ).all()
                contact_ids = [c[0] for c in prospects_with_contact]
                if contact_ids:
                    query = query.filter(Prospect.id.in_(contact_ids))
                else:
                    query = query.filter(False)

            if request.filters.businessOnly:
                query = query.filter(Prospect.business_type.isin(["Commercial", "Industrial", "Retail"]))

            if request.filters.warehousesOnly:
                query = query.filter(Prospect.business_type.ilike("%Warehouse%"))

            if request.filters.schoolsOnly:
                query = query.filter(Prospect.business_type.ilike("%School%"))

        # Order by solar confidence (solar_score) and limit results
        prospects_list = query.order_by(Prospect.solar_confidence.desc()).limit(500).all()

        # Get contact information for all prospects
        prospect_ids = [p.id for p in prospects_list]
        contacts_map = {}
        if prospect_ids:
            contacts = db.query(Contact).filter(Contact.prospect_id.in_(prospect_ids)).all()
            contacts_map = {c.prospect_id: c for c in contacts}

        # Build response with required fields only
        results = []
        for prospect in prospects_list:
            contact = contacts_map.get(prospect.id)
            solar_score = int(round((prospect.solar_confidence or 0.0) * 100))
            
            # Determine contact status
            if contact and (contact.email or contact.phone):
                contact_status = "Verified"
            elif contact:
                contact_status = "Partial"
            else:
                contact_status = "Needs Research"
            
            results.append(
                ProspectResponse(
                    id=str(prospect.id),
                    address=prospect.address,
                    business_name=prospect.business_name,
                    property_type=prospect.business_type,
                    roof_size_sqft=int(prospect.roof_area_sqft),
                    solar_score=solar_score,
                    contact_status=contact_status,
                    phone=contact.phone if contact else None,
                    email=contact.email if contact else None,
                )
            )

        logger.info(f"Search completed: {len(results)} prospects found (mode={request.mode})")
        return SearchResponse(results=results, count=len(results))

    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

