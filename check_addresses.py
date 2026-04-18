#!/usr/bin/env python3
"""Check address content"""
import sqlite3

conn = sqlite3.connect('backend/test_solarware.db')
cursor = conn.cursor()

# Get unique words in addresses
print("=== SAMPLE ADDRESSES (first 20) ===")
cursor.execute("SELECT DISTINCT address FROM prospects LIMIT 20")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# Check if any address contains "Goodwood"
cursor.execute("SELECT COUNT(*) FROM prospects WHERE address LIKE '%Goodwood%'")
goodwood_count = cursor.fetchone()[0]
print(f"\nAddresses containing 'Goodwood': {goodwood_count}")

# Check if any address contains "Cape Town"
cursor.execute("SELECT COUNT(*) FROM prospects WHERE address LIKE '%Cape Town%'")
ct_count = cursor.fetchone()[0]
print(f"Addresses containing 'Cape Town': {ct_count}")

# Get a few addresses with real names
print("\n=== ADDRESSES WITH REAL LOCATION NAMES (sample) ===")
cursor.execute("SELECT address FROM prospects WHERE address NOT LIKE 'Building near%' LIMIT 10")
for row in cursor.fetchall():
    print(f"  {row[0]}")

conn.close()
