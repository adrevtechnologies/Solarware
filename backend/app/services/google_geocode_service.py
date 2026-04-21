"""Google-only geocode helpers."""
import hashlib
import json
import logging
import math
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from pydantic import BaseModel

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class GeoLocation(BaseModel):
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
    bbox: Tuple[float, float, float, float]


def _cache_root() -> Path:
    root = Path(get_settings().OUTPUT_BASE_PATH).resolve() / "cache" / "geocode"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _cache_key(provider: str, query: str) -> str:
    return hashlib.sha256(f"{provider}|{query}".encode("utf-8")).hexdigest()[:32]


def _cache_load(provider: str, query: str, ttl_s: int = 7 * 24 * 3600) -> Optional[Dict]:
    cache_file = _cache_root() / f"{_cache_key(provider, query)}.json"
    if not cache_file.exists():
        return None
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
        if (time.time() - payload.get("ts", 0)) > ttl_s:
            return None
        return payload.get("data")
    except Exception:
        return None


def _cache_save(provider: str, query: str, data: Dict) -> None:
    cache_file = _cache_root() / f"{_cache_key(provider, query)}.json"
    payload = {"ts": time.time(), "data": data}
    cache_file.write_text(json.dumps(payload), encoding="utf-8")


def _api_key() -> str:
    settings = get_settings()
    return settings.GOOGLE_SERVER_KEY or settings.GOOGLE_MAPS_API_KEY


def geocode_address_google(
    address: str,
    city: str = "",
    province: str = "",
    suburb: str = "",
    postcode: str = "",
    country: str = "South Africa",
) -> Optional[GeoLocation]:
    api_key = _api_key()
    if not api_key:
        return None

    parts = [address, suburb, city, province, postcode, country or "South Africa"]
    query = ", ".join([p.strip() for p in parts if p and p.strip()])

    cached = _cache_load("google", query)
    if cached:
        try:
            return GeoLocation(**cached)
        except Exception:
            pass

    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": query, "key": api_key, "region": "za"},
        timeout=10,
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

    parsed = GeoLocation(
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
    _cache_save("google", query, parsed.model_dump())
    return parsed


def reverse_geocode(latitude: float, longitude: float) -> Optional[Dict]:
    api_key = _api_key()
    if not api_key:
        return None

    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"latlng": f"{latitude},{longitude}", "key": api_key, "region": "za"},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "OK" or not payload.get("results"):
        return None

    top = payload["results"][0]
    address_map: Dict[str, str] = {}
    for comp in top.get("address_components", []):
        for comp_type in comp.get("types", []):
            address_map[comp_type] = comp.get("long_name")

    return {
        "address": top.get("formatted_address"),
        "suburb": address_map.get("sublocality") or address_map.get("neighborhood"),
        "city": address_map.get("locality") or address_map.get("administrative_area_level_2"),
        "province": address_map.get("administrative_area_level_1"),
        "country": address_map.get("country"),
        "postcode": address_map.get("postal_code"),
    }


def suggest_areas_google(query: str, city: str = "", province: str = "", country: str = "South Africa", limit: int = 8) -> List[str]:
    api_key = _api_key()
    if not api_key:
        return []

    seed = (query or "").strip() or city or province or country or "South Africa"
    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/autocomplete/json",
        params={
            "input": seed,
            "types": "(regions)",
            "components": "country:za",
            "key": api_key,
            "language": "en",
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") not in {"OK", "ZERO_RESULTS"}:
        return []

    results: List[str] = []
    seen = set()
    city_norm = (city or "").strip().lower()
    province_norm = (province or "").strip().lower()
    for pred in payload.get("predictions", []):
        text = (pred.get("description") or "").strip()
        if not text:
            continue
        parts = [p.strip() for p in text.split(",") if p.strip()]
        area_name = parts[0] if parts else text
        lowered = text.lower()
        if city_norm and city_norm not in lowered:
            continue
        if province_norm and province_norm not in lowered:
            continue
        key = area_name.lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(area_name)
        if len(results) >= max(1, limit):
            break
    return results


def suggest_cities_google(query: str, province: str = "", country: str = "South Africa", limit: int = 8) -> List[str]:
    api_key = _api_key()
    if not api_key:
        return []

    seed = (query or "").strip() or province or country or "South Africa"
    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/autocomplete/json",
        params={
            "input": seed,
            "types": "(cities)",
            "components": "country:za",
            "key": api_key,
            "language": "en",
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") not in {"OK", "ZERO_RESULTS"}:
        return []

    results: List[str] = []
    seen = set()
    province_norm = (province or "").strip().lower()
    for pred in payload.get("predictions", []):
        text = (pred.get("description") or "").strip()
        if not text:
            continue
        parts = [p.strip() for p in text.split(",") if p.strip()]
        city_name = parts[0] if parts else text
        lowered = text.lower()
        if province_norm and province_norm not in lowered:
            continue
        key = city_name.lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(city_name)
        if len(results) >= max(1, limit):
            break
    return results


def get_bounding_box(center_lat: float, center_lng: float, radius_km: float) -> Tuple[float, float, float, float]:
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * max(0.2, math.cos(math.radians(center_lat))))
    return (
        center_lat - lat_delta,
        center_lat + lat_delta,
        center_lng - lng_delta,
        center_lng + lng_delta,
    )
