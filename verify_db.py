import sqlite3
import os

db_path = "test_solarware.db"
if not os.path.exists(db_path):
    print(f"ERROR: Database not found at {db_path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in current dir: {os.listdir('.')}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("=" * 60)
    print("TABLES IN DATABASE:")
    print("=" * 60)
    for table in tables:
        print(f"\n📊 TABLE: {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            print(f"   {name:20} {type_:15} PK={pk} NOT_NULL={notnull}")
        
        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   ✓ ROWS: {count}")
    
    # Sample a row
    print("\n" + "=" * 60)
    print("SAMPLE DATA:")
    print("=" * 60)
    cursor.execute("SELECT * FROM prospects LIMIT 1")
    row = cursor.fetchone()
    if row:
        cursor.execute("PRAGMA table_info(prospects)")
        cols = cursor.fetchall()
        for i, col in enumerate(cols):
            print(f"   {col[1]:20}: {row[i]}")
    
    conn.close()
