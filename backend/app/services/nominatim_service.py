"""
Nominatim Geocoding Service - Real address geocoding using OpenStreetMap data
FREE - NO API KEY REQUIRED
"""
import requests
import logging
import math
from typing import Optional, Dict, Tuple, List
from pydantic import BaseModel
from ..core.config import get_settings

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": "Solarware/1.0"}


class GeoLocation(BaseModel):
    """Geocoding result"""
    latitude: float
    longitude: float
    address: str
    street: Optional[str]
    house_number: Optional[str]
    suburb: Optional[str]
    city: Optional[str]
    province: Optional[str]
    postcode: Optional[str]
    country: str
    bbox: Tuple[float, float, float, float]  # (min_lat, max_lat, min_lon, max_lon)


def geocode_address(
    address: str,
    city: str = "",
    province: str = "",
    suburb: str = "",
    postcode: str = "",
    country: str = "South Africa",
) -> Optional[GeoLocation]:
    """
    Convert address/city/province to coordinates using Nominatim
    RETURNS: GeoLocation with lat/lon/full address
    """
    parts = [address, suburb, city, province, postcode, country or "South Africa"]
    query = ", ".join([p.strip() for p in parts if p and p.strip()])

    try:
        response = requests.get(
            f"{NOMINATIM_URL}/search",
            params={"q": query, "format": "json", "addressdetails": 1},
            headers=HEADERS,
            timeout=5
        )
        response.raise_for_status()
        
        results = response.json()
        if not results:
            logger.warning(f"Geocoding failed for: {query}")
            return None

        top_result = results[0]
        address_details = top_result.get("address", {})

        return GeoLocation(
            latitude=float(top_result["lat"]),
            longitude=float(top_result["lon"]),
            address=top_result.get("display_name", ""),
            street=address_details.get("road") or address_details.get("street"),
            house_number=address_details.get("house_number"),
            suburb=address_details.get("suburb") or address_details.get("neighbourhood"),
            city=address_details.get("city") or address_details.get("town"),
            province=address_details.get("state"),
            postcode=address_details.get("postcode"),
            country=address_details.get("country", "South Africa"),
            bbox=tuple(float(x) for x in top_result["boundingbox"])
        )
    except Exception as e:
        logger.error(f"Nominatim geocoding error for '{query}': {e}")
        return None


def geocode_address_google(
    address: str,
    city: str = "",
    province: str = "",
    suburb: str = "",
    postcode: str = "",
    country: str = "South Africa",
) -> Optional[GeoLocation]:
    """Convert address to coordinates using Google Geocoding when API key is configured."""
    settings = get_settings()
    api_key = settings.GOOGLE_MAPS_API_KEY
    if not api_key:
        return None

    parts = [address, suburb, city, province, postcode, country or "South Africa"]
    query = ", ".join([p.strip() for p in parts if p and p.strip()])

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "address": query,
                "key": api_key,
                "region": "za",
            },
            headers=HEADERS,
            timeout=6,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "OK":
            return None

        result = payload.get("results", [])[0]
        location = result.get("geometry", {}).get("location", {})
        viewport = result.get("geometry", {}).get("viewport", {})

        if "lat" not in location or "lng" not in location:
            return None

        comp_map: Dict[str, str] = {}
        for component in result.get("address_components", []):
            long_name = component.get("long_name")
            for comp_type in component.get("types", []):
                if comp_type and long_name:
                    comp_map[comp_type] = long_name

        if viewport.get("southwest") and viewport.get("northeast"):
            bbox = (
                float(viewport["southwest"].get("lat")),
                float(viewport["northeast"].get("lat")),
                float(viewport["southwest"].get("lng")),
                float(viewport["northeast"].get("lng")),
            )
        else:
            lat = float(location["lat"])
            lon = float(location["lng"])
            bbox = (lat - 0.0005, lat + 0.0005, lon - 0.0005, lon + 0.0005)

        return GeoLocation(
            latitude=float(location["lat"]),
            longitude=float(location["lng"]),
            address=result.get("formatted_address", query),
            street=comp_map.get("route"),
            house_number=comp_map.get("street_number"),
            suburb=comp_map.get("sublocality") or comp_map.get("neighborhood"),
            city=comp_map.get("locality") or comp_map.get("administrative_area_level_2"),
            province=comp_map.get("administrative_area_level_1"),
            postcode=comp_map.get("postal_code"),
            country=comp_map.get("country", country or "South Africa"),
            bbox=bbox,
        )
    except Exception as e:
        logger.warning(f"Google geocoding error for '{query}': {e}")
        return None


def geocode_address_polygon(
    address: str,
    city: str = "",
    province: str = "",
    suburb: str = "",
    postcode: str = "",
    country: str = "South Africa",
) -> Optional[List[Tuple[float, float]]]:
    """Resolve address to a polygon footprint/boundary when available from Nominatim."""
    parts = [address, suburb, city, province, postcode, country or "South Africa"]
    query = ", ".join([p.strip() for p in parts if p and p.strip()])

    try:
        response = requests.get(
            f"{NOMINATIM_URL}/search",
            params={
                "q": query,
                "format": "jsonv2",
                "addressdetails": 1,
                "polygon_geojson": 1,
                "limit": 1,
            },
            headers=HEADERS,
            timeout=8,
        )
        response.raise_for_status()

        results = response.json()
        if not results:
            return None

        geojson = results[0].get("geojson") or {}
        geometry_type = geojson.get("type")
        coords = geojson.get("coordinates")
        if not geometry_type or not coords:
            return None

        ring = None
        if geometry_type == "Polygon":
            ring = coords[0] if coords else None
        elif geometry_type == "MultiPolygon":
            # Choose the longest outer ring as primary footprint.
            rings = [poly[0] for poly in coords if poly and poly[0]]
            if rings:
                ring = sorted(rings, key=len, reverse=True)[0]

        if not ring or len(ring) < 3:
            return None

        polygon = []
        for point in ring:
            if len(point) < 2:
                continue
            lon, lat = point[0], point[1]
            polygon.append((float(lat), float(lon)))

        return polygon if len(polygon) >= 3 else None

    except Exception as e:
        logger.warning(f"Nominatim polygon lookup failed for '{query}': {e}")
        return None


def reverse_geocode(latitude: float, longitude: float) -> Optional[Dict]:
    """
    Convert coordinates to address using Nominatim
    RETURNS: Dict with address components
    """
    try:
        response = requests.get(
            f"{NOMINATIM_URL}/reverse",
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1
            },
            headers=HEADERS,
            timeout=5
        )
        response.raise_for_status()
        
        result = response.json()
        address_details = result.get("address", {})

        return {
            "address": result.get("display_name", ""),
            "street": address_details.get("road") or address_details.get("street"),
            "house_number": address_details.get("house_number"),
            "suburb": address_details.get("suburb") or address_details.get("neighbourhood"),
            "city": address_details.get("city") or address_details.get("town"),
            "province": address_details.get("state"),
            "postcode": address_details.get("postcode"),
        }
    except Exception as e:
        logger.error(f"Reverse geocoding error for ({latitude}, {longitude}): {e}")
        return None


def get_bounding_box(latitude: float, longitude: float, radius_km: float = 1.0) -> Tuple[float, float, float, float]:
    """
    Get bounding box around coordinates for search radius
    RETURNS: (min_lat, max_lat, min_lon, max_lon)
    """
    # 1 degree latitude ≈ 111 km. Longitude shrinks by cos(latitude).
    lat_delta = radius_km / 111.0
    cos_lat = max(0.01, abs(math.cos(math.radians(latitude))))
    lon_delta = radius_km / (111.0 * cos_lat)

    return (
        latitude - lat_delta,
        latitude + lat_delta,
        longitude - lon_delta,
        longitude + lon_delta
    )
