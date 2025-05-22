#!/usr/bin/env python3
import sqlite3
import os

# Connect to the database
db_path = os.path.join('data', 'terminology', 'rxnorm_core.sqlite')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# Get column info for rxnorm_concepts
cursor.execute("PRAGMA table_info(rxnorm_concepts)")
print("\nColumns in rxnorm_concepts:")
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

# Close connection
conn.close()