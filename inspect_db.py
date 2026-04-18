#!/usr/bin/env python3
"""Inspect database structure"""
import sqlite3

conn = sqlite3.connect('backend/test_solarware.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("=== TABLES IN DATABASE ===")
for table in tables:
    table_name = table[0]
    print(f"\n{table_name}:")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  Rows: {count}")
    
    # Get schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"  Columns: {len(columns)}")
    for col in columns[:10]:  # Show first 10 columns
        print(f"    - {col[1]} ({col[2]})")

print("\n\n=== SAMPLE PROSPECT DATA ===")
cursor.execute("SELECT id, address, latitude, longitude, search_area_id, solar_confidence FROM prospects LIMIT 3")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0][:8]}...")
    print(f"  Address: {row[1]}")
    print(f"  Location: ({row[2]}, {row[3]})")
    print(f"  Search Area ID: {row[4]}")
    print(f"  Solar Confidence: {row[5]}\n")

conn.close()
