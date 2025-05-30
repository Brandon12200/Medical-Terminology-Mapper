#!/usr/bin/env python
"""
Verify the contents of the terminology databases.
"""

import os
import sqlite3
import sys

def print_table_contents(db_path, table_name, limit=5):
    """Print the first few rows of a database table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    
    # Get sample data
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    rows = cursor.fetchall()
    
    print(f"\nDatabase: {os.path.basename(db_path)}")
    print(f"Table: {table_name}")
    print(f"Total rows: {row_count}")
    print("\nSample data:")
    
    # Print column headers
    header = " | ".join(columns)
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in rows:
        row_str = " | ".join(str(item) for item in row)
        print(row_str)
    
    print("\n")
    conn.close()

def main():
    # Define database paths
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "terminology")
    snomed_db = os.path.join(data_dir, "snomed_core.sqlite")
    loinc_db = os.path.join(data_dir, "loinc_core.sqlite")
    rxnorm_db = os.path.join(data_dir, "rxnorm_core.sqlite")
    
    # Print contents of each database
    print("=== Terminology Database Contents ===")
    
    print_table_contents(snomed_db, "snomed_concepts")
    print_table_contents(loinc_db, "loinc_concepts")
    print_table_contents(rxnorm_db, "rxnorm_concepts")

if __name__ == "__main__":
    main()