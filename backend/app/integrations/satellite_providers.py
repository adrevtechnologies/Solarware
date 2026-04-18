"""Base classes and interfaces for satellite data providers."""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SatelliteImage:
    """Represents a satellite image."""
    url: str
    date: str
    source: str
    cloud_coverage: float
    resolution_m: float


class SatelliteProvider(ABC):
    """Base class for satellite data providers."""

    @abstractmethod
    async def get_images(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        max_cloud_coverage: float = 20.0,
    ) -> List[SatelliteImage]:
        """Retrieve satellite images for a geographic area.
        
        Args:
            min_lat: Minimum latitude
            max_lat: Maximum latitude
            min_lon: Minimum longitude
            max_lon: Maximum longitude
            max_cloud_coverage: Maximum acceptable cloud coverage percentage
        
        Returns:
            List of SatelliteImage objects
        """
        pass

    @abstractmethod
    async def get_image_url(self, image_id: str) -> Optional[str]:
        """Get URL for a specific image.
        
        Args:
            image_id: Image identifier
        
        Returns:
            URL string or None
        """
        pass


class MockSatelliteProvider(SatelliteProvider):
    """Mock satellite provider for development and testing."""

    async def get_images(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        max_cloud_coverage: float = 20.0,
    ) -> List[SatelliteImage]:
        """Return mock satellite images."""
        return [
            SatelliteImage(
                url="https://api.mapbox.com/styles/v1/mapbox/satellite/static/0,0,12/600x400@2x?access_token=pk.test",
                date="2024-01-15",
                source="mock",
                cloud_coverage=5.0,
                resolution_m=10.0,
            )
        ]

    async def get_image_url(self, image_id: str) -> Optional[str]:
        """Return mock image URL."""
        return "https://api.mapbox.com/styles/v1/mapbox/satellite/static/0,0,12/600x400@2x?access_token=pk.test"


class GoogleStaticMapsProvider(SatelliteProvider):
    """Google Static Maps provider for satellite imagery."""

    async def get_images(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        max_cloud_coverage: float = 20.0,
    ) -> List[SatelliteImage]:
        """Return satellite image from Google Static Maps."""
        # Center of the bounding box
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        # Generate URL - No API key needed for basic functionality
        url = f"https://maps.googleapis.com/maps/api/staticmap?center={center_lat},{center_lon}&zoom=18&size=400x400&maptype=satellite"
        
        return [
            SatelliteImage(
                url=url,
                date="2024-01-15",
                source="google_static_maps",
                cloud_coverage=5.0,
                resolution_m=2.0,
            )
        ]

    async def get_image_url(self, image_id: str) -> Optional[str]:
        """Get image URL."""
        return image_id
        from app.core.logging import logger
        logger.info(f"Retrieving GEE images for bounds: ({min_lat}, {max_lat}, {min_lon}, {max_lon})")
        return []

    async def get_image_url(self, image_id: str) -> Optional[str]:
        return None


class SentinelHubProvider(SatelliteProvider):
    """Sentinel Hub satellite provider."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    async def get_images(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        max_cloud_coverage: float = 20.0,
    ) -> List[SatelliteImage]:
        """Retrieve images from Sentinel Hub."""
        from app.core.logging import logger
        logger.info(f"Retrieving Sentinel images for bounds: ({min_lat}, {max_lat}, {min_lon}, {max_lon})")
        return []

    async def get_image_url(self, image_id: str) -> Optional[str]:
        return None
