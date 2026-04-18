#!/usr/bin/env python3
"""
Test the new /api/search endpoint
"""
import requests
import json

# Test cases
test_cases = [
    {
        "name": "Search all prospects (no filter)",
        "params": {
            "mode": "area",
            "area": "Building",
            "filters": {}
        }
    },
    {
        "name": "Search with high solar score filter",
        "params": {
            "mode": "area",
            "area": "Building",
            "filters": {
                "highSolarScore": True
            }
        }
    },
    {
        "name": "Search with roof size filter",
        "params": {
            "mode": "area",
            "area": "Building",
            "filters": {
                "minRoofSize": 5000
            }
        }
    }
]

for test in test_cases:
    print(f"\n{'='*60}")
    print(f"Test: {test['name']}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/search",
            json=test['params'],
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} prospects")
            
            # Check first prospect has required fields
            if data['results']:
                prospect = data['results'][0]
                required_fields = [
                    'id', 'address', 'business_name', 'property_type',
                    'roof_area_sqft', 'solar_score', 'contact_status',
                    'phone', 'email'
                ]
                
                missing = [f for f in required_fields if f not in prospect]
                if missing:
                    print(f"⚠️ Missing fields: {missing}")
                else:
                    print("✅ All required fields present")
                    print(f"\nFirst prospect:")
                    print(json.dumps(prospect, indent=2))
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

