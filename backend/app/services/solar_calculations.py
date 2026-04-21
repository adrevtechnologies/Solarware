"""
Real Solar Calculations Engine
Based on:
- Roof area estimates from map providers
- Building type (affects usable roof %)
- South African solar yields by region
- Real tariff scenarios (no installation pricing)
"""
import logging
from typing import Dict, Tuple
import math

logger = logging.getLogger(__name__)

# South African solar yield (kWh per kW per year) by province
SA_SOLAR_YIELD = {
    "Western Cape": 1650,
    "Gauteng": 1700,
    "Free State": 1750,
    "Northern Cape": 1850,
    "Eastern Cape": 1600,
    "KwaZulu-Natal": 1550,
    "Limpopo": 1725,
    "Mpumalanga": 1675,
    "North West": 1730,
}

# Default tariff scenarios (R per kWh)
TARIFF_LOW = 1.80
TARIFF_MEDIUM = 2.40
TARIFF_HIGH = 3.00

# Roof usable percentage fixed for V1 panel estimate.
ROOF_USABLE_FACTOR = 0.72

PANEL_FOOTPRINT_SQM = 2.2
PANEL_KW = 0.55


def get_regional_yield(province: str = None) -> int:
    """Get annual solar yield (kWh/kW) for province"""
    if province and province in SA_SOLAR_YIELD:
        return SA_SOLAR_YIELD[province]
    return 1650  # Western Cape default


def get_roof_usable_factor(building_type: str) -> float:
    """Get percentage of roof usable for solar (0.0 - 1.0)"""
    return ROOF_USABLE_FACTOR


def calculate_solar_capacity(roof_area_sqm: float, building_type: str) -> Tuple[float, float]:
    """
    Calculate solar system capacity range
    
    Assumptions:
    - 1 kW requires 5-7 sqm (modern 400-500W panels)
    - Apply roof usable factor
    
    RETURNS: (capacity_low_kw, capacity_high_kw)
    """
    usable_area_sqm = roof_area_sqm * ROOF_USABLE_FACTOR
    panel_count = max(0, int(usable_area_sqm / PANEL_FOOTPRINT_SQM))
    capacity_kw = panel_count * PANEL_KW
    capacity_kw = math.floor(capacity_kw * 10) / 10
    return (capacity_kw, capacity_kw)


def calculate_annual_generation(
    capacity_kw: float,
    province: str = None
) -> float:
    """
    Calculate annual energy generation in kWh
    
    Formula: annual_kwh = capacity_kw × regional_yield
    
    RETURNS: annual_kwh (use middle value of capacity range)
    """
    yield_per_kw = 1650
    return capacity_kw * yield_per_kw


def calculate_annual_savings(annual_kwh: float) -> Dict[str, float]:
    """
    Calculate annual savings in Rands using 3 tariff scenarios
    
    No installation pricing - only operational savings
    
    RETURNS: {
        'low': savings with R1.80/kWh,
        'medium': savings with R2.40/kWh,
        'high': savings with R3.20/kWh
    }
    """
    return {
        "low": annual_kwh * TARIFF_LOW,
        "medium": annual_kwh * TARIFF_MEDIUM,
        "high": annual_kwh * TARIFF_HIGH,
    }


def calculate_solar_score(
    roof_area_sqm: float,
    building_type: str,
    province: str = None,
) -> int:
    """
    Calculate solar viability score (0-100)
    
    Base: 50
    
    Add:
    - Roof > 500 sqm: +20
    - Warehouse/factory/industrial: +15
    - High sun region (Northern Cape, Free State): +10
    - Simple roof type: +5 (already accounted in building_type)
    
    Subtract:
    - Roof < 150 sqm: -20
    - Complex/unusual building: -10 (shrines, stadiums, etc)
    - Poor sun region (Eastern Cape, KZN): -5
    
    Clamp to 0-100
    """
    score = 50

    # Roof size factor
    if roof_area_sqm > 500:
        score += 20
    elif roof_area_sqm < 150:
        score -= 20

    # Building type factor
    if building_type in ["warehouse", "factory", "industrial"]:
        score += 15
    elif building_type in ["retail", "office"]:
        score += 5

    # Region factor
    high_sun_regions = ["Northern Cape", "Free State", "Limpopo"]
    low_sun_regions = ["Eastern Cape", "KwaZulu-Natal"]

    if province in high_sun_regions:
        score += 10
    elif province in low_sun_regions:
        score -= 5

    # Clamp
    score = max(0, min(100, score))

    return score


def get_solar_stats(
    roof_area_sqm: float,
    building_type: str,
    province: str = None
) -> Dict:
    """
    All-in-one solar calculation
    
    RETURNS complete solar opportunity data
    """
    usable_roof_sqm = roof_area_sqm * ROOF_USABLE_FACTOR
    panel_count = max(0, int(usable_roof_sqm / PANEL_FOOTPRINT_SQM))

    capacity_low, capacity_high = calculate_solar_capacity(roof_area_sqm, building_type)

    # Keep panel count and capacity physically consistent.
    panel_capacity_kw = (panel_count * PANEL_KW)
    if panel_capacity_kw > 0:
        capacity_low = min(capacity_low, panel_capacity_kw)
        capacity_high = min(capacity_high, panel_capacity_kw)
        if capacity_high < capacity_low:
            capacity_high = capacity_low

    capacity_mid = (capacity_low + capacity_high) / 2

    annual_kwh_low = calculate_annual_generation(capacity_low, province)
    annual_kwh_high = calculate_annual_generation(capacity_high, province)
    annual_kwh_mid = calculate_annual_generation(capacity_mid, province)

    savings = calculate_annual_savings(annual_kwh_mid)
    score = calculate_solar_score(roof_area_sqm, building_type, province)

    return {
        "roof_area_sqm": round(roof_area_sqm, 1),
        "usable_roof_sqm": round(usable_roof_sqm, 1),
        "estimated_panel_count": panel_count,
        "capacity_low_kw": round(capacity_low, 1),
        "capacity_high_kw": round(capacity_high, 1),
        "capacity_mid_kw": round(capacity_mid, 1),
        "annual_kwh_low": round(annual_kwh_low, 0),
        "annual_kwh_high": round(annual_kwh_high, 0),
        "annual_kwh_mid": round(annual_kwh_mid, 0),
        "savings_low": round(savings["low"], 0),
        "savings_mid": round(savings["medium"], 0),
        "savings_high": round(savings["high"], 0),
        "solar_score": score,
    }
