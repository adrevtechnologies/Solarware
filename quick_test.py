import requests
import json
import time

# Create area
area_data = {
    'name': 'Test',
    'country': 'ZA',
    'region': 'WC',
    'min_latitude': -33.95,
    'max_latitude': -33.93,
    'min_longitude': 18.57,
    'max_longitude': 18.59,
    'min_roof_area_sqft': 500
}

r = requests.post('http://localhost:8000/api/search-areas', json=area_data)
print('CREATE:', r.status_code)
area = r.json()
print('Area ID:', area.get('id'))

# Process
r = requests.post(f"http://localhost:8000/api/process/search-area/{area['id']}")
print('PROCESS:', r.status_code, r.text[:200])

# Status
time.sleep(5)
r = requests.get(f"http://localhost:8000/api/process/status/{area['id']}")
print('STATUS:', r.status_code, r.json())

# Get prospects
r = requests.get(f"http://localhost:8000/api/prospects?search_area_id={area['id']}")
print('PROSPECTS:', r.status_code, len(r.json()), 'found')
if r.json():
    p = r.json()[0]
    print('\n✅ PROSPECT DATA POPULATED:')
    print('  • satellite_image_url:', bool(p.get('satellite_image_url')))
    print('  • mockup_image_url:', bool(p.get('mockup_image_url')))
    print('  • total_bos_cost:', p.get('total_bos_cost'))
    print('  • panel_cost:', p.get('panel_cost'))
    print('  • inverter_cost:', p.get('inverter_cost'))
    print('  • roi_simple_payback_years:', p.get('roi_simple_payback_years'))
    print('  • layout_efficiency:', p.get('layout_efficiency'))
