"""Database models for Solarware application."""
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text, JSON, Enum
import uuid

from ..core.database import Base


class SearchArea(Base):
    """Represents a geographic search area."""
    __tablename__ = "search_areas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    region = Column(String(255), nullable=True)
    
    # Geographic bounds
    min_latitude = Column(Float, nullable=False)
    max_latitude = Column(Float, nullable=False)
    min_longitude = Column(Float, nullable=False)
    max_longitude = Column(Float, nullable=False)
    
    # Filtering criteria
    min_roof_area_sqft = Column(Float, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Prospect(Base):
    """Represents a prospect building identified for solar installation."""
    __tablename__ = "prospects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    search_area_id = Column(String(36), nullable=False)
    
    # Geographic location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geometry_wkt = Column(Text, nullable=False)  # WKT format for compatibility with SQLite
    
    # Building information
    address = Column(String(255), nullable=False)
    building_name = Column(String(255), nullable=True)
    business_name = Column(String(255), nullable=True)
    business_type = Column(String(100), nullable=True)
    
    # Roof analysis
    roof_area_sqft = Column(Float, nullable=False)
    roof_area_sqm = Column(Float, nullable=False)
    roof_orientation = Column(String(100), nullable=True)  # N, NE, E, SE, S, SW, W, NW
    estimated_tilt = Column(Float, nullable=True)
    has_existing_solar = Column(Boolean, nullable=False, default=False)
    solar_confidence = Column(Float, nullable=True)  # 0-1 confidence score
    
    # Satellite data
    satellite_image_url = Column(String(500), nullable=True)  # Before image
    satellite_image_date = Column(DateTime, nullable=True)
    satellite_source = Column(String(50), nullable=True)  # 'google_earth_engine', 'sentinel', etc.
    mockup_image_url = Column(String(500), nullable=True)  # After/solar mockup image
    
    # Solar analysis - System design
    estimated_panel_count = Column(Integer, nullable=True)
    estimated_system_capacity_kw = Column(Float, nullable=True)
    estimated_annual_production_kwh = Column(Float, nullable=True)
    layout_efficiency = Column(Float, nullable=True)  # Percentage 0-100
    
    # Solar analysis - Financial
    estimated_annual_savings_usd = Column(Float, nullable=True)
    estimated_annual_savings_local = Column(Float, nullable=True)  # Regional currency
    annual_savings_rands = Column(Float, nullable=True)  # ZAR equivalent
    local_electricity_rate_per_kwh = Column(Float, nullable=True)
    
    # Cost breakdown
    total_bos_cost = Column(Float, nullable=True)  # Balance of System cost
    panel_cost = Column(Float, nullable=True)
    inverter_cost = Column(Float, nullable=True)
    battery_cost = Column(Float, nullable=True)
    installation_cost = Column(Float, nullable=True)
    soft_costs = Column(Float, nullable=True)
    
    # ROI and payback
    roi_simple_payback_years = Column(Float, nullable=True)
    roi_percentage_20yr = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Contact(Base):
    """Contact information for prospects."""
    __tablename__ = "contacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String(36), nullable=False)
    
    # Contact details
    contact_name = Column(String(255), nullable=True)
    title = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Data quality
    data_complete = Column(Boolean, nullable=False, default=False)
    data_source = Column(String(100), nullable=True)  # 'google_maps', 'web_search', 'manual', etc.
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class MailingPack(Base):
    """Generated mailing pack for a prospect."""
    __tablename__ = "mailing_packs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String(36), nullable=False)
    
    # Content
    email_subject = Column(String(255), nullable=False)
    email_body = Column(Text, nullable=False)
    satellite_image_path = Column(String(500), nullable=True)
    mockup_image_path = Column(String(500), nullable=True)
    report_pdf_path = Column(String(500), nullable=True)
    
    # Status tracking
    status = Column(String(50), nullable=False, default="prepared")  # prepared, reviewed, sent, failed
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    sent_via = Column(String(50), nullable=True)  # 'smtp', 'sendgrid', 'aws_ses'
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SolarAnalysisLog(Base):
    """Logging for solar analysis operations."""
    __tablename__ = "solar_analysis_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(String(36), nullable=False)
    
    operation = Column(String(100), nullable=False)  # 'detection', 'analysis', 'visualization'
    status = Column(String(50), nullable=False)  # 'success', 'failed'
    message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
