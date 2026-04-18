"""Unit tests for Nominatim helper math."""

from app.services.nominatim_service import get_bounding_box


def test_get_bounding_box_longitude_span_reasonable_at_mid_latitude():
    """Ensure longitude span scales correctly and is not collapsed near Cape Town latitude."""
    lat = -33.9043
    lon = 18.5635
    min_lat, max_lat, min_lon, max_lon = get_bounding_box(lat, lon, radius_km=0.3)

    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon

    # For small radii at this latitude, lon span should be slightly larger than lat span.
    assert lat_span > 0
    assert lon_span > 0
    assert lon_span > lat_span * 0.9
    assert lon_span < lat_span * 1.4


def test_get_bounding_box_handles_equator_without_crash():
    """Ensure longitude calculation is stable at/near the equator."""
    min_lat, max_lat, min_lon, max_lon = get_bounding_box(0.0, 0.0, radius_km=1.0)
    assert max_lat > min_lat
    assert max_lon > min_lon
