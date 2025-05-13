"""
Database updater for terminology databases.

This module provides utilities for importing data into the embedded
terminology databases from CSV and other formats.
"""

import os
import csv
import sqlite3
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

def create_empty_database(db_path: str, terminology_type: str) -> None:
    """
    Creates an empty terminology database with the appropriate schema.
    
    Args:
        db_path: Path to the database file
        terminology_type: Type of terminology (snomed, loinc, rxnorm)
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connect to new database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create schema based on terminology type
        if terminology_type == 'snomed':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS snomed_concepts (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL,
                    term TEXT NOT NULL,
                    display TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                );
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_term ON snomed_concepts(term);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_code ON snomed_concepts(code);')
            
        elif terminology_type == 'loinc':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS loinc_concepts (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL,
                    term TEXT NOT NULL,
                    display TEXT NOT NULL,
                    component TEXT,
                    property TEXT,
                    time TEXT,
                    system TEXT,
                    scale TEXT,
                    method TEXT
                );
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_term ON loinc_concepts(term);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_code ON loinc_concepts(code);')
            
        elif terminology_type == 'rxnorm':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rxnorm_concepts (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL,
                    term TEXT NOT NULL,
                    display TEXT NOT NULL,
                    tty TEXT,
                    is_active INTEGER DEFAULT 1
                );
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_term ON rxnorm_concepts(term);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_code ON rxnorm_concepts(code);')
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info(f"Created empty {terminology_type} database at {db_path}")
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise

def import_from_csv(csv_path: str, db_path: str, terminology_type: str) -> int:
    """
    Imports data from a CSV file into a terminology database.
    
    Args:
        csv_path: Path to the CSV file
        db_path: Path to the database file
        terminology_type: Type of terminology (snomed, loinc, rxnorm)
        
    Returns:
        Count of imported records
    """
    try:
        # Check if files exist
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Create database if it doesn't exist
        if not os.path.exists(db_path):
            create_empty_database(db_path, terminology_type)
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table name and fields
        table_name = f"{terminology_type}_concepts"
        
        if terminology_type == 'snomed':
            fields = ['code', 'term', 'display', 'is_active']
        elif terminology_type == 'loinc':
            fields = ['code', 'term', 'display', 'component', 'property', 
                     'time', 'system', 'scale', 'method']
        elif terminology_type == 'rxnorm':
            fields = ['code', 'term', 'display', 'tty', 'is_active']
        else:
            raise ValueError(f"Unsupported terminology type: {terminology_type}")
        
        # Prepare SQL statement
        placeholders = ', '.join(['?'] * len(fields))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({placeholders})"
        
        # Import data
        count = 0
        
        # Begin transaction
        conn.execute('BEGIN TRANSACTION')
        
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                values = [row.get(field, '') for field in fields]
                cursor.execute(insert_sql, values)
                count += 1
                
                # Log progress for large files
                if count % 10000 == 0:
                    logger.info(f"Imported {count} records...")
        
        # Commit transaction
        conn.commit()
        
        # Close connection
        conn.close()
        
        logger.info(f"Successfully imported {count} records into {terminology_type} database")
        return count
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        # Rollback if connection exists
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        raise

def create_sample_databases(data_dir: str) -> None:
    """
    Creates sample databases with test data for development.
    
    Args:
        data_dir: Directory containing terminology data
    """
    try:
        # Define paths
        sample_dir = os.path.join(data_dir, 'sample_data')
        
        # Check if sample directory exists
        if not os.path.exists(sample_dir):
            logger.error(f"Sample data directory not found: {sample_dir}")
            return
        
        # Create databases
        terminologies = [
            {'type': 'snomed', 'file': 'snomed_sample.csv'},
            {'type': 'loinc', 'file': 'loinc_sample.csv'},
            {'type': 'rxnorm', 'file': 'rxnorm_sample.csv'}
        ]
        
        for term in terminologies:
            csv_path = os.path.join(sample_dir, term['file'])
            db_path = os.path.join(data_dir, f"{term['type']}_core.sqlite")
            
            if os.path.exists(csv_path):
                logger.info(f"Creating sample {term['type']} database...")
                create_empty_database(db_path, term['type'])
                count = import_from_csv(csv_path, db_path, term['type'])
                logger.info(f"Sample {term['type']} database created with {count} records")
            else:
                logger.warning(f"Sample file not found: {csv_path}")
        
        logger.info('Sample databases creation completed')
    except Exception as e:
        logger.error(f"Error creating sample databases: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Database updater for terminology databases')
    parser.add_argument('--data-dir', default=None, help='Directory containing terminology data')
    parser.add_argument('--create-sample', action='store_true', help='Create sample databases')
    parser.add_argument('--import-csv', action='store_true', help='Import data from CSV file')
    parser.add_argument('--csv-path', help='Path to CSV file')
    parser.add_argument('--db-path', help='Path to database file')
    parser.add_argument('--terminology', choices=['snomed', 'loinc', 'rxnorm'], help='Terminology type')
    
    args = parser.parse_args()
    
    # Set default data directory if not provided
    if args.data_dir is None:
        args.data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))))), 
            'data', 'terminology'
        )
    
    # Create sample databases
    if args.create_sample:
        create_sample_databases(args.data_dir)
    
    # Import data from CSV
    if args.import_csv:
        if not args.csv_path or not args.db_path or not args.terminology:
            logger.error("--csv-path, --db-path, and --terminology are required for --import-csv")
        else:
            import_from_csv(args.csv_path, args.db_path, args.terminology)