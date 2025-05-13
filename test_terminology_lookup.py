#!/usr/bin/env python
"""
Test script to demonstrate terminology lookup functionality.

This script shows how to use the EmbeddedDatabaseManager to look up
medical terms in the SNOMED CT, LOINC, and RxNorm databases.
"""

import os
import sys
import json
from typing import Dict, Any, Optional

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from app modules
from app.utils.logger import setup_logger
from app.standards.terminology.embedded_db import EmbeddedDatabaseManager

# Configure logging
logger = setup_logger("test_terminology_lookup", 
                     log_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                          "logs", "test_terminology_lookup.log"))

def print_result(term: str, result: Optional[Dict[str, Any]], system: str) -> None:
    """Print the result of a terminology lookup in a readable format."""
    print(f"\nLooking up '{term}' in {system}:")
    if result:
        print(f"  Found: {result.get('found', False)}")
        print(f"  Code: {result.get('code', 'N/A')}")
        print(f"  Display: {result.get('display', 'N/A')}")
        print(f"  System: {result.get('system', 'N/A')}")
        if 'confidence' in result:
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
    else:
        print(f"  No mapping found for '{term}' in {system}")

def main() -> None:
    """Run terminology lookup tests."""
    print("\n=== Medical Terminology Mapper - Lookup Demo ===\n")
    
    # Initialize the database manager
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "terminology")
    db_manager = EmbeddedDatabaseManager(data_dir)
    
    # Connect to the databases
    if not db_manager.connect():
        logger.error("Failed to connect to terminology databases")
        print("Error: Failed to connect to the terminology databases")
        return
    
    # Test various term lookups
    test_terms = [
        # SNOMED CT terms
        {"term": "hypertension", "system": "snomed"},
        {"term": "diabetes mellitus", "system": "snomed"},
        {"term": "migraine", "system": "snomed"},
        {"term": "unknown disease", "system": "snomed"},
        
        # LOINC terms
        {"term": "hemoglobin a1c", "system": "loinc"},
        {"term": "blood glucose", "system": "loinc"},
        {"term": "white blood cell count", "system": "loinc"},
        {"term": "unknown lab test", "system": "loinc"},
        
        # RxNorm terms
        {"term": "metformin", "system": "rxnorm"},
        {"term": "lisinopril", "system": "rxnorm"},
        {"term": "aspirin", "system": "rxnorm"},
        {"term": "unknown medication", "system": "rxnorm"}
    ]
    
    # Perform the lookups
    for test in test_terms:
        term = test["term"]
        system = test["system"]
        
        result = None
        if system == "snomed":
            result = db_manager.lookup_snomed(term)
        elif system == "loinc":
            result = db_manager.lookup_loinc(term)
        elif system == "rxnorm":
            result = db_manager.lookup_rxnorm(term)
        
        print_result(term, result, system)
    
    # Print database statistics
    stats = db_manager.get_statistics()
    print("\n=== Database Statistics ===\n")
    print(json.dumps(stats, indent=2))
    
    # Close the database connections
    db_manager.close()
    print("\nTest completed. Database connections closed.")

if __name__ == "__main__":
    main()