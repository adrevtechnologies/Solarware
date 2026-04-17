"""Pydantic schemas for request/response validation."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
import uuid


# Search Area Schemas
class SearchAreaCreate(BaseModel):
    """Schema for creating a new search area."""
    name: str
    country: str
    region: Optional[str] = None
    
    # Address fields (for user-friendly interface)
    street: Optional[str] = None
    area: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    
    # Legacy coordinate-based (still supported)
    min_latitude: Optional[float] = None
    max_latitude: Optional[float] = None
    min_longitude: Optional[float] = None
    max_longitude: Optional[float] = None
    
    min_roof_area_sqft: float = 5000

    @field_validator("min_roof_area_sqft")
    @classmethod
    def validate_roof_area(cls, v):
        if v < 100:
            raise ValueError("Minimum roof area must be at least 100 sqft")
        return v

    @field_validator("min_latitude", "max_latitude", mode="before")
    @classmethod
    def validate_latitude(cls, v):
        if v is not None and not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("min_longitude", "max_longitude", mode="before")
    @classmethod
    def validate_longitude(cls, v):
        if v is not None and not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class SearchAreaResponse(SearchAreaCreate):
    """Schema for search area response."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Prospect Schemas
class ProspectCreate(BaseModel):
    """Schema for creating a prospect."""
    search_area_id: uuid.UUID
    latitude: float
    longitude: float
    address: str
    roof_area_sqft: float
    roof_area_sqm: float


class ProspectResponse(BaseModel):
    """Schema for prospect response."""
    id: uuid.UUID
    search_area_id: uuid.UUID
    latitude: float
    longitude: float
    address: str
    building_name: Optional[str]
    business_name: Optional[str]
    business_type: Optional[str]
    roof_area_sqft: float
    roof_area_sqm: float
    has_existing_solar: bool
    estimated_panel_count: Optional[int]
    estimated_system_capacity_kw: Optional[float]
    estimated_annual_production_kwh: Optional[float]
    estimated_annual_savings_usd: Optional[float]
    annual_savings_rands: Optional[float] = None  # Alias for regional currency
    
    # Cost breakdown
    panel_cost: Optional[float] = None
    inverter_cost: Optional[float] = None
    battery_cost: Optional[float] = None
    cable_cost: Optional[float] = None
    installation_labor: Optional[float] = None
    soft_costs: Optional[float] = None
    total_bos_cost: Optional[float] = None
    
    # Installation timeline
    installation_calendar_days: Optional[float] = None
    installation_team_size: Optional[int] = None
    installation_casual_workers: Optional[int] = None
    
    # ROI metrics
    roi_simple_payback_years: Optional[float] = None
    roi_npv_25_years: Optional[float] = None
    roi_cumulative_savings_25_years: Optional[float] = None
    roi_percentage: Optional[float] = None
    
    # Layout efficiency
    strings: Optional[int] = None
    rows: Optional[int] = None
    layout_efficiency: Optional[float] = None
    
    satellite_image_url: Optional[str]
    satellite_source: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Contact Schemas
class ContactCreate(BaseModel):
    """Schema for creating a contact."""
    prospect_id: uuid.UUID
    contact_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class ContactResponse(ContactCreate):
    """Schema for contact response."""
    id: uuid.UUID
    data_complete: bool
    data_source: Optional[str]
    confidence_score: Optional[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Mailing Pack Schemas
class MailingPackCreate(BaseModel):
    """Schema for creating a mailing pack."""
    prospect_id: uuid.UUID
    email_subject: str
    email_body: str
    satellite_image_path: Optional[str] = None
    mockup_image_path: Optional[str] = None


class MailingPackResponse(BaseModel):
    """Schema for mailing pack response."""
    id: uuid.UUID
    prospect_id: uuid.UUID
    email_subject: str
    email_body: str
    satellite_image_path: Optional[str]
    mockup_image_path: Optional[str]
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]
    sent_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Processing request schemas
class ProcessSearchAreaRequest(BaseModel):
    """Request to process a search area for prospects."""
    search_area_id: uuid.UUID
    include_satellite_images: bool = True
    generate_visualizations: bool = True
    enrich_contacts: bool = True


class BatchProcessRequest(BaseModel):
    """Request to process multiple search areas."""
    search_area_ids: List[uuid.UUID]
    config: Optional[dict] = None


# Email sending schemas
class EmailSendRequest(BaseModel):
    """Request to send email for a mailing pack."""
    mailing_pack_id: uuid.UUID
    recipient_email: str
    via: str = "smtp"  # 'smtp', 'sendgrid', 'aws_ses'


class BulkEmailSendRequest(BaseModel):
    """Request to send emails for multiple mailing packs."""
    mailing_pack_ids: List[uuid.UUID]
    via: str = "smtp"
    dry_run: bool = True  # If true, prepare but don't send


# Analysis result schemas
class SolarAnalysisResult(BaseModel):
    """Result from solar analysis."""
    prospect_id: uuid.UUID
    panel_count: int
    system_capacity_kw: float
    annual_production_kwh: float
    annual_savings_usd: float
    confidence_score: float


class ProspectExportRow(BaseModel):
    """CSV export row for prospects."""
    address: str
    business_name: Optional[str]
    roof_area_sqft: float
    estimated_system_capacity_kw: Optional[float]
    estimated_annual_savings_usd: Optional[float]
    contact_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    data_complete: bool
    created_at: datetime
