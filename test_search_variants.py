#!/usr/bin/env python3
import requests
import json

# Test 1: Simple area search
payload1 = {
    'mode': 'area',
    'area': 'Goodwood'
}

print("=== TEST 1: Area search for Goodwood ===")
resp = requests.post('http://127.0.0.1:8000/api/search', json=payload1, timeout=5)
print(f'Status: {resp.status_code}')
data = resp.json()
print(f'Count: {data.get("count", 0)}')

# Test 2: Country search
payload2 = {
    'mode': 'country',
    'country': 'South Africa'
}

print("\n=== TEST 2: Country search for South Africa ===")
resp = requests.post('http://127.0.0.1:8000/api/search', json=payload2, timeout=5)
print(f'Status: {resp.status_code}')
data = resp.json()
print(f'Count: {data.get("count", 0)}')
if data.get('results'):
    print(f'First result: {data["results"][0]}')

# Test 3: Address search (try a known address)
payload3 = {
    'mode': 'address',
    'street': '69 Holloway Road'
}

print("\n=== TEST 3: Address search ===")
resp = requests.post('http://127.0.0.1:8000/api/search', json=payload3, timeout=5)
print(f'Status: {resp.status_code}')
data = resp.json()
print(f'Count: {data.get("count", 0)}')
if data.get('results'):
    print(f'First result: {data["results"][0]}')
