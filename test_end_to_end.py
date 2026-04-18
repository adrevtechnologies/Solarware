#!/usr/bin/env python
"""End-to-end test for search pipeline."""
import httpx
import json
import asyncio
import time


async def test_search():
    async with httpx.AsyncClient() as client:
        # Create search area
        search_payload = {
            'name': 'Test Cape Town',
            'country': 'ZA',
            'region': 'WC',
            'city': 'Cape Town',
            'area': 'Goodwood',
            'min_roof_area_sqft': 2000
        }
        
        try:
            resp = await client.post('http://localhost:8000/api/search-areas', json=search_payload, timeout=10.0)
            print(f'Create search area: {resp.status_code}')
            if resp.status_code in [200, 201]:
                area_data = resp.json()
                area_id = area_data.get('id')
                print(f'Search area ID: {area_id}')
                
                # Trigger processing
                proc_resp = await client.post(f'http://localhost:8000/api/process/search-area/{area_id}', timeout=60.0)
                print(f'Start processing: {proc_resp.status_code}')
                
                # Wait for processing
                await asyncio.sleep(5)
                
                # Get prospects
                prospects_resp = await client.get(f'http://localhost:8000/api/prospects?search_area_id={area_id}', timeout=10.0)
                print(f'Get prospects: {prospects_resp.status_code}')
                if prospects_resp.status_code == 200:
                    prospects = prospects_resp.json()
                    print(f'Prospects count: {len(prospects)}')
                    if prospects:
                        print(f'Sample prospect address: {prospects[0].get("address")}')
                        print(f'Sample prospect type: {prospects[0].get("business_type")}')
                        print(f'Sample prospect roof sqft: {prospects[0].get("roof_area_sqft")}')
                        print('SUCCESS: Full search pipeline works!')
            else:
                print(f'Error response: {resp.text}')
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_search())
