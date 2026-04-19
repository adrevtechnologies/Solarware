#!/usr/bin/env python3
"""V1 API smoke test for active real-search flow."""

from __future__ import annotations

import json

import requests


BASE_URL = "http://localhost:8000"


def main() -> int:
    payload = {
        "country": "South Africa",
        "province": "Western Cape",
        "city": "Cape Town",
        "suburb": "Goodwood",
        "radius_m": 1500,
    }

    print("Testing active V1 endpoint: POST /api/search")
    response = requests.post(f"{BASE_URL}/api/search", json=payload, timeout=60)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        return 1

    data = response.json()
    print(f"Count: {data.get('count', 0)}")
    print(f"Message: {data.get('message', '')}")

    results = data.get("results", [])
    required_fields = [
        "address",
        "building_type",
        "roof_area_sqm",
        "estimated_panel_count",
        "satellite_image_url",
    ]

    if results:
        sample = results[0]
        missing = [field for field in required_fields if field not in sample]
        if missing:
            print(f"Missing expected fields in sample result: {missing}")
            return 1

        banned_fields = [
            "roi_simple_payback_years",
            "roi_percentage_20yr",
            "solar_confidence",
        ]
        leaked = [field for field in banned_fields if field in sample]
        if leaked:
            print(f"Unexpected legacy fields in result: {leaked}")
            return 1

    print("V1 API smoke test passed")
    print(json.dumps({"count": data.get("count", 0), "search_area": data.get("search_area")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
