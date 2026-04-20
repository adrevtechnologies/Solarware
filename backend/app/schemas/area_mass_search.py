from typing import List, Optional

from pydantic import BaseModel, Field


class AreaMassSearchRequest(BaseModel):
    query: Optional[str] = ""
    place_id: Optional[str] = None
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    min_latitude: Optional[float] = None
    max_latitude: Optional[float] = None
    min_longitude: Optional[float] = None
    max_longitude: Optional[float] = None
    radius_m: int = Field(default=1600, ge=300, le=10000)
    tile_size_m: int = Field(default=500, ge=250, le=2000)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    include_types: List[str] = Field(default_factory=lambda: ["store", "point_of_interest"])


class AreaMassSearchResult(BaseModel):
    place_id: str
    name: str
    address: str
    lat: float
    lng: float
    types: List[str]
    business_type: str
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    business_status: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    opening_hours: Optional[List[str]] = None
    estimated_roof_sqm: float
    estimated_annual_savings: float
    lead_score: int
    lead_grade: str


class AreaMassSearchResponse(BaseModel):
    results: List[AreaMassSearchResult]
    count: int
    total: int
    page: int
    page_size: int
    export_csv_url: Optional[str] = None
