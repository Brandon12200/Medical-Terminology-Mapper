#!/usr/bin/env python
"""
Test script for database functionality only.
"""

import os
import sys
import logging
from app.utils.logger import setup_logger
from app.standards.terminology.embedded_db import EmbeddedDatabaseManager

# Configure logging
logger = setup_logger("test_db_only")

def main():
    print("\n=== Medical Terminology Mapper - Database Test ===\n")
    
    # Initialize database manager
    logger.info("Initializing database manager")
    db_manager = EmbeddedDatabaseManager()
    
    try:
        # Connect to the databases
        if db_manager.connect():
            logger.info("Connected to terminology databases")
            print("Successfully connected to terminology databases.")
            
            # Get database statistics
            stats = db_manager.get_statistics()
            print(f"\nDatabase statistics:")
            print(f"SNOMED concepts: {stats['snomed']['count']}")
            print(f"LOINC concepts: {stats['loinc']['count']}")
            print(f"RxNorm concepts: {stats['rxnorm']['count']}")
            print(f"Custom mappings: {sum(stats['custom'].values())}")
            
            # Test a couple of lookups
            print("\nTesting basic lookups:")
            
            term = "hypertension"
            result = db_manager.lookup_snomed(term)
            if result:
                print(f"  Found SNOMED term '{term}': {result['code']} - {result['display']}")
            else:
                print(f"  Could not find SNOMED term '{term}'")
            
            term = "hemoglobin a1c"
            result = db_manager.lookup_loinc(term)
            if result:
                print(f"  Found LOINC term '{term}': {result['code']} - {result['display']}")
            else:
                print(f"  Could not find LOINC term '{term}'")
            
            print("\nDatabase test completed successfully!")
            return 0
        else:
            logger.error("Failed to connect to terminology databases")
            print("Error: Failed to connect to terminology databases.")
            return 1
            
    except Exception as e:
        logger.error(f"Error in database test: {e}")
        print(f"Error: {e}")
        return 1
    finally:
        # Always close the connection
        try:
            db_manager.close()
            logger.info("Database connections closed")
        except:
            pass

if __name__ == "__main__":
    sys.exit(main())