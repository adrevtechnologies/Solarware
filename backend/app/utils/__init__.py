"""Utility functions and utilities initialization."""
from .validators import validate_coordinates, validate_search_bounds, validate_roof_area
from .solar_calculations import (
    calculate_solar_analysis,
    calculate_panel_count,
    calculate_panel_count_advanced,
    calculate_system_capacity,
    calculate_annual_production,
    calculate_annual_savings,
    get_solar_irradiance,
    get_electricity_rate,
    sqft_to_sqm,
    sqm_to_sqft,
)
from .cost_estimator import SolarCostEstimator
from .address_geocoder import AddressGeocoder
from .geo import haversine, get_bounding_box_for_point, get_grid_points, calculate_area_from_bounds
from .files import ensure_output_dir, get_mailing_pack_dir, generate_filename, save_file

__all__ = [
    # Validators
    "validate_coordinates",
    "validate_search_bounds",
    "validate_roof_area",
    # Solar calculations
    "calculate_solar_analysis",
    "calculate_panel_count",
    "calculate_panel_count_advanced",
    "calculate_system_capacity",
    "calculate_annual_production",
    "calculate_annual_savings",
    "get_solar_irradiance",
    "get_electricity_rate",
    "sqft_to_sqm",
    "sqm_to_sqft",
    # Cost estimation
    "SolarCostEstimator",
    # Address geocoding
    "AddressGeocoder",
    # Geo utilities
    "haversine",
    "get_bounding_box_for_point",
    "get_grid_points",
    "calculate_area_from_bounds",
    # File utilities
    "ensure_output_dir",
    "get_mailing_pack_dir",
    "generate_filename",
    "save_file",
]
