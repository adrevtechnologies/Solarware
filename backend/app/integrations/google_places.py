"""Google Places API client for backend search and enrichment."""
import re
import time
from typing import Any, Dict, List, Optional

import requests
from requests import RequestException


class GooglePlacesClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._nearby_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        self._text_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self._details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_s = 3600

    def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        row = self._cache.get(key)
        if not row:
            return None
        if (time.time() - row["ts"]) > self._cache_ttl_s:
            self._cache.pop(key, None)
            return None
        return row["value"]

    def _cache_set(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        self._cache[key] = {"ts": time.time(), "value": value}
        return value

    def _request(self, url: str, params: Dict[str, Any], timeout: int = 12) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "MISSING_KEY", "results": []}
        base_params = dict(params)
        base_params["key"] = self.api_key
        cache_key = f"{url}|{str(sorted(base_params.items()))}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            response = requests.get(url, params=base_params, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            return self._cache_set(cache_key, payload)
        except RequestException:
            # Return a safe payload so callers can keep processing instead of failing the whole search.
            return {"status": "REQUEST_ERROR", "results": [], "result": {}}

    def search_nearby(
        self,
        lat: float,
        lng: float,
        radius: int = 500,
        keyword: str = "",
        place_type: Optional[str] = None,
        max_pages: int = 2,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "location": f"{lat},{lng}",
            "radius": int(radius),
        }
        if keyword:
            params["keyword"] = keyword
        if place_type:
            params["type"] = place_type

        merged: List[Dict[str, Any]] = []
        data = self._request(self._nearby_url, params)
        merged.extend(data.get("results", []))
        token = data.get("next_page_token")
        page = 1

        while token and page < max_pages:
            # Google Places next_page_token needs a short delay before becoming valid.
            time.sleep(2.1)
            page_data = self._request(self._nearby_url, {"pagetoken": token})
            merged.extend(page_data.get("results", []))
            token = page_data.get("next_page_token")
            page += 1

        return merged

    def search_text(self, query: str, max_pages: int = 2) -> List[Dict[str, Any]]:
        if not query.strip():
            return []
        data = self._request(self._text_url, {"query": query.strip()})
        merged = list(data.get("results", []))
        token = data.get("next_page_token")
        page = 1

        while token and page < max_pages:
            time.sleep(2.1)
            page_data = self._request(self._text_url, {"pagetoken": token})
            merged.extend(page_data.get("results", []))
            token = page_data.get("next_page_token")
            page += 1

        return merged

    def place_details(self, place_id: str) -> Dict[str, Any]:
        if not place_id:
            return {}
        fields = ",".join(
            [
                "place_id",
                "name",
                "formatted_address",
                "geometry",
                "types",
                "website",
                "formatted_phone_number",
                "international_phone_number",
                "business_status",
                "opening_hours",
                "rating",
                "user_ratings_total",
            ]
        )
        payload = self._request(self._details_url, {"place_id": place_id, "fields": fields}, timeout=6)
        return payload.get("result", {})

    def discover_website_email(self, website: Optional[str]) -> Optional[str]:
        """Best-effort email extraction from business website homepage."""
        if not website:
            return None
        try:
            if not website.startswith(("http://", "https://")):
                return None
            response = requests.get(website, timeout=3, headers={"User-Agent": "Solarware/1.0"})
            response.raise_for_status()
            text = response.text[:200000]
            matches = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
            if not matches:
                return None
            for email in matches:
                lower = email.lower()
                if not lower.endswith((".png", ".jpg", ".jpeg", ".svg")):
                    return email
            return None
        except Exception:
            return None
