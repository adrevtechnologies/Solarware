"""Utility validators and helpers."""
from ..core.errors import ValidationError


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate geographic coordinates.
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If coordinates are invalid
    """
    if not -90 <= latitude <= 90:
        raise ValidationError(f"Invalid latitude: {latitude}. Must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValidationError(f"Invalid longitude: {longitude}. Must be between -180 and 180")
    return True


def validate_search_bounds(min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> bool:
    """Validate search area bounds.
    
    Args:
        min_lat: Minimum latitude
        max_lat: Maximum latitude
        min_lon: Minimum longitude
        max_lon: Maximum longitude
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If bounds are invalid
    """
    validate_coordinates(min_lat, min_lon)
    validate_coordinates(max_lat, max_lon)
    
    if min_lat >= max_lat:
        raise ValidationError("min_latitude must be less than max_latitude")
    if min_lon >= max_lon:
        raise ValidationError("min_longitude must be less than max_longitude")
    
    return True


def validate_roof_area(area_sqft: float) -> bool:
    """Validate roof area.
    
    Args:
        area_sqft: Roof area in square feet
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If area is invalid
    """
    if area_sqft < 100:
        raise ValidationError("Roof area must be at least 100 sqft")
    if area_sqft > 1000000:  # 1M sqft limit (23 acres)
        raise ValidationError("Roof area appears to be invalid (exceeds 1,000,000 sqft)")
    return True
