"""Test configuration and fixtures."""
import pytest
from app.core import get_settings


@pytest.fixture
def settings():
    """Provide test settings."""
    return get_settings()


@pytest.fixture
def test_search_area():
    """Provide test search area data."""
    return {
        "name": "Test Area",
        "country": "US",
        "region": "CA",
        "min_latitude": 40.7,
        "max_latitude": 40.8,
        "min_longitude": -74.0,
        "max_longitude": -73.9,
        "min_roof_area_sqft": 5000,
    }


@pytest.fixture
def test_prospect():
    """Provide test prospect data."""
    return {
        "address": "123 Test St",
        "latitude": 40.75,
        "longitude": -73.95,
        "roof_area_sqft": 10000,
        "roof_area_sqm": 929,
    }
