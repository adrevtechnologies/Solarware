"""Satellite imagery service with polygon-aware framing for roof visibility."""
import logging
import math
import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Tuple, List
from ..core.config import get_settings

logger = logging.getLogger(__name__)


def _image_cache_file() -> Path:
    file_path = Path(get_settings().OUTPUT_BASE_PATH).resolve() / "cache" / "images" / "url_cache.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        file_path.write_text("{}", encoding="utf-8")
    return file_path


def _image_cache_get(key: str, ttl_s: int = 7 * 24 * 3600) -> Optional[str]:
    try:
        payload = json.loads(_image_cache_file().read_text(encoding="utf-8"))
        row = payload.get(key)
        if not row:
            return None
        if (time.time() - row.get("ts", 0)) > ttl_s:
            return None
        return row.get("url")
    except Exception:
        return None


def _image_cache_set(key: str, url: str) -> str:
    try:
        cache_file = _image_cache_file()
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
        payload[key] = {"ts": time.time(), "url": url}
        cache_file.write_text(json.dumps(payload), encoding="utf-8")
    except Exception:
        pass
    return url


def _url_key(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _bbox_from_polygon(nodes: List[Tuple[float, float]], padding_ratio: float = 0.10) -> Tuple[float, float, float, float]:
    lats = [n[0] for n in nodes]
    lons = [n[1] for n in nodes]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon

    pad_lat = lat_span * padding_ratio if lat_span > 0 else 0.00012
    pad_lon = lon_span * padding_ratio if lon_span > 0 else 0.00012

    return (min_lat - pad_lat, max_lat + pad_lat, min_lon - pad_lon, max_lon + pad_lon)


def _centroid_from_polygon(nodes: List[Tuple[float, float]]) -> Tuple[float, float]:
    if not nodes:
        raise ValueError("Polygon nodes are required")
    lat = sum(n[0] for n in nodes) / len(nodes)
    lon = sum(n[1] for n in nodes) / len(nodes)
    return lat, lon


def get_padded_bbox_for_polygon(
    nodes: List[Tuple[float, float]],
    padding_ratio: float = 0.10,
) -> Tuple[float, float, float, float]:
    """Public helper used by visualization to map geo polygon into returned image frame."""
    return _bbox_from_polygon(nodes, padding_ratio=padding_ratio)


def _choose_image_size(min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> Tuple[int, int]:
    avg_lat = (min_lat + max_lat) / 2.0
    lat_m = (max_lat - min_lat) * 111320.0
    lon_m = (max_lon - min_lon) * 111320.0 * max(0.2, math.cos(math.radians(avg_lat)))
    ratio = lon_m / max(1.0, lat_m)

    if ratio >= 1.8:
        # Wide roof
        return (640, 360)
    if ratio <= 0.65:
        # Long footprint, use custom wide frame to keep full parcel in view
        return (640, 320)
    # Square-ish footprint
    return (512, 512)


def get_satellite_image_url_for_bbox(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    width: int = 640,
    height: int = 640,
) -> str:
    settings = get_settings()
    google_api_key = settings.GOOGLE_SERVER_KEY or settings.GOOGLE_MAPS_API_KEY

    cache_key = _url_key(
        "bbox",
        f"{min_lat:.7f}",
        f"{max_lat:.7f}",
        f"{min_lon:.7f}",
        f"{max_lon:.7f}",
        str(width),
        str(height),
        "google" if bool(google_api_key) else "arcgis",
    )
    cached = _image_cache_get(cache_key)
    if cached:
        return cached

    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2

    if google_api_key:
        visible = f"{min_lat},{min_lon}|{max_lat},{max_lon}"
        url = (
            f"https://maps.googleapis.com/maps/api/staticmap?"
            f"center={center_lat},{center_lon}"
            f"&visible={visible}"
            f"&size={width}x{height}"
            f"&scale=2"
            f"&maptype=satellite"
            f"&style=feature:all|element:labels|visibility:off"
            f"&key={google_api_key}"
        )
        return _image_cache_set(cache_key, url)

    url = (
        "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?"
        f"bbox={min_lon},{min_lat},{max_lon},{max_lat}"
        "&bboxSR=4326"
        f"&size={width},{height}"
        "&imageSR=4326"
        "&format=jpg"
        "&f=image"
    )
    return _image_cache_set(cache_key, url)


def get_satellite_image_url_for_polygon(
    nodes: List[Tuple[float, float]],
    width: int = 0,
    height: int = 0,
    padding_ratio: float = 0.10,
) -> str:
    if not nodes:
        raise ValueError("Polygon nodes are required for polygon imagery")
    min_lat, max_lat, min_lon, max_lon = _bbox_from_polygon(nodes, padding_ratio=padding_ratio)
    if width <= 0 or height <= 0:
        width, height = _choose_image_size(min_lat, max_lat, min_lon, max_lon)

    return get_satellite_image_url_for_bbox(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        width=width,
        height=height,
    )


def get_satellite_image_url(latitude: float, longitude: float, width: int = 640, height: int = 640) -> str:
    """
    Get satellite image URL from Google Static Maps
    
    Free tier: 25,000 map images per day
    
    RETURNS: URL to satellite image (top-down view of building)
    """
    settings = get_settings()
    google_api_key = settings.GOOGLE_SERVER_KEY or settings.GOOGLE_MAPS_API_KEY

    cache_key = _url_key(
        "point",
        f"{latitude:.7f}",
        f"{longitude:.7f}",
        str(width),
        str(height),
        "google" if bool(google_api_key) else "arcgis",
    )
    cached = _image_cache_get(cache_key)
    if cached:
        return cached

    if google_api_key:
        zoom = 21
        url = (
            f"https://maps.googleapis.com/maps/api/staticmap?"
            f"center={latitude},{longitude}"
            f"&zoom={zoom}"
            f"&size={width}x{height}"
            f"&maptype=satellite"
            f"&style=feature:all|element:labels|visibility:off"
            f"&key={google_api_key}"
        )
        return _image_cache_set(cache_key, url)

    # No-key fallback using ArcGIS World Imagery export endpoint.
    lat_delta = 0.0012
    lon_delta = 0.0012
    min_lon = longitude - lon_delta
    min_lat = latitude - lat_delta
    max_lon = longitude + lon_delta
    max_lat = latitude + lat_delta

    url = (
        "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?"
        f"bbox={min_lon},{min_lat},{max_lon},{max_lat}"
        "&bboxSR=4326"
        f"&size={width},{height}"
        "&imageSR=4326"
        "&format=jpg"
        "&f=image"
    )
    return _image_cache_set(cache_key, url)


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

