#!/usr/bin/env python3
import sqlite3

# Test absolute path
db_path = 'd:/Solarware/Solarware/test_solarware.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM prospects")
count = cursor.fetchone()[0]

print(f"Database at {db_path}")
print(f"Total prospects: {count}")

conn.close()
