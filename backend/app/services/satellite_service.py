"""
Satellite Imagery Service
Fetches top-down satellite images using Google Static Maps
FREE tier available (no key required for basic requests)
"""
import logging
from typing import Optional, Tuple
import base64
import io

logger = logging.getLogger(__name__)


def get_satellite_image_url(latitude: float, longitude: float, width: int = 400, height: int = 400) -> str:
    """
    Get satellite image URL from Google Static Maps
    
    Free tier: 25,000 map images per day
    
    RETURNS: URL to satellite image (top-down view of building)
    """
    zoom = 18  # Street level detail
    
    url = (
        f"https://maps.googleapis.com/maps/api/staticmap?"
        f"center={latitude},{longitude}"
        f"&zoom={zoom}"
        f"&size={width}x{height}"
        f"&maptype=satellite"
        f"&style=feature:all|element:labels|visibility:off"
    )
    
    return url


def get_mapbox_satellite_url(latitude: float, longitude: float, width: int = 400, height: int = 400, access_token: Optional[str] = None) -> Optional[str]:
    """
    Alternative: Mapbox satellite imagery
    Requires free Mapbox account but very clean imagery
    """
    if not access_token:
        logger.debug("Mapbox access token not configured")
        return None

    zoom = 18
    url = (
        f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/"
        f"{longitude},{latitude},{zoom},"
        f"0,60/"
        f"{width}x{height}"
        f"?access_token={access_token}"
    )

    return url


def draw_panel_overlay(
    image_url: str,
    capacity_kw: float,
    building_type: str,
) -> str:
    """
    Add solar panel rectangle overlay to satellite image
    
    Simplified visualization:
    - Panel dimensions: 1.7m x 1.0m
    - Rows aligned to typical roof direction
    - Based on building type (warehouse = straight lines, retail = scattered)
    
    For MVP: Just return image URL and render overlay on frontend with canvas
    TODO: Implement backend image manipulation with Pillow if needed
    """
    # For now, return raw image URL
    # Frontend will add canvas overlay with rectangles
    return image_url


def test_satellite_url(latitude: float, longitude: float) -> bool:
    """Test if satellite image URL is accessible"""
    import requests
    try:
        url = get_satellite_image_url(latitude, longitude)
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False
