"""Area mass search service with tiling, dedupe, scoring, and export support."""
import csv
import hashlib
import json
import logging
import math
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import get_settings
from ..integrations.google_places import GooglePlacesClient
from ..schemas.area_mass_search import AreaMassSearchRequest, AreaMassSearchResult
from ..services.google_geocode_service import geocode_address_google
from ..services.solar_calculations import get_solar_stats


logger = logging.getLogger(__name__)


class AreaMassSearchService:
    def __init__(self):
        settings = get_settings()
        key = settings.GOOGLE_SERVER_KEY or settings.GOOGLE_MAPS_API_KEY
        self.places = GooglePlacesClient(key)
        self.cache_root = Path(settings.OUTPUT_BASE_PATH) / "cache" / "area_mass"
        self.export_root = Path(settings.OUTPUT_BASE_PATH) / "cache" / "exports"
        self.cache_root.mkdir(parents=True, exist_ok=True)
        self.export_root.mkdir(parents=True, exist_ok=True)

    def _meters_to_lat(self, meters: float) -> float:
        return meters / 111320.0

    def _meters_to_lng(self, meters: float, lat: float) -> float:
        denom = 40075000 * max(0.2, math.cos(math.radians(lat))) / 360
        return meters / denom

    def _grade(self, score: int) -> str:
        if score >= 88:
            return "A+ HOT LEAD"
        if score >= 76:
            return "A GOOD LEAD"
        if score >= 60:
            return "B MEDIUM"
        return "C LOW"

    def _estimate_roof_sqm(self, types: List[str], name: Optional[str], user_ratings_total: Optional[int]) -> float:
        t = set(types or [])
        label = (name or "").lower()

        if {"shopping_mall", "supermarket", "department_store"}.intersection(t):
            return 2400.0
        if {"warehouse", "industrial", "factory"}.intersection(t):
            return 1800.0
        if {"school", "university", "hospital"}.intersection(t):
            return 1200.0
        if {"store", "point_of_interest"}.intersection(t):
            # Popular destinations likely have larger rooftops.
            if (user_ratings_total or 0) > 200:
                return 900.0
            if "center" in label or "centre" in label:
                return 1100.0
            return 650.0
        return 500.0

    def _estimate_savings(self, roof_sqm: float, types: List[str]) -> float:
        # Reuse the same modeled solar economics path as main search flow.
        building_type = "commercial"
        t = set(types)
        if "industrial" in t or "warehouse" in t or "factory" in t:
            building_type = "industrial"
        elif "office" in t:
            building_type = "office"
        elif "school" in t or "university" in t:
            building_type = "school"
        elif "hospital" in t:
            building_type = "hospital"
        elif "supermarket" in t or "store" in t or "shopping_mall" in t:
            building_type = "retail"

        stats = get_solar_stats(roof_sqm, building_type)
        return float(stats.get("savings_mid", 0.0))

    def _score(self, roof_sqm: float, types: List[str], rating: Optional[float], open_now_like: bool) -> int:
        score = 0

        # Large roof
        if roof_sqm >= 2500:
            score += 35
        elif roof_sqm >= 1200:
            score += 26
        elif roof_sqm >= 700:
            score += 18
        else:
            score += 10

        # Business type and electricity profile
        t = set(types)
        if {"industrial", "warehouse", "supermarket", "shopping_mall"}.intersection(t):
            score += 28
        elif {"store", "office", "school", "hospital", "restaurant"}.intersection(t):
            score += 18
        else:
            score += 8

        # Weekday/open likelihood
        score += 10 if open_now_like else 6

        # Quality signal
        if rating is not None:
            score += 10 if rating >= 4.2 else 7 if rating >= 3.7 else 4
        else:
            score += 5

        # Orientation proxy reserved budget
        score += 12

        return max(0, min(100, score))

    def _resolve_bounds(self, request: AreaMassSearchRequest) -> Tuple[float, float, float, float]:
        if (
            request.min_latitude is not None
            and request.max_latitude is not None
            and request.min_longitude is not None
            and request.max_longitude is not None
        ):
            return (
                request.min_latitude,
                request.max_latitude,
                request.min_longitude,
                request.max_longitude,
            )

        if request.center_lat is not None and request.center_lng is not None:
            lat_delta = self._meters_to_lat(request.radius_m)
            lng_delta = self._meters_to_lng(request.radius_m, request.center_lat)
            return (
                request.center_lat - lat_delta,
                request.center_lat + lat_delta,
                request.center_lng - lng_delta,
                request.center_lng + lng_delta,
            )

        if request.query and request.query.strip():
            geo = geocode_address_google(request.query.strip(), country="South Africa")
            if geo:
                return geo.bbox

        raise ValueError("Unable to resolve bounds. Provide bbox, center, or a geocodable query.")

    def tile_bounds(self, bounds: Tuple[float, float, float, float], tile_size_m: int) -> List[Dict[str, float]]:
        min_lat, max_lat, min_lng, max_lng = bounds
        lat_step = self._meters_to_lat(tile_size_m)
        lng_step = self._meters_to_lng(tile_size_m, (min_lat + max_lat) / 2)

        tiles: List[Dict[str, float]] = []
        lat = min_lat
        while lat < max_lat:
            lng = min_lng
            while lng < max_lng:
                center_lat = min(lat + lat_step / 2, max_lat)
                center_lng = min(lng + lng_step / 2, max_lng)
                tiles.append({"lat": center_lat, "lng": center_lng})
                lng += lng_step
            lat += lat_step
        return tiles

    def _cache_key(self, request: AreaMassSearchRequest, bounds: Tuple[float, float, float, float]) -> str:
        payload = {
            "query": (request.query or "").strip().lower(),
            "place_id": request.place_id,
            "bounds": [round(x, 6) for x in bounds],
            "radius_m": request.radius_m,
            "tile_size_m": request.tile_size_m,
            "include_types": sorted(request.include_types),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]

    def _cache_path(self, key: str) -> Path:
        return self.cache_root / f"area_{key}.json"

    def _load_cached(self, key: str) -> Optional[List[Dict[str, Any]]]:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload.get("results", [])
        except Exception:
            return None

    def _save_cached(self, key: str, rows: List[Dict[str, Any]]) -> None:
        path = self._cache_path(key)
        path.write_text(json.dumps({"results": rows}, indent=2), encoding="utf-8")

    def _export_csv(self, rows: List[AreaMassSearchResult], key: str) -> str:
        export_path = self.export_root / f"area_leads_{key}.csv"
        with export_path.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(
                [
                    "place_id",
                    "name",
                    "address",
                    "lat",
                    "lng",
                    "business_type",
                    "rating",
                    "user_ratings_total",
                    "website",
                    "email",
                    "phone",
                    "estimated_roof_sqm",
                    "estimated_annual_savings",
                    "lead_score",
                    "lead_grade",
                ]
            )
            for r in rows:
                writer.writerow(
                    [
                        r.place_id,
                        r.name,
                        r.address,
                        r.lat,
                        r.lng,
                        r.business_type,
                        r.rating,
                        r.user_ratings_total,
                        r.website,
                        r.email,
                        r.phone,
                        r.estimated_roof_sqm,
                        r.estimated_annual_savings,
                        r.lead_score,
                        r.lead_grade,
                    ]
                )
        return f"/output/cache/exports/{export_path.name}"

    def search_area(self, request: AreaMassSearchRequest) -> Tuple[List[AreaMassSearchResult], int, str]:
        started = time.time()
        max_duration_s = 22.0
        max_tiles = 64
        max_candidates = 260
        max_enriched = max(request.page_size * 4, 120)

        bounds = self._resolve_bounds(request)
        cache_key = self._cache_key(request, bounds)

        cached_rows = self._load_cached(cache_key)
        if cached_rows is not None:
            parsed_cached = [AreaMassSearchResult(**row) for row in cached_rows]
            logger.info("Area mass cache hit: key=%s rows=%s", cache_key, len(parsed_cached))
            return parsed_cached, len(parsed_cached), self._export_csv(parsed_cached, cache_key)

        tiles = self.tile_bounds(bounds, request.tile_size_m)
        if len(tiles) > max_tiles:
            logger.info("Area mass tile cap applied: %s -> %s", len(tiles), max_tiles)
            tiles = tiles[:max_tiles]

        radius = max(200, int(request.tile_size_m // 2))

        # Multiple query paths to increase recall per tile.
        keywords = [k for k in [(request.query or "").strip(), "industrial", "warehouse", "commercial"] if k]

        dedupe: Dict[str, Dict[str, Any]] = {}
        for tile in tiles:
            if (time.time() - started) > max_duration_s:
                logger.warning("Area mass stopped at tile loop due to time budget")
                break
            for keyword in keywords:
                if (time.time() - started) > max_duration_s:
                    logger.warning("Area mass stopped at keyword loop due to time budget")
                    break
                tile_results = self.places.search_nearby(
                    lat=tile["lat"],
                    lng=tile["lng"],
                    radius=radius,
                    keyword=keyword,
                    max_pages=2,
                )
                for row in tile_results:
                    pid = row.get("place_id")
                    if not pid:
                        continue
                    if pid not in dedupe:
                        dedupe[pid] = row
                        if len(dedupe) >= max_candidates:
                            logger.info("Area mass candidate cap reached: %s", max_candidates)
                            break
                if len(dedupe) >= max_candidates:
                    break
            if len(dedupe) >= max_candidates:
                break

        enriched: List[AreaMassSearchResult] = []
        for pid, row in dedupe.items():
            if (time.time() - started) > max_duration_s:
                logger.warning("Area mass stopped at enrichment due to time budget")
                break
            if len(enriched) >= max_enriched:
                logger.info("Area mass enriched cap reached: %s", max_enriched)
                break

            try:
                details = self.places.place_details(pid)
            except Exception:
                details = {}
            merged = dict(row)
            merged.update({k: v for k, v in details.items() if v is not None})

            geometry = merged.get("geometry", {}) or {}
            location = geometry.get("location", {}) or {}
            lat = location.get("lat")
            lng = location.get("lng")
            if lat is None or lng is None:
                continue

            types = merged.get("types") or []
            rating = merged.get("rating")
            votes = merged.get("user_ratings_total")

            roof_sqm = self._estimate_roof_sqm(types, merged.get("name"), votes)

            annual_savings = self._estimate_savings(roof_sqm, types)
            open_now_like = bool(merged.get("opening_hours") and merged["opening_hours"].get("weekday_text"))
            lead_score = self._score(roof_sqm, types, rating, open_now_like)

            opening_hours = None
            if merged.get("opening_hours") and merged["opening_hours"].get("weekday_text"):
                opening_hours = list(merged["opening_hours"]["weekday_text"])

            website = merged.get("website")
            discovered_email = None

            business_type = types[0] if types else "point_of_interest"

            enriched.append(
                AreaMassSearchResult(
                    place_id=pid,
                    name=merged.get("name") or "Unknown",
                    address=merged.get("formatted_address") or merged.get("vicinity") or "",
                    lat=float(lat),
                    lng=float(lng),
                    types=types,
                    business_type=business_type,
                    rating=rating,
                    user_ratings_total=votes,
                    business_status=merged.get("business_status"),
                    website=website,
                    email=discovered_email,
                    phone=merged.get("formatted_phone_number") or merged.get("international_phone_number"),
                    opening_hours=opening_hours,
                    estimated_roof_sqm=roof_sqm,
                    estimated_annual_savings=annual_savings,
                    lead_score=lead_score,
                    lead_grade=self._grade(lead_score),
                )
            )

        enriched.sort(key=lambda x: (x.lead_score, x.estimated_roof_sqm, x.user_ratings_total or 0), reverse=True)

        self._save_cached(cache_key, [r.model_dump() for r in enriched])
        export_url = self._export_csv(enriched, cache_key)
        logger.info(
            "Area mass completed: rows=%s tiles=%s duration_s=%.2f",
            len(enriched),
            len(tiles),
            time.time() - started,
        )
        return enriched, len(enriched), export_url
