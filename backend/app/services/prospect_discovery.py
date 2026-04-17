"""Main orchestration service."""
from typing import Dict, List
from datetime import datetime
import json
import math
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.logging import logger
from app.core.database import get_db_context
from app.models import SearchArea, Prospect, Contact
from app.integrations.satellite_providers import MockSatelliteProvider
from app.utils import calculate_solar_analysis


PROCESSING_STATUS: Dict[str, Dict] = {}


def get_processing_status(search_area_id: str) -> Dict:
    """Return latest processing status for a search area."""
    return PROCESSING_STATUS.get(search_area_id, {
        "search_area_id": search_area_id,
        "status": "unknown",
        "message": "No processing state found",
    })


class ProspectDiscoveryService:
    """Main service orchestrating prospect discovery and analysis."""

    def __init__(self):
        self.satellite_provider = MockSatelliteProvider()

    @staticmethod
    def _set_status(search_area_id: str, **updates):
        current = PROCESSING_STATUS.get(search_area_id, {"search_area_id": search_area_id})
        current.update(updates)
        PROCESSING_STATUS[search_area_id] = current

    @staticmethod
    def _suitability_score(roof_area_sqft: float, has_existing_solar: bool = False) -> float:
        """Convert roof size to a 0-1 suitability score for lead ranking."""
        if has_existing_solar:
            return 0.15

        # Score from 0.35 to 0.95 based on roof size between 900 and 4500 sqft.
        min_area = 900.0
        max_area = 4500.0
        normalized = (roof_area_sqft - min_area) / (max_area - min_area)
        normalized = max(0.0, min(1.0, normalized))
        return round(0.35 + (normalized * 0.60), 2)

    @staticmethod
    def _business_type_from_area(roof_area_sqft: float) -> str:
        if roof_area_sqft >= 3200:
            return "Warehouse"
        if roof_area_sqft >= 2200:
            return "Retail"
        if roof_area_sqft >= 1500:
            return "Office"
        return "Clinic"

    async def process_search_area(
        self,
        search_area_id: str,
        generate_visualizations: bool = True,
        enrich_contacts: bool = True,
        generate_packs: bool = True,
    ) -> Dict:
        """Process a search area end-to-end.
        
        Args:
            search_area_id: UUID of search area
            generate_visualizations: Whether to generate solar mockups
            enrich_contacts: Whether to enrich contact data
            generate_packs: Whether to generate mailing packs
        
        Returns:
            Processing result summary
        """
        logger.info(f"Starting processing for search area: {search_area_id}")
        
        result = {
            "search_area_id": search_area_id,
            "started_at": datetime.utcnow().isoformat(),
            "prospects_discovered": 0,
            "prospects_analyzed": 0,
            "contacts_enriched": 0,
            "visualizations_generated": 0,
            "mailing_packs_generated": 0,
            "status": "processing",
            "errors": [],
        }
        self._set_status(
            search_area_id,
            **{k: v for k, v in result.items() if k != "search_area_id"},
        )
        
        try:
            # Retrieve search area config
            with get_db_context() as db:
                search_area = db.query(SearchArea).filter(SearchArea.id == search_area_id).first()
                if not search_area:
                    raise ValueError(f"Search area not found: {search_area_id}")

                discovered = self._create_osm_prospects(db, search_area, search_area_id)
                result["prospects_discovered"] = discovered
                result["prospects_analyzed"] = discovered
                result["status"] = "completed"
                result["completed_at"] = datetime.utcnow().isoformat()
                self._set_status(
                    search_area_id,
                    **{k: v for k, v in result.items() if k != "search_area_id"},
                )
                
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}", exc_info=e)
            result["status"] = "failed"
            result["errors"].append(str(e))
            result["completed_at"] = datetime.utcnow().isoformat()
            self._set_status(
                search_area_id,
                **{k: v for k, v in result.items() if k != "search_area_id"},
            )
        
        logger.info(f"Processing completed for search area: {search_area_id}")
        return result

    @staticmethod
    def _polygon_area_sqm(geometry: List[Dict]) -> float:
        """Approximate polygon area in square meters from lat/lon points."""
        if len(geometry) < 3:
            return 0.0

        lat0 = sum(p["lat"] for p in geometry) / len(geometry)
        scale_x = 111320.0 * math.cos(math.radians(lat0))
        scale_y = 110540.0

        points = [(p["lon"] * scale_x, p["lat"] * scale_y) for p in geometry]
        area = 0.0
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]
            area += (x1 * y2) - (x2 * y1)
        return abs(area) / 2.0

    @staticmethod
    def _build_address(tags: Dict, lat: float, lon: float) -> str:
        house = tags.get("addr:housenumber")
        street = tags.get("addr:street")
        city = tags.get("addr:city") or tags.get("addr:suburb") or tags.get("addr:town")
        name = tags.get("name")

        if house and street:
            parts = [f"{house} {street}"]
            if city:
                parts.append(city)
            return ", ".join(parts)
        if name:
            return name
        return f"Building near {lat:.5f}, {lon:.5f}"

    def _fetch_osm_buildings(self, search_area) -> List[Dict]:
        """Fetch building footprints from OSM Overpass API for a bbox."""
        bbox = (
            f"{search_area.min_latitude},"
            f"{search_area.min_longitude},"
            f"{search_area.max_latitude},"
            f"{search_area.max_longitude}"
        )
        query = (
            "[out:json][timeout:30];"
            f"way[\"building\"]({bbox});"
            "out geom tags;"
        )

        body = urlencode({"data": query}).encode("utf-8")
        req = Request(
            "https://overpass-api.de/api/interpreter",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(req, timeout=35) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload.get("elements", [])

    def _create_osm_prospects(self, db, search_area, search_area_id: str) -> int:
        """Create prospects from real OSM buildings in the selected search area."""
        created = 0
        min_area_sqft = float(search_area.min_roof_area_sqft)

        try:
            from geoalchemy2.types import WKTElement

            buildings = self._fetch_osm_buildings(search_area)
            for building in buildings:
                geometry = building.get("geometry") or []
                if len(geometry) < 3:
                    continue

                area_sqm = self._polygon_area_sqm(geometry)
                area_sqft = area_sqm * 10.764
                if area_sqft < min_area_sqft:
                    continue

                centroid_lat = sum(p["lat"] for p in geometry) / len(geometry)
                centroid_lon = sum(p["lon"] for p in geometry) / len(geometry)
                tags = building.get("tags") or {}
                address = self._build_address(tags, centroid_lat, centroid_lon)

                existing = db.query(Prospect).filter(
                    Prospect.address == address,
                    Prospect.search_area_id == search_area_id,
                ).first()
                if existing:
                    continue

                solar = calculate_solar_analysis(
                    roof_area_sqft=area_sqft,
                    roof_area_sqm=area_sqm,
                    country=search_area.country,
                    region=search_area.region,
                    include_costs=False,
                )
                suitability = self._suitability_score(area_sqft, has_existing_solar=False)
                business_type = tags.get("building") or self._business_type_from_area(area_sqft)

                point = WKTElement(f"POINT({centroid_lon} {centroid_lat})", srid=4326)
                prospect = Prospect(
                    search_area_id=search_area_id,
                    latitude=centroid_lat,
                    longitude=centroid_lon,
                    geometry=point,
                    address=address,
                    business_name=tags.get("name") or None,
                    business_type=str(business_type).title(),
                    roof_area_sqft=round(area_sqft, 2),
                    roof_area_sqm=round(area_sqm, 2),
                    estimated_panel_count=solar.get("panel_count"),
                    estimated_system_capacity_kw=solar.get("system_capacity_kw"),
                    estimated_annual_production_kwh=None,
                    estimated_annual_savings_usd=None,
                    annual_savings_rands=None,
                    solar_confidence=suitability,
                    local_electricity_rate_per_kwh=2.50,
                )
                db.add(prospect)
                db.flush()

                # Keep contact explicit when no verified source data exists.
                db.add(
                    Contact(
                        prospect_id=prospect.id,
                        contact_name="Needs Research",
                        title=None,
                        email=None,
                        phone=None,
                        data_complete=False,
                        data_source="unverified",
                        confidence_score=0.0,
                    )
                )
                created += 1

            db.commit()
            logger.info(f"Created {created} OSM-based prospects")
            return created
        except Exception as e:
            logger.error(f"Error creating OSM prospects: {str(e)}")
            db.rollback()
            raise
