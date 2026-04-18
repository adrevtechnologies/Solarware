#!/usr/bin/env python3
"""
Quick test of the complete API flow with image and cost data verification.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_complete_flow():
    print("🧪 TESTING FULL API FLOW WITH COMPLETE DATA")
    print("=" * 80)
    
    # Create a search area
    print("\n1️⃣  Creating search area...")
    area_data = {
        "name": "Test Area",
        "country": "ZA",
        "region": "WC",
        "min_latitude": -33.95,
        "max_latitude": -33.93,
        "min_longitude": 18.57,
        "max_longitude": 18.59,
        "min_roof_area_sqft": 500
    }
    
    resp = requests.post(f"{BASE_URL}/search-areas", json=area_data)
    print(f"   Status: {resp.status_code}")
    if resp.status_code != 200 and resp.status_code != 201:
        print(f"   Error: {resp.text}")
        return
    
    area = resp.json()
    print(f"   ✓ Area created: {area['id'][:8]}...")
    area_id = area['id']
    
    # Trigger processing
    print("\n2️⃣  Triggering discovery process...")
    resp = requests.post(f"{BASE_URL}/search-areas/{area_id}/process")
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.json()}")
    
    # Wait for processing
    print("\n3️⃣  Waiting for processing to complete...")
    for attempt in range(30):
        resp = requests.get(f"{BASE_URL}/search-areas/{area_id}/status")
        status = resp.json().get('status', 'unknown')
        print(f"   Attempt {attempt+1}: {status}")
        if status == 'completed':
            break
        if status == 'failed':
            print(f"   Error: {resp.json().get('errors', [])}")
            return
        time.sleep(2)
    
    # Get prospects
    print("\n4️⃣  Fetching prospects...")
    resp = requests.get(f"{BASE_URL}/prospects?search_area_id={area_id}&limit=100")
    print(f"   Status: {resp.status_code}")
    prospects = resp.json()
    print(f"   Found: {len(prospects)} prospects")
    
    if prospects:
        print("\n5️⃣  PROSPECT DATA VALIDATION")
        print("=" * 80)
        prospect = prospects[0]
        
        # Check for image URLs
        print("\n📸 IMAGE FIELDS:")
        print(f"   • satellite_image_url: {bool(prospect.get('satellite_image_url'))} - {prospect.get('satellite_image_url')[:50]}..." if prospect.get('satellite_image_url') else "   • satellite_image_url: ❌ MISSING")
        print(f"   • mockup_image_url: {bool(prospect.get('mockup_image_url'))} - {prospect.get('mockup_image_url')[:50]}..." if prospect.get('mockup_image_url') else "   • mockup_image_url: ❌ MISSING")
        
        # Check for solar system data
        print("\n☀️ SOLAR SYSTEM DATA:")
        print(f"   • estimated_panel_count: {prospect.get('estimated_panel_count')} ✓" if prospect.get('estimated_panel_count') else "   • estimated_panel_count: ❌ MISSING")
        print(f"   • estimated_system_capacity_kw: {prospect.get('estimated_system_capacity_kw')} kW ✓" if prospect.get('estimated_system_capacity_kw') else "   • estimated_system_capacity_kw: ❌ MISSING")
        print(f"   • estimated_annual_production_kwh: {prospect.get('estimated_annual_production_kwh')} kWh ✓" if prospect.get('estimated_annual_production_kwh') else "   • estimated_annual_production_kwh: ❌ MISSING")
        print(f"   • layout_efficiency: {prospect.get('layout_efficiency')}% ✓" if prospect.get('layout_efficiency') else "   • layout_efficiency: ❌ MISSING")
        
        # Check for financial data
        print("\n💰 FINANCIAL DATA:")
        print(f"   • estimated_annual_savings_usd: R{prospect.get('estimated_annual_savings_usd')} ✓" if prospect.get('estimated_annual_savings_usd') else "   • estimated_annual_savings_usd: ❌ MISSING")
        
        # Check for cost breakdown
        print("\n💵 COST BREAKDOWN:")
        print(f"   • total_bos_cost: R{prospect.get('total_bos_cost')} ✓" if prospect.get('total_bos_cost') else "   • total_bos_cost: ❌ MISSING")
        print(f"   • panel_cost: R{prospect.get('panel_cost')} ✓" if prospect.get('panel_cost') else "   • panel_cost: ❌ MISSING")
        print(f"   • inverter_cost: R{prospect.get('inverter_cost')} ✓" if prospect.get('inverter_cost') else "   • inverter_cost: ❌ MISSING")
        print(f"   • battery_cost: R{prospect.get('battery_cost')} ✓" if prospect.get('battery_cost') else "   • battery_cost: ❌ MISSING")
        print(f"   • installation_cost: R{prospect.get('installation_cost')} ✓" if prospect.get('installation_cost') else "   • installation_cost: ❌ MISSING")
        print(f"   • soft_costs: R{prospect.get('soft_costs')} ✓" if prospect.get('soft_costs') else "   • soft_costs: ❌ MISSING")
        
        # Check for ROI data
        print("\n📊 ROI DATA:")
        print(f"   • roi_simple_payback_years: {prospect.get('roi_simple_payback_years')} years ✓" if prospect.get('roi_simple_payback_years') is not None else "   • roi_simple_payback_years: ❌ MISSING")
        print(f"   • roi_percentage_20yr: {prospect.get('roi_percentage_20yr')}% ✓" if prospect.get('roi_percentage_20yr') else "   • roi_percentage_20yr: ❌ MISSING")
        
        # Summary
        print("\n" + ("=" * 80))
        required_fields = [
            'satellite_image_url', 'mockup_image_url',
            'estimated_panel_count', 'estimated_system_capacity_kw', 'estimated_annual_production_kwh', 'layout_efficiency',
            'estimated_annual_savings_usd',
            'total_bos_cost', 'panel_cost', 'inverter_cost', 'installation_cost', 'soft_costs',
            'roi_simple_payback_years', 'roi_percentage_20yr'
        ]
        
        populated = sum(1 for f in required_fields if prospect.get(f) is not None)
        total = len(required_fields)
        
        print(f"\n✅ COMPLETION: {populated}/{total} critical fields populated ({100*populated//total}%)")
        
        if populated == total:
            print("🎉 ALL FIELDS PRESENT AND READY FOR FRONTEND!")
        else:
            print(f"⚠️  Missing: {', '.join([f for f in required_fields if prospect.get(f) is None])}")
    else:
        print("❌ No prospects returned!")

if __name__ == "__main__":
    test_complete_flow()
