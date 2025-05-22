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
            # Main concepts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS snomed_concepts (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL,
                    term TEXT NOT NULL,
                    display TEXT NOT NULL,
                    concept_type TEXT,
                    is_active INTEGER DEFAULT 1
                );
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_term ON snomed_concepts(term);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_code ON snomed_concepts(code);')
            
            # Relationships table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS snomed_relationships (
                    id INTEGER PRIMARY KEY,
                    source_code TEXT NOT NULL,
                    destination_code TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (source_code) REFERENCES snomed_concepts(code),
                    FOREIGN KEY (destination_code) REFERENCES snomed_concepts(code)
                );
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_rel_source ON snomed_relationships(source_code);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_rel_dest ON snomed_relationships(destination_code);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_rel_type ON snomed_relationships(relationship_type);')
            
        elif terminology_type == 'loinc':
            # Main LOINC concepts table with extended fields
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
                    method TEXT,
                    long_common_name TEXT,
                    class TEXT,
                    version_last_changed TEXT,
                    status TEXT DEFAULT 'ACTIVE',
                    consumer_name TEXT,
                    classtype INTEGER,
                    order_obs TEXT
                );
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_term ON loinc_concepts(term);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_code ON loinc_concepts(code);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_component ON loinc_concepts(component);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_system ON loinc_concepts(system);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_class ON loinc_concepts(class);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_order_obs ON loinc_concepts(order_obs);')
            
            # LOINC parts table for multiaxial hierarchy
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS loinc_parts (
                    id INTEGER PRIMARY KEY,
                    part_number TEXT NOT NULL,
                    part_name TEXT NOT NULL,
                    part_display_name TEXT NOT NULL,
                    part_type TEXT NOT NULL,
                    status TEXT DEFAULT 'ACTIVE'
                );
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_part_number ON loinc_parts(part_number);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_part_type ON loinc_parts(part_type);')
            
            # LOINC concept-parts mapping
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS loinc_concept_parts (
                    id INTEGER PRIMARY KEY,
                    loinc_code TEXT NOT NULL,
                    part_number TEXT NOT NULL,
                    part_type TEXT NOT NULL,
                    FOREIGN KEY (loinc_code) REFERENCES loinc_concepts(code),
                    FOREIGN KEY (part_number) REFERENCES loinc_parts(part_number)
                );
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_concept_parts_code ON loinc_concept_parts(loinc_code);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_concept_parts_part ON loinc_concept_parts(part_number);')
            
            # LOINC hierarchy for panel-component relationships
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS loinc_hierarchy (
                    id INTEGER PRIMARY KEY,
                    parent_code TEXT NOT NULL,
                    child_code TEXT NOT NULL,
                    hierarchy_type TEXT NOT NULL,
                    FOREIGN KEY (parent_code) REFERENCES loinc_concepts(code),
                    FOREIGN KEY (child_code) REFERENCES loinc_concepts(code)
                );
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_hierarchy_parent ON loinc_hierarchy(parent_code);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_hierarchy_child ON loinc_hierarchy(child_code);')
            
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

def import_from_csv(csv_path: str, db_path: str, terminology_type: str, data_type: str = 'concepts') -> int:
    """
    Imports data from a CSV file into a terminology database.
    
    Args:
        csv_path: Path to the CSV file
        db_path: Path to the database file
        terminology_type: Type of terminology (snomed, loinc, rxnorm)
        data_type: Type of data to import ('concepts' or 'relationships')
        
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
        
        # Verify that needed tables exist
        if data_type == 'relationships':
            # Check if the relationships table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{terminology_type}_relationships'")
            if cursor.fetchone() is None:
                logger.warning(f"{terminology_type}_relationships table doesn't exist, creating it...")
                
                # Manually create the relationship table
                if terminology_type == 'snomed':
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS snomed_relationships (
                        id INTEGER PRIMARY KEY,
                        source_code TEXT NOT NULL,
                        destination_code TEXT NOT NULL,
                        relationship_type TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1,
                        FOREIGN KEY (source_code) REFERENCES snomed_concepts(code),
                        FOREIGN KEY (destination_code) REFERENCES snomed_concepts(code)
                    )
                    ''')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_rel_source ON snomed_relationships(source_code)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_rel_dest ON snomed_relationships(destination_code)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snomed_rel_type ON snomed_relationships(relationship_type)')
                
                elif terminology_type == 'rxnorm':
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rxnorm_relationships (
                        id INTEGER PRIMARY KEY,
                        source_code TEXT NOT NULL,
                        destination_code TEXT NOT NULL,
                        relationship_type TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1,
                        FOREIGN KEY (source_code) REFERENCES rxnorm_concepts(code),
                        FOREIGN KEY (destination_code) REFERENCES rxnorm_concepts(code)
                    )
                    ''')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_rel_source ON rxnorm_relationships(source_code)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_rel_dest ON rxnorm_relationships(destination_code)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_rel_type ON rxnorm_relationships(relationship_type)')
                
                conn.commit()
        
        # Import based on data type
        if data_type == 'concepts':
            count = _import_concepts(cursor, csv_path, terminology_type)
        elif data_type == 'relationships':
            if terminology_type == 'snomed':
                count = _import_snomed_relationships(cursor, csv_path)
            elif terminology_type == 'rxnorm':
                count = _import_rxnorm_relationships(cursor, csv_path)
            else:
                raise ValueError(f"Unsupported relationship data type for {terminology_type}")
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
        
        # Commit transaction and close connection
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully imported {count} {data_type} records into {terminology_type} database")
        return count
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        # Rollback if connection exists
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        raise

def _import_concepts(cursor, csv_path: str, terminology_type: str) -> int:
    """
    Imports concept data from a CSV file.
    
    Args:
        cursor: Database cursor
        csv_path: Path to the CSV file
        terminology_type: Type of terminology
        
    Returns:
        Count of imported records
    """
    # Get table name and fields
    table_name = f"{terminology_type}_concepts"
    
    if terminology_type == 'snomed':
        fields = ['code', 'term', 'display', 'concept_type', 'is_active']
    elif terminology_type == 'loinc':
        fields = ['code', 'term', 'display', 'component', 'property', 
                 'time', 'system', 'scale', 'method', 'long_common_name', 
                 'class', 'version_last_changed', 'status', 'consumer_name', 
                 'classtype', 'order_obs']
    elif terminology_type == 'rxnorm':
        fields = ['code', 'term', 'display', 'tty', 'is_active']
    else:
        raise ValueError(f"Unsupported terminology type: {terminology_type}")
    
    # Prepare SQL statement
    available_fields = []
    with open(csv_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        if reader.fieldnames:
            available_fields = [f for f in fields if f in reader.fieldnames]
    
    if not available_fields:
        raise ValueError(f"No matching fields found in CSV file: {csv_path}")
    
    placeholders = ', '.join(['?'] * len(available_fields))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(available_fields)}) VALUES ({placeholders})"
    
    # Import data
    count = 0
    
    # Begin transaction
    cursor.execute('BEGIN TRANSACTION')
    
    with open(csv_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            values = [row.get(field, '') for field in available_fields]
            cursor.execute(insert_sql, values)
            count += 1
            
            # Log progress for large files
            if count % 10000 == 0:
                logger.info(f"Imported {count} records...")
    
    return count

def _import_relationships(cursor, csv_path: str, terminology_type: str) -> int:
    """
    Imports relationship data from a CSV file.
    
    Args:
        cursor: Database cursor
        csv_path: Path to the CSV file
        terminology_type: Type of terminology (snomed, rxnorm)
        
    Returns:
        Count of imported records
    """
    # Expected fields in the relationships CSV
    expected_fields = ['source_code', 'destination_code', 'relationship_type', 'is_active']
    
    # Verify CSV has required fields
    available_fields = []
    with open(csv_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        if reader.fieldnames:
            available_fields = [f for f in expected_fields if f in reader.fieldnames]
    
    if not set(['source_code', 'destination_code', 'relationship_type']).issubset(set(available_fields)):
        raise ValueError(f"CSV file missing required fields for relationships: {csv_path}")
    
    # Determine the table name based on terminology type
    table_name = f"{terminology_type}_relationships"
    
    # Prepare SQL statement
    placeholders = ', '.join(['?'] * len(available_fields))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(available_fields)}) VALUES ({placeholders})"
    
    # Import data
    count = 0
    
    # Begin transaction
    cursor.execute('BEGIN TRANSACTION')
    
    with open(csv_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            values = [row.get(field, '') for field in available_fields]
            
            # Skip if source or destination code is empty
            if not values[0] or not values[1]:
                continue
                
            try:
                cursor.execute(insert_sql, values)
                count += 1
                
                # Log progress for large files
                if count % 10000 == 0:
                    logger.info(f"Imported {count} relationship records...")
            except sqlite3.IntegrityError as e:
                # Log and continue if relationship references non-existent concepts
                logger.warning(f"Skipping relationship: {values[0]} -> {values[1]} ({values[2]}): {e}")
    
    return count
    
def _import_snomed_relationships(cursor, csv_path: str) -> int:
    """
    Imports SNOMED CT relationship data from a CSV file.
    
    Args:
        cursor: Database cursor
        csv_path: Path to the CSV file
        
    Returns:
        Count of imported records
    """
    return _import_relationships(cursor, csv_path, "snomed")
    
def _import_rxnorm_relationships(cursor, csv_path: str) -> int:
    """
    Imports RxNorm relationship data from a CSV file.
    
    Args:
        cursor: Database cursor
        csv_path: Path to the CSV file
        
    Returns:
        Count of imported records
    """
    return _import_relationships(cursor, csv_path, "rxnorm")

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
            {'type': 'snomed', 'files': {
                'concepts': 'snomed_sample.csv',
                'relationships': 'snomed_relationships_sample.csv'
            }},
            {'type': 'loinc', 'files': {
                'concepts': 'loinc_sample.csv',
                'parts': 'loinc_parts_sample.csv',
                'concept_parts': 'loinc_concept_parts_sample.csv',
                'hierarchy': 'loinc_hierarchy_sample.csv'
            }},
            {'type': 'rxnorm', 'files': {
                'concepts': 'rxnorm_sample.csv',
                'relationships': 'rxnorm_relationships_sample.csv'
            }}
        ]
        
        for term in terminologies:
            db_path = os.path.join(data_dir, f"{term['type']}_core.sqlite")
            
            # Remove any existing database to ensure clean creation
            if os.path.exists(db_path):
                os.remove(db_path)
                logger.info(f"Removed existing {term['type']} database for clean creation")
            
            # Create empty database with full schema
            logger.info(f"Creating sample {term['type']} database...")
            create_empty_database(db_path, term['type'])
            
            # Verify that all necessary tables were created
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check for relationships table
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{term['type']}_relationships'")
            has_rel_table = cursor.fetchone() is not None
            
            # For LOINC, check for the LOINC-specific tables
            if term['type'] == 'loinc':
                # LOINC parts table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='loinc_parts'")
                has_parts_table = cursor.fetchone() is not None
                if not has_parts_table:
                    logger.info("Creating loinc_parts table...")
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS loinc_parts (
                        id INTEGER PRIMARY KEY,
                        part_number TEXT NOT NULL,
                        part_name TEXT NOT NULL,
                        part_display_name TEXT NOT NULL,
                        part_type TEXT NOT NULL,
                        status TEXT DEFAULT 'ACTIVE'
                    )
                    ''')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_part_number ON loinc_parts(part_number)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_part_type ON loinc_parts(part_type)')
                    conn.commit()
                
                # LOINC concept-parts mapping table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='loinc_concept_parts'")
                has_concept_parts_table = cursor.fetchone() is not None
                if not has_concept_parts_table:
                    logger.info("Creating loinc_concept_parts table...")
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS loinc_concept_parts (
                        id INTEGER PRIMARY KEY,
                        loinc_code TEXT NOT NULL,
                        part_number TEXT NOT NULL,
                        part_type TEXT NOT NULL,
                        FOREIGN KEY (loinc_code) REFERENCES loinc_concepts(code),
                        FOREIGN KEY (part_number) REFERENCES loinc_parts(part_number)
                    )
                    ''')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_concept_parts_code ON loinc_concept_parts(loinc_code)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_concept_parts_part ON loinc_concept_parts(part_number)')
                    conn.commit()
                
                # LOINC hierarchy table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='loinc_hierarchy'")
                has_hierarchy_table = cursor.fetchone() is not None
                if not has_hierarchy_table:
                    logger.info("Creating loinc_hierarchy table...")
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS loinc_hierarchy (
                        id INTEGER PRIMARY KEY,
                        parent_code TEXT NOT NULL,
                        child_code TEXT NOT NULL,
                        hierarchy_type TEXT NOT NULL,
                        FOREIGN KEY (parent_code) REFERENCES loinc_concepts(code),
                        FOREIGN KEY (child_code) REFERENCES loinc_concepts(code)
                    )
                    ''')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_hierarchy_parent ON loinc_hierarchy(parent_code)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_hierarchy_child ON loinc_hierarchy(child_code)')
                    conn.commit()
                
                # Check if loinc_concepts table needs to be expanded
                cursor.execute("PRAGMA table_info(loinc_concepts)")
                columns = [row[1] for row in cursor.fetchall()]
                
                expected_columns = ['id', 'code', 'term', 'display', 'component', 'property', 'time', 'system', 
                                  'scale', 'method', 'long_common_name', 'class', 'version_last_changed', 
                                  'status', 'consumer_name', 'classtype', 'order_obs']
                
                missing_columns = [col for col in expected_columns if col not in columns]
                
                if missing_columns:
                    logger.info(f"Updating LOINC concepts table with missing columns: {missing_columns}")
                    
                    # Add missing columns one by one
                    for col in missing_columns:
                        col_type = "TEXT"  # Default type
                        cursor.execute(f"ALTER TABLE loinc_concepts ADD COLUMN {col} {col_type}")
                        
                    # Add indexes for commonly searched columns
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_component ON loinc_concepts(component)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_system ON loinc_concepts(system)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_class ON loinc_concepts(class)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loinc_order_obs ON loinc_concepts(order_obs)')
                    
                    conn.commit()
            
            # If relationships table wasn't created, there's an issue with the schema
            if not has_rel_table and term['type'] != 'loinc':
                logger.error(f"CRITICAL: {term['type']}_relationships table was not created in schema")
                
                # Manually create relationships table for RxNorm if needed
                if term['type'] == 'rxnorm':
                    logger.info(f"Manually creating rxnorm_relationships table...")
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rxnorm_relationships (
                        id INTEGER PRIMARY KEY,
                        source_code TEXT NOT NULL,
                        destination_code TEXT NOT NULL,
                        relationship_type TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1,
                        FOREIGN KEY (source_code) REFERENCES rxnorm_concepts(code),
                        FOREIGN KEY (destination_code) REFERENCES rxnorm_concepts(code)
                    )
                    ''')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_rel_source ON rxnorm_relationships(source_code)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_rel_dest ON rxnorm_relationships(destination_code)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_rel_type ON rxnorm_relationships(relationship_type)')
                    conn.commit()
                    logger.info(f"Manually created rxnorm_relationships table successfully")
            
            # Check all columns for rxnorm_concepts
            if term['type'] == 'rxnorm':
                cursor.execute("PRAGMA table_info(rxnorm_concepts)")
                columns = [row[1] for row in cursor.fetchall()]
                
                expected_columns = ['id', 'code', 'term', 'display', 'tty', 'brand_name', 
                                   'ingredient', 'strength', 'dose_form', 'route', 'ndc', 
                                   'atc', 'is_active']
                
                missing_columns = [col for col in expected_columns if col not in columns]
                
                if missing_columns:
                    logger.error(f"Missing RxNorm columns: {missing_columns}")
                    
                    # Recreate with all columns
                    cursor.execute("DROP TABLE IF EXISTS rxnorm_concepts")
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rxnorm_concepts (
                        id INTEGER PRIMARY KEY,
                        code TEXT NOT NULL,
                        term TEXT NOT NULL,
                        display TEXT NOT NULL,
                        tty TEXT,
                        brand_name TEXT,
                        ingredient TEXT,
                        strength TEXT,
                        dose_form TEXT,
                        route TEXT,
                        ndc TEXT,
                        atc TEXT,
                        is_active INTEGER DEFAULT 1
                    )
                    ''')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_term ON rxnorm_concepts(term)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_code ON rxnorm_concepts(code)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_ingredient ON rxnorm_concepts(ingredient)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rxnorm_brand ON rxnorm_concepts(brand_name)')
                    conn.commit()
                    logger.info(f"Recreated rxnorm_concepts table with all required columns")
            
            conn.close()
            
            # Import concepts
            concept_path = os.path.join(sample_dir, term['files']['concepts'])
            if os.path.exists(concept_path):
                concept_count = import_from_csv(concept_path, db_path, term['type'], 'concepts')
                logger.info(f"Imported {concept_count} {term['type']} concepts")
            else:
                logger.warning(f"Sample concepts file not found: {concept_path}")
            
            # For LOINC data, handle parts and hierarchy files
            if term['type'] == 'loinc':
                # Import LOINC parts if available
                if 'parts' in term['files']:
                    parts_path = os.path.join(sample_dir, term['files']['parts'])
                    if os.path.exists(parts_path):
                        try:
                            # Import parts
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            
                            # Clear existing data
                            cursor.execute("DELETE FROM loinc_parts")
                            
                            # Import parts
                            count = 0
                            with open(parts_path, 'r') as f:
                                reader = csv.reader(f)
                                # Skip header
                                next(reader, None)
                                
                                for row in reader:
                                    if len(row) >= 4:
                                        cursor.execute(
                                            """INSERT INTO loinc_parts 
                                               (part_number, part_name, part_display_name, part_type) 
                                               VALUES (?, ?, ?, ?)""",
                                            (row[0], row[1], row[2], row[3])
                                        )
                                        count += 1
                            
                            conn.commit()
                            conn.close()
                            logger.info(f"Imported {count} LOINC parts")
                        except Exception as e:
                            logger.error(f"Error importing LOINC parts: {e}")
                
                # Import LOINC concept-parts mapping if available
                if 'concept_parts' in term['files']:
                    concept_parts_path = os.path.join(sample_dir, term['files']['concept_parts'])
                    if os.path.exists(concept_parts_path):
                        try:
                            # Import concept-parts mapping
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            
                            # Clear existing data
                            cursor.execute("DELETE FROM loinc_concept_parts")
                            
                            # Import mapping
                            count = 0
                            with open(concept_parts_path, 'r') as f:
                                reader = csv.reader(f)
                                # Skip header
                                next(reader, None)
                                
                                for row in reader:
                                    if len(row) >= 3:
                                        try:
                                            cursor.execute(
                                                """INSERT INTO loinc_concept_parts 
                                                   (loinc_code, part_number, part_type) 
                                                   VALUES (?, ?, ?)""",
                                                (row[0], row[1], row[2])
                                            )
                                            count += 1
                                        except sqlite3.IntegrityError:
                                            # Skip if reference integrity fails
                                            pass
                            
                            conn.commit()
                            conn.close()
                            logger.info(f"Imported {count} LOINC concept-part mappings")
                        except Exception as e:
                            logger.error(f"Error importing LOINC concept-parts mapping: {e}")
                
                # Import LOINC hierarchy if available
                if 'hierarchy' in term['files']:
                    hierarchy_path = os.path.join(sample_dir, term['files']['hierarchy'])
                    if os.path.exists(hierarchy_path):
                        try:
                            # Import hierarchy
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            
                            # Clear existing data
                            cursor.execute("DELETE FROM loinc_hierarchy")
                            
                            # Import hierarchy
                            count = 0
                            with open(hierarchy_path, 'r') as f:
                                reader = csv.reader(f)
                                # Skip header
                                next(reader, None)
                                
                                for row in reader:
                                    if len(row) >= 3:
                                        try:
                                            cursor.execute(
                                                """INSERT INTO loinc_hierarchy 
                                                   (parent_code, child_code, hierarchy_type) 
                                                   VALUES (?, ?, ?)""",
                                                (row[0], row[1], row[2])
                                            )
                                            count += 1
                                        except sqlite3.IntegrityError:
                                            # Skip if reference integrity fails
                                            pass
                            
                            conn.commit()
                            conn.close()
                            logger.info(f"Imported {count} LOINC hierarchy relationships")
                        except Exception as e:
                            logger.error(f"Error importing LOINC hierarchy: {e}")
            
            # Import relationships if available
            if 'relationships' in term['files']:
                rel_path = os.path.join(sample_dir, term['files']['relationships'])
                
                if os.path.exists(rel_path):
                    try:
                        rel_count = import_from_csv(rel_path, db_path, term['type'], 'relationships')
                        logger.info(f"Imported {rel_count} {term['type']} relationships")
                    except Exception as e:
                        logger.error(f"Error importing relationships from file: {e}")
                        
                        # Try to create sample relationships if import failed
                        if term['type'] == 'snomed':
                            rel_count = _create_sample_snomed_relationships(db_path)
                            logger.info(f"Created {rel_count} sample {term['type']} relationships")
                        elif term['type'] == 'rxnorm':
                            rel_count = _create_sample_rxnorm_relationships(db_path)
                            logger.info(f"Created {rel_count} sample {term['type']} relationships")
                else:
                    logger.warning(f"Relationship file not found: {rel_path}")
                    
                    # Create sample relationships if file doesn't exist
                    if term['type'] == 'snomed':
                        rel_count = _create_sample_snomed_relationships(db_path)
                        logger.info(f"Created {rel_count} sample {term['type']} relationships")
                    elif term['type'] == 'rxnorm':
                        rel_count = _create_sample_rxnorm_relationships(db_path)
                        logger.info(f"Created {rel_count} sample {term['type']} relationships")
        
        logger.info('Sample databases creation completed')
    except Exception as e:
        logger.error(f"Error creating sample databases: {e}")
        raise

def _create_sample_rxnorm_relationships(db_path: str) -> int:
    """
    Creates sample RxNorm relationships based on existing concepts.
    
    Args:
        db_path: Path to the RxNorm database
        
    Returns:
        Count of relationships created
    """
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing concepts
        cursor.execute("SELECT code, term, display FROM rxnorm_concepts")
        concepts = cursor.fetchall()
        
        if not concepts or len(concepts) < 3:
            logger.warning("Not enough concepts to create sample relationships")
            return 0
        
        # Define drug to ingredient mappings with brand names
        medication_data = [
            {
                'ingredient_code': '6809',         # metformin
                'ingredient_name': 'metformin',
                'brand_code': '1226211',           # fictional code for Glucophage
                'brand_name': 'Glucophage',
                'strength': '500mg',
                'form': 'tablet'
            },
            {
                'ingredient_code': '29046',        # lisinopril
                'ingredient_name': 'lisinopril',
                'brand_code': '1226212',           # fictional code for Zestril
                'brand_name': 'Zestril',
                'strength': '10mg',
                'form': 'tablet'
            },
            {
                'ingredient_code': '1191',         # aspirin
                'ingredient_name': 'aspirin',
                'brand_code': '1226213',           # fictional code for Bayer
                'brand_name': 'Bayer',
                'strength': '325mg',
                'form': 'tablet'
            },
            {
                'ingredient_code': '4053',         # atorvastatin
                'ingredient_name': 'atorvastatin',
                'brand_code': '1226214',           # fictional code for Lipitor
                'brand_name': 'Lipitor',
                'strength': '20mg',
                'form': 'tablet'
            },
            {
                'ingredient_code': '3640',         # amlodipine
                'ingredient_name': 'amlodipine',
                'brand_code': '1226215',           # fictional code for Norvasc
                'brand_name': 'Norvasc',
                'strength': '5mg',
                'form': 'tablet'
            }
        ]
        
        # Create brand name concepts if they don't exist
        for med in medication_data:
            cursor.execute(
                "SELECT 1 FROM rxnorm_concepts WHERE code = ?", 
                (med['brand_code'],)
            )
            if not cursor.fetchone():
                # Insert brand name concept
                cursor.execute(
                    """INSERT INTO rxnorm_concepts 
                       (code, term, display, tty, brand_name, ingredient, strength, dose_form, is_active) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                    (
                        med['brand_code'], 
                        med['brand_name'], 
                        f"{med['brand_name']} {med['strength']} {med['form']}", 
                        "BN",                       # Brand Name 
                        med['brand_name'], 
                        med['ingredient_name'], 
                        med['strength'], 
                        med['form']
                    )
                )
        
        # Create relationships between ingredients and brand names
        count = 0
        for med in medication_data:
            # Check if ingredient exists
            cursor.execute("SELECT 1 FROM rxnorm_concepts WHERE code = ?", (med['ingredient_code'],))
            has_ingredient = cursor.fetchone()
            
            # Check if brand exists
            cursor.execute("SELECT 1 FROM rxnorm_concepts WHERE code = ?", (med['brand_code'],))
            has_brand = cursor.fetchone()
            
            if has_ingredient and has_brand:
                # Add brand name has ingredient relationship
                cursor.execute(
                    """INSERT INTO rxnorm_relationships 
                       (source_code, destination_code, relationship_type, is_active) 
                       VALUES (?, ?, ?, 1)""",
                    (med['brand_code'], med['ingredient_code'], "has_ingredient")
                )
                count += 1
                
                # Add ingredient of brand relationship (inverse)
                cursor.execute(
                    """INSERT INTO rxnorm_relationships 
                       (source_code, destination_code, relationship_type, is_active) 
                       VALUES (?, ?, ?, 1)""",
                    (med['ingredient_code'], med['brand_code'], "ingredient_of")
                )
                count += 1
        
        # Create combination products
        combo_meds = [
            {
                'combo_code': '1226216',           # fictional code for lisinopril-hctz
                'combo_name': 'lisinopril-hydrochlorothiazide',
                'brand_name': 'Zestoretic',
                'ingredients': [
                    {'code': '29046', 'name': 'lisinopril'},           # lisinopril
                    {'code': '5487', 'name': 'hydrochlorothiazide'}    # fictional code for HCTZ
                ],
                'strength': '10-12.5mg',
                'form': 'tablet'
            },
            {
                'combo_code': '1226217',           # fictional code for amlodipine-benazepril
                'combo_name': 'amlodipine-benazepril',
                'brand_name': 'Lotrel',
                'ingredients': [
                    {'code': '3640', 'name': 'amlodipine'},            # amlodipine
                    {'code': '1746', 'name': 'benazepril'}             # fictional code for benazepril
                ],
                'strength': '5-10mg',
                'form': 'capsule'
            }
        ]
        
        # Create HCTZ and benazepril if they don't exist
        for ingredient_code, ingredient_name in [('5487', 'hydrochlorothiazide'), ('1746', 'benazepril')]:
            cursor.execute("SELECT 1 FROM rxnorm_concepts WHERE code = ?", (ingredient_code,))
            if not cursor.fetchone():
                cursor.execute(
                    """INSERT INTO rxnorm_concepts 
                       (code, term, display, tty, ingredient, is_active) 
                       VALUES (?, ?, ?, ?, ?, 1)""",
                    (ingredient_code, ingredient_name, ingredient_name, "IN", ingredient_name)
                )
        
        # Create combination products and relationships
        for combo in combo_meds:
            # Create combination product concept
            cursor.execute("SELECT 1 FROM rxnorm_concepts WHERE code = ?", (combo['combo_code'],))
            if not cursor.fetchone():
                cursor.execute(
                    """INSERT INTO rxnorm_concepts 
                       (code, term, display, tty, brand_name, ingredient, strength, dose_form, is_active) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                    (
                        combo['combo_code'], 
                        combo['combo_name'], 
                        f"{combo['brand_name']} {combo['strength']} {combo['form']}", 
                        "SCD",                      # Standard Clinical Drug 
                        combo['brand_name'], 
                        combo['combo_name'], 
                        combo['strength'], 
                        combo['form']
                    )
                )
            
            # Create relationships between combo and ingredients
            for ingredient in combo['ingredients']:
                cursor.execute("SELECT 1 FROM rxnorm_concepts WHERE code = ?", (ingredient['code'],))
                if cursor.fetchone():
                    # Add combo has ingredient relationship
                    cursor.execute(
                        """INSERT INTO rxnorm_relationships 
                           (source_code, destination_code, relationship_type, is_active) 
                           VALUES (?, ?, ?, 1)""",
                        (combo['combo_code'], ingredient['code'], "has_ingredient")
                    )
                    count += 1
                    
                    # Add ingredient of combo relationship (inverse)
                    cursor.execute(
                        """INSERT INTO rxnorm_relationships 
                           (source_code, destination_code, relationship_type, is_active) 
                           VALUES (?, ?, ?, 1)""",
                        (ingredient['code'], combo['combo_code'], "ingredient_of")
                    )
                    count += 1
        
        # Create common relationships based on administration route
        route_relationships = [
            {
                'source_code': '1191',     # aspirin
                'route_code': '1226220',   # fictional code for oral route
                'route_name': 'Oral'
            },
            {
                'source_code': '29046',    # lisinopril
                'route_code': '1226220',   # oral route
                'route_name': 'Oral'
            },
            {
                'source_code': '7646',     # naproxen
                'route_code': '1226220',   # oral route
                'route_name': 'Oral'
            }
        ]
        
        # Create routes if they don't exist
        cursor.execute("SELECT 1 FROM rxnorm_concepts WHERE code = ?", ('1226220',))
        if not cursor.fetchone():
            cursor.execute(
                """INSERT INTO rxnorm_concepts 
                   (code, term, display, tty, is_active) 
                   VALUES (?, ?, ?, ?, 1)""",
                ('1226220', 'Oral', 'Oral route of administration', 'ROA', 1)  # Route of Administration
            )
        
        # Create relationships for routes
        for route_rel in route_relationships:
            cursor.execute("SELECT 1 FROM rxnorm_concepts WHERE code = ?", (route_rel['source_code'],))
            if cursor.fetchone():
                cursor.execute(
                    """INSERT INTO rxnorm_relationships 
                       (source_code, destination_code, relationship_type, is_active) 
                       VALUES (?, ?, ?, 1)""",
                    (route_rel['source_code'], route_rel['route_code'], "has_route")
                )
                count += 1
        
        # Update ingredient fields for existing concepts
        for concept_code, ingredient_name in [
            ('6809', 'metformin'),
            ('29046', 'lisinopril'),
            ('1191', 'aspirin'),
            ('4053', 'atorvastatin'),
            ('3640', 'amlodipine'),
            ('10582', 'losartan'),
            ('42316', 'montelukast'),
            ('7646', 'naproxen'),
            ('8163', 'omeprazole')
        ]:
            cursor.execute(
                """UPDATE rxnorm_concepts 
                   SET ingredient = ?, tty = 'IN' 
                   WHERE code = ?""",
                (ingredient_name, concept_code)
            )
        
        # Commit changes
        conn.commit()
        conn.close()
        
        return count
    except Exception as e:
        logger.error(f"Error creating sample RxNorm relationships: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return 0

def _create_sample_snomed_relationships(db_path: str) -> int:
    """
    Creates sample SNOMED CT relationships based on existing concepts.
    
    Args:
        db_path: Path to the SNOMED CT database
        
    Returns:
        Count of relationships created
    """
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing concepts
        cursor.execute("SELECT code, display FROM snomed_concepts")
        concepts = cursor.fetchall()
        
        if not concepts or len(concepts) < 2:
            logger.warning("Not enough concepts to create sample relationships")
            return 0
        
        # Define relationship types
        rel_types = [
            "116680003",  # Is-a
            "363698007",  # Finding site
            "42752001",   # Due to
            "47429007"    # Associated with
        ]
        
        # Create some sample hierarchical relationships
        relationships = []
        
        # Define hierarchical relationships (parent-child)
        hierarchy = {
            # General disease categories with specific diseases
            "235856003": ["422034002"],  # Liver disease (parent) -> Diabetic neuropathy (child)
            "73211009": ["44054006", "422034002"],  # Diabetes mellitus -> Type 2 diabetes, Diabetic neuropathy
            "235856003": ["73211009"],  # Liver disease -> Diabetes mellitus
            
            # Cardiovascular disorders
            "49436004": ["38341003"],  # Atrial fibrillation -> Hypertension
            
            # Respiratory disorders
            "13645005": ["8098009"],  # COPD -> Asthma
            
            # Neurological disorders
            "24700007": ["57406009", "84757009"],  # Multiple sclerosis -> Migraine, Epilepsy
            
            # Mental health
            "35489007": ["57406009"]  # Depressive disorder -> Migraine
        }
        
        # Create relationships based on defined hierarchy
        count = 0
        for parent, children in hierarchy.items():
            for child in children:
                # Check that both parent and child exist in the database
                cursor.execute("SELECT 1 FROM snomed_concepts WHERE code = ?", (parent,))
                if not cursor.fetchone():
                    continue
                    
                cursor.execute("SELECT 1 FROM snomed_concepts WHERE code = ?", (child,))
                if not cursor.fetchone():
                    continue
                
                # Add the is-a relationship
                cursor.execute(
                    "INSERT INTO snomed_relationships (source_code, destination_code, relationship_type, is_active) VALUES (?, ?, ?, 1)",
                    (child, parent, "116680003")  # Child is-a Parent
                )
                count += 1
        
        # Create some finding site relationships (disorder to body structure)
        finding_sites = {
            "38341003": "27175008",  # Hypertension -> Entire vascular system
            "49436004": "80891009",  # Atrial fibrillation -> Heart structure
            "8098009": "39607008",   # Asthma -> Lung structure
            "57406009": "12738006",  # Migraine -> Brain structure
            "85828009": "87642003"   # Rheumatoid arthritis -> Joint structure
        }
        
        # Insert hardcoded body structure concepts for the finding sites
        body_structures = [
            ("27175008", "Entire vascular system", "Entire vascular system (body structure)", "body structure", 1),
            ("80891009", "Heart structure", "Heart structure (body structure)", "body structure", 1),
            ("39607008", "Lung structure", "Lung structure (body structure)", "body structure", 1),
            ("12738006", "Brain structure", "Brain structure (body structure)", "body structure", 1),
            ("87642003", "Joint structure", "Joint structure (body structure)", "body structure", 1)
        ]
        
        for structure in body_structures:
            cursor.execute(
                "INSERT OR IGNORE INTO snomed_concepts (code, term, display, concept_type, is_active) VALUES (?, ?, ?, ?, ?)",
                structure
            )
        
        # Create finding site relationships
        for disorder, site in finding_sites.items():
            # Check that disorder exists
            cursor.execute("SELECT 1 FROM snomed_concepts WHERE code = ?", (disorder,))
            if not cursor.fetchone():
                continue
            
            # Add the finding site relationship
            cursor.execute(
                "INSERT INTO snomed_relationships (source_code, destination_code, relationship_type, is_active) VALUES (?, ?, ?, 1)",
                (disorder, site, "363698007")  # Disorder finding_site Body_Structure
            )
            count += 1
        
        # Create some "due to" and "associated with" relationships
        causal_relationships = [
            # disorder1 "due to" disorder2
            ("422034002", "44054006", "42752001"),  # Diabetic neuropathy due to Type 2 diabetes
            
            # disorder1 "associated with" disorder2
            ("49436004", "38341003", "47429007"),  # Atrial fibrillation associated with Hypertension
            ("57406009", "35489007", "47429007")   # Migraine associated with Depressive disorder
        ]
        
        for source, dest, rel_type in causal_relationships:
            # Check that both concepts exist
            cursor.execute("SELECT 1 FROM snomed_concepts WHERE code = ?", (source,))
            if not cursor.fetchone():
                continue
                
            cursor.execute("SELECT 1 FROM snomed_concepts WHERE code = ?", (dest,))
            if not cursor.fetchone():
                continue
            
            # Add the relationship
            cursor.execute(
                "INSERT INTO snomed_relationships (source_code, destination_code, relationship_type, is_active) VALUES (?, ?, ?, 1)",
                (source, dest, rel_type)
            )
            count += 1
        
        # Commit changes
        conn.commit()
        conn.close()
        
        return count
    except Exception as e:
        logger.error(f"Error creating sample relationships: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return 0

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