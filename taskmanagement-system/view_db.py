import sqlite3
import os

# Get the database file
db_file = 'payroll_system.db'

# Check if database exists
if not os.path.exists(db_file):
    print(f"Database '{db_file}' not found!")
    print("Creating database...")
    from py.database import initialize_db
    initialize_db()
    print("Database created!")

# Connect to database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

print("\n" + "="*60)
print("PAYROLL SYSTEM DATABASE")
print("="*60)

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    print(f"\n📋 TABLE: {table_name.upper()}")
    print("-"*40)
    
    # Get column info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print("Columns:")
    for col in columns:
        print(f"  • {col[1]} ({col[2]})")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\nTotal records: {count}")
    
    # Show sample data (first 5 rows)
    if count > 0:
        print("\nSample data:")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {row}")
    print()

conn.close()
print("="*60)