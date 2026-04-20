"""Google Places New proxy endpoints for reliable frontend autocomplete."""
from typing import List, Optional

import requests
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..core.config import get_settings


router = APIRouter(prefix="/api/places", tags=["places"])


class AutocompleteRequest(BaseModel):
    input: str
    session_token: Optional[str] = None
    region_code: str = "za"


class AutocompleteSuggestion(BaseModel):
    place_id: str
    main_text: str
    secondary_text: str = ""
    full_text: str


class AutocompleteResponse(BaseModel):
    suggestions: List[AutocompleteSuggestion]


class PlaceDetailsResponse(BaseModel):
    place_id: str
    formatted_address: str
    business_name: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None


def _extract_component(components: List[dict], component_type: str) -> Optional[str]:
    for component in components:
        types = component.get("types") or []
        if component_type in types:
            return component.get("longText") or component.get("shortText")
    return None


@router.post("/autocomplete", response_model=AutocompleteResponse)
def places_autocomplete(request: AutocompleteRequest):
    settings = get_settings()
    api_key = settings.GOOGLE_SERVER_KEY or settings.GOOGLE_MAPS_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="Google Places key is not configured")

    query = (request.input or "").strip()
    if len(query) < 2:
        return AutocompleteResponse(suggestions=[])

    try:
        response = requests.post(
            "https://places.googleapis.com/v1/places:autocomplete",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": (
                    "suggestions.placePrediction.place,"
                    "suggestions.placePrediction.text,"
                    "suggestions.placePrediction.structuredFormat"
                ),
            },
            json={
                "input": query,
                "languageCode": "en",
                # Prefer South Africa results first, while still allowing global matches.
                "regionCode": request.region_code or "za",
                "sessionToken": request.session_token,
            },
            timeout=10,
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Places autocomplete failed: {response.text}")

        payload = response.json()
        suggestions: List[AutocompleteSuggestion] = []
        for item in payload.get("suggestions") or []:
            prediction = item.get("placePrediction") or {}
            place_name = str(prediction.get("place") or "")
            place_id = place_name.replace("places/", "")
            if not place_id:
                continue

            main_text = (
                ((prediction.get("structuredFormat") or {}).get("mainText") or {}).get("text")
                or ((prediction.get("text") or {}).get("text") or "")
            )
            secondary_text = (
                ((prediction.get("structuredFormat") or {}).get("secondaryText") or {}).get("text")
                or ""
            )
            full_text = ((prediction.get("text") or {}).get("text") or "").strip()
            if not full_text:
                full_text = ", ".join([part for part in [main_text, secondary_text] if part])

            suggestions.append(
                AutocompleteSuggestion(
                    place_id=place_id,
                    main_text=main_text,
                    secondary_text=secondary_text,
                    full_text=full_text,
                )
            )

        return AutocompleteResponse(suggestions=suggestions)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Places autocomplete error: {exc}")


@router.get("/{place_id}", response_model=PlaceDetailsResponse)
def place_details(place_id: str, session_token: Optional[str] = Query(default=None)):
    settings = get_settings()
    api_key = settings.GOOGLE_SERVER_KEY or settings.GOOGLE_MAPS_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="Google Places key is not configured")

    try:
        response = requests.get(
            f"https://places.googleapis.com/v1/places/{place_id}",
            headers={
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": "id,displayName,formattedAddress,location,addressComponents",
            },
            params={
                "languageCode": "en",
                "regionCode": "za",
                "sessionToken": session_token,
            },
            timeout=10,
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Places details failed: {response.text}")

        payload = response.json()
        components = payload.get("addressComponents") or []

        city = (
            _extract_component(components, "locality")
            or _extract_component(components, "postal_town")
            or _extract_component(components, "administrative_area_level_2")
        )
        province = _extract_component(components, "administrative_area_level_1")
        country = _extract_component(components, "country") or "South Africa"

        return PlaceDetailsResponse(
            place_id=payload.get("id") or place_id,
            formatted_address=payload.get("formattedAddress") or "",
            business_name=((payload.get("displayName") or {}).get("text") or ""),
            lat=((payload.get("location") or {}).get("latitude")),
            lng=((payload.get("location") or {}).get("longitude")),
            city=city,
            province=province,
            country=country,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Places details error: {exc}")
