"""Unit tests for utility functions."""
import pytest
from app.utils import (
    validate_coordinates,
    validate_search_bounds,
    calculate_solar_analysis,
    sqft_to_sqm,
    sqm_to_sqft,
    get_solar_irradiance,
    get_electricity_rate,
)
from app.core.errors import ValidationError


class TestCoordinateValidation:
    """Test coordinate validation."""

    def test_valid_coordinates(self):
        """Test valid coordinates."""
        assert validate_coordinates(40.7128, -74.0060) is True
        assert validate_coordinates(-33.8688, 151.2093) is True  # Sydney
        assert validate_coordinates(0, 0) is True  # Equator/Prime Meridian

    def test_invalid_latitude(self):
        """Test invalid latitude."""
        with pytest.raises(ValidationError):
            validate_coordinates(95.0, 0.0)
        with pytest.raises(ValidationError):
            validate_coordinates(-100.0, 0.0)

    def test_invalid_longitude(self):
        """Test invalid longitude."""
        with pytest.raises(ValidationError):
            validate_coordinates(0.0, 200.0)
        with pytest.raises(ValidationError):
            validate_coordinates(0.0, -190.0)


class TestSearchBoundsValidation:
    """Test search bounds validation."""

    def test_valid_bounds(self):
        """Test valid bounds."""
        assert validate_search_bounds(40.7, 40.8, -74.0, -73.9) is True

    def test_inverted_latitude(self):
        """Test inverted latitude bounds."""
        with pytest.raises(ValidationError):
            validate_search_bounds(40.8, 40.7, -74.0, -73.9)

    def test_inverted_longitude(self):
        """Test inverted longitude bounds."""
        with pytest.raises(ValidationError):
            validate_search_bounds(40.7, 40.8, -73.9, -74.0)


class TestAreaConversion:
    """Test area conversion."""

    def test_sqft_to_sqm(self):
        """Test square feet to square meters."""
        # 10,000 sq ft ≈ 929 sq m
        result = sqft_to_sqm(10000)
        assert 920 < result < 940

    def test_sqm_to_sqft(self):
        """Test square meters to square feet."""
        # 929 sq m ≈ 10,000 sq ft
        result = sqm_to_sqft(929)
        assert 9990 < result < 10010


class TestSolarAnalysis:
    """Test solar analysis calculations."""

    def test_solar_irradiance_us(self):
        """Test solar irradiance for US."""
        irradiance = get_solar_irradiance("US")
        assert 4.0 < irradiance < 5.0

    def test_solar_irradiance_california(self):
        """Test solar irradiance for California."""
        irradiance = get_solar_irradiance("US", "CA")
        assert 5.0 < irradiance < 6.0  # Should be higher than US average

    def test_electricity_rate(self):
        """Test electricity rates."""
        us_rate = get_electricity_rate("US")
        assert 0.10 < us_rate < 0.20

    def test_complete_analysis(self):
        """Test complete solar analysis."""
        result = calculate_solar_analysis(
            roof_area_sqft=10000,
            roof_area_sqm=929,
            country="US",
        )
        
        assert "panel_count" in result
        assert "system_capacity_kw" in result
        assert "annual_production_kwh" in result
        assert "annual_savings" in result
        
        assert result["panel_count"] > 0
        assert result["system_capacity_kw"] > 0
        assert result["annual_production_kwh"] > 0
        assert result["annual_savings"] > 0
