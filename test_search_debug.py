#!/usr/bin/env python3
import requests
import json

payload = {
    'mode': 'area',
    'area': 'Goodwood',
    'filters': {}
}

try:
    resp = requests.post('http://127.0.0.1:8000/api/search', json=payload, timeout=5)
    print(f'Status: {resp.status_code}')
    data = resp.json()
    print(f'Count: {data.get("count", 0)}')
    if data.get('results'):
        print('First result:')
        print(json.dumps(data['results'][0], indent=2))
    else:
        print('No results returned')
        print(f'Response: {json.dumps(data, indent=2)}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
