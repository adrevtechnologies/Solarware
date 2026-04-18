#!/usr/bin/env python3
"""Check search areas"""
import sqlite3

conn = sqlite3.connect('backend/test_solarware.db')
cursor = conn.cursor()

cursor.execute("SELECT sa.id, sa.name, sa.country, sa.region, COUNT(p.id) as prospects FROM search_areas sa LEFT JOIN prospects p ON sa.id = p.search_area_id GROUP BY sa.id ORDER BY prospects DESC")
rows = cursor.fetchall()

print("=== SEARCH AREAS ===")
for row in rows:
    print(f"\nID: {row[0][:8]}...")
    print(f"  Name: {row[1]}")
    print(f"  Country: {row[2]}")
    print(f"  Region: {row[3]}")
    print(f"  Prospects: {row[4]}")

# Show geographic coverage
print("\n=== GEOGRAPHIC BOUNDS (to understand search logic) ===")
cursor.execute("SELECT name, min_latitude, max_latitude, min_longitude, max_longitude FROM search_areas")
for row in cursor.fetchall():
    print(f"\n{row[0]}:")
    print(f"  Lat: {row[1]:.4f} to {row[2]:.4f}")
    print(f"  Lon: {row[3]:.4f} to {row[4]:.4f}")

conn.close()
