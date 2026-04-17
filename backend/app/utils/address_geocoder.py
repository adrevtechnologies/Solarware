"""Address geocoding utilities."""
from typing import Tuple, Dict, Optional
import re


class AddressGeocoder:
    """Mock geocoder for address to coordinates conversion."""
    
    # Known locations database for testing
    KNOWN_LOCATIONS = {
        # South Africa - Cape Town area
        ("goodwood", "cape town", "za"): (-33.9402, 18.5828, "Goodwood, Cape Town"),
        ("richmond street", "goodwood", "cape town"): (-33.9402, 18.5828, "98 Richmond Street, Goodwood, Cape Town"),
        ("98 richmond", "goodwood", "cape town"): (-33.9402, 18.5828, "98 Richmond Street, Goodwood, Cape Town"),
        
        # US - San Francisco
        ("mission district", "san francisco", "ca"): (37.7599, -122.4148, "Mission District, San Francisco, CA"),
        ("brooklyn", "new york", "ny"): (40.6501, -73.9496, "Brooklyn, New York"),
        
        # Europe
        ("berlin", "germany", "de"): (52.5200, 13.4050, "Berlin, Germany"),
        ("london", "uk", "uk"): (51.5074, -0.1278, "London, UK"),
    }
    
    # Regional bounding boxes for fallback search areas
    REGIONAL_BOUNDS = {
        ("cape town", "za"): {
            "min_lat": -34.2,
            "max_lat": -33.8,
            "min_lon": 18.3,
            "max_lon": 18.8,
            "name": "Cape Town Metro Area",
        },
        ("goodwood", "cape town"): {
            "min_lat": -33.95,
            "max_lat": -33.93,
            "min_lon": 18.57,
            "max_lon": 18.59,
            "name": "Goodwood, Cape Town",
        },
        ("san francisco", "ca"): {
            "min_lat": 37.60,
            "max_lat": 37.87,
            "min_lon": -123.17,
            "max_lon": -122.35,
            "name": "San Francisco Metro Area",
        },
        ("brooklyn", "ny"): {
            "min_lat": 40.55,
            "max_lat": 40.73,
            "min_lon": -74.04,
            "max_lon": -73.86,
            "name": "Brooklyn, New York",
        },
    }
    
    # Regional bounding boxes for fallback search areas (by country)
    COUNTRY_DEFAULTS = {
        "us": {"lat": 37.0, "lon": -95.0, "name": "United States", "radius": 50.0},
        "uk": {"lat": 51.5, "lon": -0.1, "name": "United Kingdom", "radius": 30.0},
        "de": {"lat": 51.1, "lon": 10.4, "name": "Germany", "radius": 25.0},
        "za": {"lat": -30.5, "lon": 22.9, "name": "South Africa", "radius": 60.0},
        "au": {"lat": -25.2, "lon": 133.8, "name": "Australia", "radius": 100.0},
        "br": {"lat": -14.2, "lon": -51.9, "name": "Brazil", "radius": 80.0},
    }
    
    @staticmethod
    def normalize_address_parts(
        street: Optional[str],
        area: Optional[str],
        district: Optional[str],
        city: Optional[str],
        region: Optional[str],
        country: str,
    ) -> Tuple[str, str, str, str]:
        """Normalize address components for lookup.
        
        Returns: (search_city, search_area, search_country, full_address_str)
        """
        address_parts = []
        
        if street:
            address_parts.append(street.lower().strip())
        if area:
            address_parts.append(area.lower().strip())
        if district:
            address_parts.append(district.lower().strip())
        if city:
            address_parts.append(city.lower().strip())
        if region:
            address_parts.append(region.upper().strip())
            
        address_parts.append(country.upper())
        
        full_address = ", ".join(address_parts)
        
        # Return priority fields for lookup
        search_city = city.lower().strip() if city else ""
        search_area = area.lower().strip() if area else (district.lower().strip() if district else "")
        search_country = country.upper().strip()
        
        return search_city, search_area, search_country, full_address
    
    @staticmethod
    def geocode_address(
        street: Optional[str] = None,
        area: Optional[str] = None,
        district: Optional[str] = None,
        city: Optional[str] = None,
        region: Optional[str] = None,
        country: str = "ZA",
    ) -> Dict:
        """Convert address to coordinates and search bounds.
        
        Args:
            street: Street address
            area: Area/neighborhood
            district: District
            city: City
            region: Region/province/state
            country: Country code
        
        Returns:
            Dictionary with geocoding result including coordinates and bounds
        """
        search_city, search_area, search_country, full_address = AddressGeocoder.normalize_address_parts(
            street, area, district, city, region, country
        )
        
        # Try exact match first
        search_key = (search_area, search_city, search_country)
        if search_key in AddressGeocoder.KNOWN_LOCATIONS:
            lat, lon, display_name = AddressGeocoder.KNOWN_LOCATIONS[search_key]
            return {
                "latitude": lat,
                "longitude": lon,
                "full_address": display_name,
                "bounds": AddressGeocoder.get_bounds_for_coords(lat, lon, 1.0),
                "confidence": 0.95,
                "source": "known_location",
            }
        
        # Try with just area and country
        search_key2 = (search_area, search_country)
        for key in AddressGeocoder.KNOWN_LOCATIONS:
            if search_area and len(key) >= 2 and key[0] == search_area and key[-1] == search_country:
                lat, lon, display_name = AddressGeocoder.KNOWN_LOCATIONS[key]
                return {
                    "latitude": lat,
                    "longitude": lon,
                    "full_address": display_name,
                    "bounds": AddressGeocoder.get_bounds_for_coords(lat, lon, 2.0),
                    "confidence": 0.85,
                    "source": "partial_match",
                }
        
        # Try regional bounds
        regional_key = (search_city, search_country) if search_city else (search_area, search_country)
        if regional_key in AddressGeocoder.REGIONAL_BOUNDS:
            bounds = AddressGeocoder.REGIONAL_BOUNDS[regional_key]
            center_lat = (bounds["min_lat"] + bounds["max_lat"]) / 2
            center_lon = (bounds["min_lon"] + bounds["max_lon"]) / 2
            
            return {
                "latitude": center_lat,
                "longitude": center_lon,
                "full_address": full_address,
                "bounds": {
                    "min_latitude": bounds["min_lat"],
                    "max_latitude": bounds["max_lat"],
                    "min_longitude": bounds["min_lon"],
                    "max_longitude": bounds["max_lon"],
                },
                "confidence": 0.70,
                "source": "regional_bounds",
            }
        
        # Fallback: default to center of country/region
        return AddressGeocoder.get_default_bounds_for_country(search_country)
    
    @staticmethod
    def get_bounds_for_coords(
        latitude: float,
        longitude: float,
        radius_km: float = 1.0,
    ) -> Dict[str, float]:
        """Get search bounds for a point.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in km
        
        Returns:
            Dictionary with bounds
        """
        lat_offset = radius_km / 111.0  # ~111 km per degree
        lon_offset = radius_km / (111.0 * abs(__import__("math").cos(__import__("math").radians(latitude))))
        
        return {
            "min_latitude": latitude - lat_offset,
            "max_latitude": latitude + lat_offset,
            "min_longitude": longitude - lon_offset,
            "max_longitude": longitude + lon_offset,
        }
    
    @staticmethod
    def get_default_bounds_for_country(country: str) -> Dict:
        """Get default search bounds for a country."""
        country_lower = country.lower()
        bounds_data = AddressGeocoder.COUNTRY_DEFAULTS.get(country_lower, AddressGeocoder.COUNTRY_DEFAULTS["us"])
        bounds = AddressGeocoder.get_bounds_for_coords(
            bounds_data["lat"],
            bounds_data["lon"],
            bounds_data["radius"]
        )
        
        return {
            "latitude": bounds_data["lat"],
            "longitude": bounds_data["lon"],
            "full_address": bounds_data["name"],
            "bounds": bounds,
            "confidence": 0.50,
            "source": "country_default",
        }
