"""Utility functions for solar calculations."""
import math
from typing import Dict, Optional
from datetime import datetime


# Solar irradiance data by country/region (simplified annual averages in kWh/m²/day)
SOLAR_IRRADIANCE_BY_COUNTRY = {
    "US": {
        "default": 4.5,
        "regions": {
            "CA": 5.5,  # California - highest
            "AZ": 5.8,
            "FL": 4.2,
            "NY": 3.8,
            "WA": 3.5,
        }
    },
    "ZA": {
        "default": 5.2,  # South Africa - excellent solar
        "regions": {
            "WC": 5.3,  # Western Cape
            "GP": 5.1,  # Gauteng
            "KZN": 4.9, # KwaZulu-Natal
            "EC": 5.0,  # Eastern Cape
        }
    },
    "DE": {"default": 3.2},  # Germany
    "UK": {"default": 2.8},
    "ES": {"default": 4.8},  # Spain
    "FR": {"default": 3.5},  # France
    "IT": {"default": 4.4},  # Italy
    "AU": {"default": 5.2},  # Australia
    "BR": {"default": 4.8},  # Brazil
    "IN": {"default": 5.0},  # India
    "CN": {"default": 4.2},  # China
    "MX": {"default": 5.6},  # Mexico
}

# Electricity rates by country (in local currency per kWh)
ELECTRICITY_RATES_BY_COUNTRY = {
    "US": 0.14,   # USD
    "ZA": 2.50,   # ZAR (2026 estimate)
    "DE": 0.36,   # EUR
    "UK": 0.32,   # GBP
    "ES": 0.23,   # EUR
    "FR": 0.18,   # EUR
    "IT": 0.27,   # EUR
    "AU": 0.28,   # AUD
    "BR": 0.13,   # BRL
    "IN": 0.10,   # INR
    "CN": 0.12,   # CNY
    "MX": 0.14,   # MXN
}


def get_solar_irradiance(country: str, region: str = None) -> float:
    """Get average annual solar irradiance for a location.
    
    Args:
        country: Two-letter country code
        region: Optional region/state code
    
    Returns:
        Solar irradiance in kWh/m²/day
    """
    country = country.upper()
    if country not in SOLAR_IRRADIANCE_BY_COUNTRY:
        return SOLAR_IRRADIANCE_BY_COUNTRY.get("US", {}).get("default", 4.5)
    
    country_data = SOLAR_IRRADIANCE_BY_COUNTRY[country]
    if region and "regions" in country_data:
        return country_data["regions"].get(region.upper(), country_data["default"])
    
    return country_data["default"]


def get_electricity_rate(country: str) -> float:
    """Get average electricity rate for a country.
    
    Args:
        country: Two-letter country code
    
    Returns:
        Electricity rate in $/kWh
    """
    country = country.upper()
    return ELECTRICITY_RATES_BY_COUNTRY.get(country, 0.15)


def calculate_panel_count_advanced(
    roof_area_sqm: float,
    panel_width: float = 1.75,
    panel_height: float = 1.05,
    inter_row_spacing_mm: float = 2000,
    walkway_area_sqm: float = 0,
    strings_per_array: int = 8,
    panels_per_string: int = 16,
) -> Dict[str, float]:
    """Calculate optimal panel placement with advanced considerations.
    
    Args:
        roof_area_sqm: Total roof area in square meters
        panel_width: Panel width in meters (default 1.75m)
        panel_height: Panel height in meters (default 1.05m)
        inter_row_spacing_mm: Spacing between panel rows in mm (default 2000mm = 2m)
        walkway_area_sqm: Area reserved for walkways (default 300m²)
        strings_per_array: Number of strings in parallel (default 8)
        panels_per_string: Number of panels in series per string (default 16)
    
    Returns:
        Dictionary with layout optimization details
    """
    # Convert spacing from mm to m
    inter_row_spacing_m = inter_row_spacing_mm / 1000.0
    
    # Use ratio-based walkway/equipment reservation to avoid over-penalizing smaller roofs.
    effective_walkway_sqm = walkway_area_sqm if walkway_area_sqm > 0 else (roof_area_sqm * 0.22)
    equipment_space_sqm = max(8.0, roof_area_sqm * 0.04)
    usable_area_sqm = roof_area_sqm - effective_walkway_sqm - equipment_space_sqm
    
    if usable_area_sqm <= 0:
        return {
            "panel_count": 0,
            "strings": 0,
            "panels_per_string": 0,
            "panel_area_sqm": 0,
            "usable_roof_area": usable_area_sqm,
            "walkway_area": round(effective_walkway_sqm, 2),
            "equipment_space": equipment_space_sqm,
            "layout_efficiency": 0.0,
            "error": "Insufficient space after walkways and equipment"
        }
    
    panel_area = panel_width * panel_height  # ~1.8375 m² per panel
    
    # Calculate optimal rows
    # Assume panels installed vertically (1.05m width when viewed from above)
    # With 2m spacing between row starts
    row_width = panel_width + inter_row_spacing_m
    
    # Estimate rows that fit
    estimated_rows = int(usable_area_sqm / (panel_area / panel_height * row_width))
    estimated_rows = max(1, estimated_rows)
    
    # Panels per row (panels fit side by side)
    panels_per_row = int(usable_area_sqm / (panel_area * estimated_rows))
    panels_per_row = max(panels_per_string, panels_per_row)  # At least one string
    
    # Total panels
    total_panels = estimated_rows * panels_per_row
    
    # String configuration
    num_strings = total_panels // panels_per_string
    num_strings = max(1, min(num_strings, strings_per_array))
    
    # Adjust total panels to fit string configuration
    total_panels = num_strings * panels_per_string
    
    # Actual area used by panels
    panel_area_used = total_panels * panel_area
    
    # Layout efficiency
    layout_efficiency = (panel_area_used / usable_area_sqm) * 100.0
    
    return {
        "panel_count": total_panels,
        "strings": num_strings,
        "panels_per_string": panels_per_string,
        "rows": estimated_rows,
        "panels_per_row": panels_per_row,
        "panel_area_sqm": round(panel_area_used, 2),
        "usable_roof_area": round(usable_area_sqm, 2),
        "walkway_area": round(effective_walkway_sqm, 2),
        "equipment_space": equipment_space_sqm,
        "inter_row_spacing_m": inter_row_spacing_m,
        "layout_efficiency": round(layout_efficiency, 1),
    }


def calculate_panel_count(roof_area_sqm: float, panel_width: float = 1.75, panel_height: float = 1.05) -> int:
    """Legacy function for backward compatibility."""
    result = calculate_panel_count_advanced(roof_area_sqm, panel_width, panel_height)
    return result.get("panel_count", 0)


def calculate_system_capacity(panel_count: int, panel_rated_power: float = 400) -> float:
    """Calculate system capacity in kW.
    
    Args:
        panel_count: Number of panels
        panel_rated_power: Rated power per panel in watts
    
    Returns:
        System capacity in kW
    """
    return (panel_count * panel_rated_power) / 1000


def calculate_annual_production(
    system_capacity_kw: float,
    solar_irradiance_kwh_m2_day: float,
    roof_area_sqm: float,
    system_efficiency: float = 0.82,
) -> float:
    """Calculate estimated annual energy production.
    
    Args:
        system_capacity_kw: System capacity in kW
        solar_irradiance_kwh_m2_day: Average daily solar irradiance
        roof_area_sqm: Roof area in square meters
        system_efficiency: System efficiency factor (0-1)
    
    Returns:
        Annual production in kWh
    """
    if system_capacity_kw <= 0:
        return 0.0

    # Simple planning figure for outreach scoring, not a contractual energy forecast.
    daily_kwh = system_capacity_kw * solar_irradiance_kwh_m2_day * system_efficiency
    annual_kwh = daily_kwh * 365
    return annual_kwh


def calculate_annual_savings(
    annual_production_kwh: float,
    electricity_rate_per_kwh: float,
) -> float:
    """Calculate estimated annual savings in dollars.
    
    Args:
        annual_production_kwh: Annual energy production in kWh
        electricity_rate_per_kwh: Electricity rate in $/kWh
    
    Returns:
        Annual savings in dollars
    """
    return annual_production_kwh * electricity_rate_per_kwh


def calculate_solar_analysis(
    roof_area_sqft: float,
    roof_area_sqm: float,
    country: str,
    region: str = None,
    panel_width_m: float = 1.75,
    panel_height_m: float = 1.05,
    panel_rated_power_w: int = 400,
    system_efficiency: float = 0.82,
    include_costs: bool = True,
    battery_capacity_kwh: float = 0,
) -> Dict[str, float]:
    """Calculate complete solar analysis for a prospect.
    
    Args:
        roof_area_sqft: Roof area in square feet
        roof_area_sqm: Roof area in square meters
        country: Two-letter country code
        region: Optional region/state code
        panel_width_m: Panel width in meters
        panel_height_m: Panel height in meters
        panel_rated_power_w: Rated power per panel in watts
        system_efficiency: System efficiency factor
        include_costs: Whether to include cost estimation
        battery_capacity_kwh: Optional battery capacity
    
    Returns:
        Dictionary with analysis results
    """
    # Advanced panel calculation with spacing/walkways
    layout = calculate_panel_count_advanced(
        roof_area_sqm,
        panel_width_m,
        panel_height_m,
        inter_row_spacing_mm=2000,
        walkway_area_sqm=0,
    )
    
    panel_count = layout.get("panel_count", 0)
    system_capacity_kw = calculate_system_capacity(panel_count, panel_rated_power_w)
    solar_irradiance = get_solar_irradiance(country, region)
    annual_production = calculate_annual_production(
        system_capacity_kw,
        solar_irradiance,
        roof_area_sqm,
        system_efficiency
    )
    electricity_rate = get_electricity_rate(country)
    annual_savings = calculate_annual_savings(annual_production, electricity_rate)
    
    result = {
        "panel_count": panel_count,
        "system_capacity_kw": round(system_capacity_kw, 2),
        "annual_production_kwh": round(annual_production, 0),
        "annual_savings": round(annual_savings, 2),
        "solar_irradiance_kwh_m2_day": solar_irradiance,
        "electricity_rate_per_kwh": electricity_rate,
        "layout_efficiency": layout.get("layout_efficiency", 0),
        "strings": layout.get("strings", 0),
        "rows": layout.get("rows", 0),
    }
    
    # Add cost estimation if requested
    if include_costs:
        from app.utils.cost_estimator import SolarCostEstimator
        
        costs = SolarCostEstimator.estimate_bos_costs(
            system_capacity_kw,
            panel_count,
            country,
            region,
            battery_capacity_kwh
        )
        result.update(costs)
        
        # Add installation timeline
        timeline = SolarCostEstimator.estimate_installation_time(
            panel_count,
            system_capacity_kw,
            country=country
        )
        result.update({
            f"installation_{k}": v for k, v in timeline.items()
        })
        
        # Add ROI metrics
        roi = SolarCostEstimator.estimate_system_roi(
            annual_production,
            costs["total_bos_cost"],
            electricity_rate
        )
        result.update({
            f"roi_{k}": v for k, v in roi.items()
        })
    
    return result


def sqft_to_sqm(sqft: float) -> float:
    """Convert square feet to square meters."""
    return sqft / 10.764


def sqm_to_sqft(sqm: float) -> float:
    """Convert square meters to square feet."""
    return sqm * 10.764
