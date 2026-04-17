"""Cost estimation for solar installations."""
from typing import Dict
import math


class SolarCostEstimator:
    """Comprehensive cost estimation for solar PV systems."""
    
    # Pricing data (South Africa ZAR for local relevance)
    PRICING = {
        "ZA": {  # South Africa
            "panel_cost_per_watt": 8.50,      # R8.50 per watt
            "inverter_cost_per_kw": 4500,     # R4,500 per kW capacity
            "battery_cost_per_kwh": 12000,    # R12,000 per kWh (lithium)
            "cable_cost_per_meter": 45,       # R45 per meter
            "installation_labor_per_panel": 280,  # R280 per panel
            "team_size": 5,                   # Main team
            "casual_workers": 2,              # Heavy lifting team
            "labor_hours_setup": 8,           # Site setup
            "labor_hours_per_string": 6,      # Per string installation
            "electricity_rate_rands_per_kwh": 2.50,  # R2.50/kWh (2026 estimate)
        },
        "US": {
            "panel_cost_per_watt": 1.05,
            "inverter_cost_per_kw": 600,
            "battery_cost_per_kwh": 1500,
            "cable_cost_per_meter": 5.50,
            "installation_labor_per_panel": 35,
            "team_size": 5,
            "casual_workers": 2,
            "labor_hours_setup": 8,
            "labor_hours_per_string": 6,
            "electricity_rate_usd_per_kwh": 0.14,
        },
    }
    
    # Regional overrides
    REGIONAL_ADJUSTMENTS = {
        "ZA": {
            "WC": 0.95,  # Western Cape - slightly cheaper
            "GP": 0.98,  # Gauteng
            "KZN": 1.02, # KwaZulu-Natal - slight premium
        }
    }
    
    @staticmethod
    def estimate_bos_costs(
        system_capacity_kw: float,
        panel_count: int,
        country: str = "ZA",
        region: str = None,
        battery_capacity_kwh: float = 0,
    ) -> Dict[str, float]:
        """Estimate balance-of-system (BOS) costs.
        
        Args:
            system_capacity_kw: System size in kW
            panel_count: Number of panels
            country: Country code
            region: Region/province code
            battery_capacity_kwh: Optional battery storage size
        
        Returns:
            Dictionary with cost breakdown
        """
        country = country.upper()
        pricing = SolarCostEstimator.PRICING.get(country, SolarCostEstimator.PRICING["US"])
        
        # Regional adjustment
        adjustment = 1.0
        if country in SolarCostEstimator.REGIONAL_ADJUSTMENTS and region:
            adjustment = SolarCostEstimator.REGIONAL_ADJUSTMENTS[country].get(region.upper(), 1.0)
        
        # Panel costs
        panel_capacity_w = system_capacity_kw * 1000
        panel_cost = panel_capacity_w * pricing["panel_cost_per_watt"] * adjustment
        
        # Inverter costs (1.25x system capacity for headroom)
        inverter_capacity_kw = system_capacity_kw * 1.25
        inverter_cost = inverter_capacity_kw * pricing["inverter_cost_per_kw"] * adjustment
        
        # Battery costs (if specified)
        battery_cost = battery_capacity_kwh * pricing["battery_cost_per_kwh"] * adjustment if battery_capacity_kwh > 0 else 0
        
        # Cable costs (complex calculation based on strings and conductor sizing)
        cable_runs = math.ceil(panel_count / 16)  # Typical 16 panels per string
        cable_length = cable_runs * 25  # ~25m average per run (main combiner + to inverter)
        
        # Conductor sizing: use wire gauge based on current
        # Typical: ~7-8A per 1kW for 48V system, use #10 AWG for runs up to 100ft
        cable_cost = cable_length * pricing["cable_cost_per_meter"] * adjustment
        
        # Labor (installation labor)
        labor_cost = panel_count * pricing["installation_labor_per_panel"] * adjustment
        
        # Soft costs (permits, engineering, interconnection, etc.)
        soft_costs = (panel_cost + inverter_cost + battery_cost + cable_cost + labor_cost) * 0.15
        
        return {
            "panel_cost": round(panel_cost, 2),
            "inverter_cost": round(inverter_cost, 2),
            "battery_cost": round(battery_cost, 2),
            "cable_cost": round(cable_cost, 2),
            "installation_labor": round(labor_cost, 2),
            "soft_costs": round(soft_costs, 2),
            "total_bos_cost": round(panel_cost + inverter_cost + battery_cost + cable_cost + labor_cost + soft_costs, 2),
        }
    
    @staticmethod
    def estimate_installation_time(
        panel_count: int,
        system_capacity_kw: float,
        team_size: int = 5,
        casual_workers: int = 2,
        country: str = "ZA"
    ) -> Dict[str, float]:
        """Estimate installation timeline.
        
        Args:
            panel_count: Number of panels
            system_capacity_kw: System size
            team_size: Main team size
            casual_workers: Heavy lifting support workers
            country: Country code
        
        Returns:
            Time estimates
        """
        country = country.upper()
        pricing = SolarCostEstimator.PRICING.get(country, SolarCostEstimator.PRICING["US"])
        
        # Normalize to pricing model
        team_size = pricing["team_size"]
        casual_workers = pricing["casual_workers"]
        
        # Time calculations
        setup_hours = pricing["labor_hours_setup"]  # Site prep, safety, staging
        
        # Strings and parallel strings
        panels_per_string = 16  # Typical for 48V systems
        num_strings = math.ceil(panel_count / panels_per_string)
        string_installation_hours = num_strings * pricing["labor_hours_per_string"]
        
        # Electrical work (combiner box, main disconnect, breakers, fuses)
        electrical_hours = 4 + (num_strings * 0.5)
        
        # Inverter installation and testing
        inverter_hours = 3
        
        # Racking only (subfactor for heavy lifting team)
        racking_hours = panel_count * 0.15  # ~9 minutes per panel
        
        # Total
        total_labor_hours = setup_hours + string_installation_hours + electrical_hours + inverter_hours + racking_hours
        
        # Calculate crew-hours and calendar days
        main_team_hours = total_labor_hours  # All skilled work
        casual_team_hours = racking_hours * 1.5  # Casual workers assist with racking
        
        # Concurrent work: assume 80% parallel efficiency
        concurrent_hours = max(main_team_hours, casual_team_hours * 0.8)
        
        # Calendar days (8-hour work days)
        calendar_days_main = main_team_hours / (team_size * 8)
        calendar_days_casual = casual_team_hours / (casual_workers * 8) if casual_workers > 0 else 0
        
        # Total project days (sequential phasing)
        total_project_days = calendar_days_main + calendar_days_casual + 0.5  # +0.5 for testing/commissioning
        
        return {
            "setup_hours": round(setup_hours, 1),
            "racking_hours": round(racking_hours, 1),
            "string_installation_hours": round(string_installation_hours, 1),
            "electrical_hours": round(electrical_hours, 1),
            "inverter_hours": round(inverter_hours, 1),
            "total_labor_hours": round(total_labor_hours, 1),
            "main_team_crew_hours": round(main_team_hours, 1),
            "casual_team_crew_hours": round(casual_team_hours, 1),
            "calendar_days": round(total_project_days, 1),
            "team_size": team_size,
            "casual_workers": casual_workers,
        }
    
    @staticmethod
    def estimate_system_roi(
        annual_production_kwh: float,
        total_cost: float,
        electricity_rate_per_kwh: float,
        inflation_rate: float = 0.06,
        system_degradation: float = 0.005,
    ) -> Dict[str, float]:
        """Calculate return on investment (ROI) metrics.
        
        Args:
            annual_production_kwh: Annual production in kWh
            total_cost: Total system cost
            electricity_rate_per_kwh: Current electricity rate
            inflation_rate: Annual inflation rate (default 0.06 = 6%)
            system_degradation: Annual system degradation (default 0.005 = 0.5%)
        
        Returns:
            ROI metrics
        """
        annual_savings = annual_production_kwh * electricity_rate_per_kwh
        
        # Simple payback period
        simple_payback = total_cost / annual_savings if annual_savings > 0 else 999
        
        # 25-year NPV (typical panel lifetime)
        npv = 0
        rate_of_return = 0.08  # Target 8% discount rate for NPV
        
        for year in range(1, 26):
            # Savings increase with inflation, production decreases with degradation
            year_production = annual_production_kwh * (1 - system_degradation) ** year
            year_rate = electricity_rate_per_kwh * (1 + inflation_rate) ** year
            year_savings = year_production * year_rate
            
            # Discount back to present value
            npv += year_savings / (1 + rate_of_return) ** year
        
        npv -= total_cost  # Subtract initial investment
        
        # 25-year cumulative savings
        cumulative_savings = 0
        for year in range(1, 26):
            year_production = annual_production_kwh * (1 - system_degradation) ** year
            year_rate = electricity_rate_per_kwh * (1 + inflation_rate) ** year
            cumulative_savings += year_production * year_rate
        
        return {
            "annual_savings": round(annual_savings, 2),
            "simple_payback_years": round(simple_payback, 1),
            "npv_25_years": round(npv, 2),
            "cumulative_savings_25_years": round(cumulative_savings, 2),
            "roi_percentage": round((npv / total_cost) * 100, 1) if total_cost > 0 else 0,
        }
