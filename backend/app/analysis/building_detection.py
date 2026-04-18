"""Building detection and analysis."""
from typing import List, Dict, Tuple
from dataclasses import dataclass
import random
from ..core.logging import logger
from ..core.errors import BuildingDetectionError
from ..utils import sqft_to_sqm


@dataclass
class DetectedBuilding:
    """Represents a building detected from satellite imagery."""
    latitude: float
    longitude: float
    roof_area_sqft: float
    confidence: float
    roof_orientation: str  # N, NE, E, SE, S, SW, W, NW
    has_solar_panels: bool = False
    solar_confidence: float = 0.0


class BuildingDetector:
    """Detects buildings from satellite imagery."""

    @staticmethod
    async def detect_buildings(
        satellite_images: List[Dict],
        min_roof_area_sqft: float = 1000.0,
        exclude_solar: bool = True,
    ) -> List[DetectedBuilding]:
        """Detect buildings in satellite images.
        
        Args:
            satellite_images: List of satellite image data
            min_roof_area_sqft: Minimum roof area to include
            exclude_solar: Exclude buildings with existing solar panels
        
        Returns:
            List of DetectedBuilding objects
        
        Raises:
            BuildingDetectionError: If detection fails
        """
        logger.info(f"Starting building detection for {len(satellite_images)} images")
        
        buildings = []
        
        # Mock detection - in production this would use ML model
        for image in satellite_images:
            try:
                # Simulate detection
                detected = BuildingDetector._simulate_detection(min_roof_area_sqft, exclude_solar)
                buildings.extend(detected)
            except Exception as e:
                logger.error(f"Error detecting buildings: {str(e)}")
                raise BuildingDetectionError(f"Building detection failed: {str(e)}")
        
        logger.info(f"Detected {len(buildings)} buildings")
        return buildings

    @staticmethod
    def _simulate_detection(min_roof_area_sqft: float, exclude_solar: bool) -> List[DetectedBuilding]:
        """Simulate building detection for development."""
        buildings = []
        
        # Generate 5-15 mock buildings per image
        count = random.randint(5, 15)
        
        orientations = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        
        for _ in range(count):
            roof_area = random.uniform(max(min_roof_area_sqft, 1000), 50000)
            
            # 10% chance of existing solar panels
            has_solar = random.random() < 0.1 if exclude_solar else False
            
            if has_solar and exclude_solar:
                continue
            
            buildings.append(
                DetectedBuilding(
                    latitude=random.uniform(40.0, 41.0),
                    longitude=random.uniform(-74.0, -73.0),
                    roof_area_sqft=roof_area,
                    confidence=random.uniform(0.75, 0.99),
                    roof_orientation=random.choice(orientations),
                    has_solar_panels=has_solar,
                    solar_confidence=0.85 if has_solar else 0.0,
                )
            )
        
        return buildings

    @staticmethod
    def filter_by_criteria(
        buildings: List[DetectedBuilding],
        min_roof_area_sqft: float,
        exclude_solar: bool = True,
    ) -> List[DetectedBuilding]:
        """Filter buildings by criteria.
        
        Args:
            buildings: List of detected buildings
            min_roof_area_sqft: Minimum roof area
            exclude_solar: Whether to exclude buildings with solar
        
        Returns:
            Filtered list of buildings
        """
        filtered = []
        
        for building in buildings:
            # Check roof area
            if building.roof_area_sqft < min_roof_area_sqft:
                continue
            
            # Check solar panels
            if exclude_solar and building.has_solar_panels:
                logger.debug(f"Excluding building at ({building.latitude}, {building.longitude}) - has solar panels")
                continue
            
            filtered.append(building)
        
        logger.info(f"Filtered {len(buildings)} buildings to {len(filtered)} after criteria application")
        return filtered

    @staticmethod
    def estimate_solar_potential(building: DetectedBuilding, country: str = "US") -> Dict:
        """Estimate solar potential for a building.
        
        Args:
            building: Detected building
            country: Country code for solar calculations
        
        Returns:
            Dictionary with solar potential data
        """
        from app.utils import calculate_solar_analysis, sqft_to_sqm
        
        roof_area_sqm = sqft_to_sqm(building.roof_area_sqft)
        
        analysis = calculate_solar_analysis(
            roof_area_sqft=building.roof_area_sqft,
            roof_area_sqm=roof_area_sqm,
            country=country,
        )
        
        return analysis
