"""Utility functions for geospatial operations."""
from typing import Tuple, List
from math import radians, cos, sin, asin, sqrt


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculate great-circle distance between two points on Earth.
    
    Args:
        lon1: Longitude of point 1
        lat1: Latitude of point 1
        lon2: Longitude of point 2
        lat2: Latitude of point 2
    
    Returns:
        Distance in kilometers
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r


def get_bounding_box_for_point(
    latitude: float,
    longitude: float,
    radius_km: float
) -> Tuple[float, float, float, float]:
    """Get bounding box for a point with given radius.
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius_km: Radius in kilometers
    
    Returns:
        Tuple of (min_lat, max_lat, min_lon, max_lon)
    """
    lat_offset = radius_km / 111.0  # ~111 km per degree latitude
    lon_offset = radius_km / (111.0 * cos(radians(latitude)))
    
    return (
        latitude - lat_offset,
        latitude + lat_offset,
        longitude - lon_offset,
        longitude + lon_offset,
    )


def get_grid_points(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    grid_spacing_km: float = 1.0
) -> List[Tuple[float, float]]:
    """Generate a grid of points within bounds.
    
    Args:
        min_lat: Minimum latitude
        max_lat: Maximum latitude
        min_lon: Minimum longitude
        max_lon: Maximum longitude
        grid_spacing_km: Spacing between grid points in kilometers
    
    Returns:
        List of (latitude, longitude) tuples
    """
    lat_spacing = grid_spacing_km / 111.0
    lon_spacing = grid_spacing_km / (111.0 * cos(radians((min_lat + max_lat) / 2)))
    
    points = []
    lat = min_lat
    while lat <= max_lat:
        lon = min_lon
        while lon <= max_lon:
            points.append((lat, lon))
            lon += lon_spacing
        lat += lat_spacing
    
    return points


def calculate_area_from_bounds(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float
) -> float:
    """Calculate area of bounding box in square kilometers.
    
    Args:
        min_lat: Minimum latitude
        max_lat: Maximum latitude
        min_lon: Minimum longitude
        max_lon: Maximum longitude
    
    Returns:
        Area in square kilometers
    """
    lat_dist = haversine(min_lon, min_lat, min_lon, max_lat)
    lon_dist = haversine(min_lon, (min_lat + max_lat) / 2, max_lon, (min_lat + max_lat) / 2)
    return lat_dist * lon_dist
