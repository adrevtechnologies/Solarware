#!/usr/bin/env python3
"""Standalone Goodwood check using the active V1 API."""

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
        "street_name": "Richmond Street",
        "street_number": "98",
        "radius_m": 500,
    }

    print("Running Goodwood exact-address check on V1 API")
    response = requests.post(f"{BASE_URL}/api/search", json=payload, timeout=60)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        return 1

    data = response.json()
    results = data.get("results", [])

    print(json.dumps({
        "count": data.get("count", 0),
        "search_area": data.get("search_area"),
        "message": data.get("message"),
    }, indent=2))

    if not isinstance(results, list):
        print("Invalid response: results is not a list")
        return 1

    if results:
        first = results[0]
        summary = {
            "address": first.get("address"),
            "building_type": first.get("building_type"),
            "roof_area_sqm": first.get("roof_area_sqm"),
            "estimated_panel_count": first.get("estimated_panel_count"),
            "satellite_image_url": first.get("satellite_image_url"),
        }
        print("Top result sample:")
        print(json.dumps(summary, indent=2))

    print("Goodwood check completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
