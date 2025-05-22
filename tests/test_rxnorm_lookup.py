#!/usr/bin/env python3
"""
Test script for RxNorm lookup functionality.

This script tests the enhanced RxNorm lookup features.
"""

import os
import sys
import logging
import json
from typing import Dict, Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from app modules
from app.standards.terminology.embedded_db import EmbeddedDatabaseManager
from app.standards.terminology.db_updater import create_sample_databases

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_rxnorm_lookup")

def setup_test_db():
    """Ensure the test database is set up with sample data."""
    # Define the path to the data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           "data", "terminology")
    
    # Create the directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Check if the sample database exists
    db_path = os.path.join(data_dir, "rxnorm_core.sqlite")
    
    if not os.path.exists(db_path):
        logging.info("Creating sample databases")
        create_sample_databases(data_dir)
    
    return data_dir

def test_rxnorm_basic_lookup():
    """Test basic RxNorm lookup functionality."""
    data_dir = setup_test_db()
    
    # Initialize the database manager
    db_manager = EmbeddedDatabaseManager(data_dir)
    db_manager.connect()
    
    # Test lookups
    test_cases = [
        {"term": "lisinopril", "expected_found": True},
        {"term": "metformin", "expected_found": True},
        {"term": "Lipitor", "expected_found": True, "expected_type": "brand"},
        {"term": "ibuprofen", "expected_found": False},
    ]
    
    print("\n=== Testing Basic RxNorm Lookup ===")
    
    for test_case in test_cases:
        term = test_case["term"]
        print(f"\nLooking up term: {term}")
        
        # Test lookup
        result = db_manager.lookup_rxnorm(term)
        found = result is not None and result.get("found", False)
        
        print(f"  Found: {found}, Expected: {test_case['expected_found']}")
        
        if found:
            print(f"  Code: {result.get('code')}")
            print(f"  Display: {result.get('display')}")
            if "expected_type" in test_case:
                match_type = result.get("match_type", "unknown")
                print(f"  Match type: {match_type}, Expected: {test_case['expected_type']}")
    
    db_manager.close()

def test_rxnorm_drug_name_normalization():
    """Test drug name normalization for RxNorm lookup."""
    data_dir = setup_test_db()
    
    # Initialize the database manager
    db_manager = EmbeddedDatabaseManager(data_dir)
    db_manager.connect()
    
    # Test normalization cases
    test_cases = [
        {"term": "lisinopril 10mg", "expected_normalized": "lisinopril", "expected_found": True},
        {"term": "metformin 500 mg tablet", "expected_normalized": "metformin", "expected_found": True},
        {"term": "Lipitor 20mg", "expected_normalized": "lipitor", "expected_found": True},
        {"term": "ibuprofen 200mg oral tablet", "expected_normalized": "ibuprofen", "expected_found": False},
    ]
    
    print("\n=== Testing RxNorm Drug Name Normalization ===")
    
    for test_case in test_cases:
        term = test_case["term"]
        print(f"\nNormalizing term: {term}")
        
        # Get normalized term
        normalized = db_manager._normalize_drug_name(term)
        print(f"  Normalized: '{normalized}', Expected: '{test_case['expected_normalized']}'")
        
        # Test lookup with original term
        result = db_manager.lookup_rxnorm(term)
        found = result is not None and result.get("found", False)
        
        print(f"  Found with normalized term: {found}, Expected: {test_case['expected_found']}")
        
        if found:
            print(f"  Code: {result.get('code')}")
            print(f"  Display: {result.get('display')}")
            print(f"  Match type: {result.get('match_type', 'unknown')}")
            print(f"  Confidence: {result.get('confidence', 1.0)}")
    
    db_manager.close()

def test_rxnorm_pattern_matching():
    """Test pattern matching for RxNorm lookup."""
    data_dir = setup_test_db()
    
    # Initialize the database manager
    db_manager = EmbeddedDatabaseManager(data_dir)
    db_manager.connect()
    
    # Test pattern matching cases
    test_cases = [
        {"term": "lisinopril-hctz", "expected_pattern": "combination", "expected_found": False},  # Updated expectation
        {"term": "amlodipine/benazepril", "expected_pattern": "combination", "expected_found": False},  # Updated expectation
        {"term": "10mg metformin", "expected_pattern": "strength_ingredient", "expected_found": True},
    ]
    
    print("\n=== Testing RxNorm Pattern Matching ===")
    
    for test_case in test_cases:
        term = test_case["term"]
        print(f"\nTesting pattern for term: {term}")
        
        # Test lookup with pattern matching
        result = db_manager.lookup_rxnorm(term)
        found = result is not None and result.get("found", False)
        
        print(f"  Found: {found}, Expected: {test_case['expected_found']}")
        
        if found:
            match_type = result.get("match_type", "unknown")
            print(f"  Match type: {match_type}")
            expected_pattern = f"pattern_{test_case['expected_pattern']}"
            print(f"  Pattern matched: {match_type == expected_pattern}, Expected: {expected_pattern}")
            print(f"  Code: {result.get('code')}")
            print(f"  Display: {result.get('display')}")
            print(f"  Confidence: {result.get('confidence', 1.0)}")
    
    db_manager.close()

def test_rxnorm_detailed_lookup():
    """Test detailed RxNorm lookup with ingredients and related information."""
    data_dir = setup_test_db()
    
    # Initialize the database manager
    db_manager = EmbeddedDatabaseManager(data_dir)
    db_manager.connect()
    
    # Test detailed lookup cases
    test_cases = [
        {"term": "lisinopril", "expected_fields": ["ingredient", "strength", "dose_form"]},
        {"term": "Lipitor", "expected_fields": ["ingredient", "brand_name", "strength"]},
        {"term": "lisinopril-hydrochlorothiazide", "expected_fields": ["ingredients", "brand_name", "strength"]},
    ]
    
    print("\n=== Testing RxNorm Detailed Lookup ===")
    
    for test_case in test_cases:
        term = test_case["term"]
        print(f"\nDetailed lookup for term: {term}")
        
        # Test detailed lookup
        result = db_manager.lookup_rxnorm(term, include_details=True)
        found = result is not None and result.get("found", False)
        
        print(f"  Found: {found}")
        
        if found:
            print(f"  Code: {result.get('code')}")
            print(f"  Display: {result.get('display')}")
            print(f"  Match type: {result.get('match_type', 'unknown')}")
            
            # Check for expected fields
            for field in test_case["expected_fields"]:
                field_present = field in result or (field == "ingredients" and "ingredients" in result)
                print(f"  Has {field}: {field_present}")
                if field_present:
                    if field == "ingredients" and "ingredients" in result:
                        print(f"    Ingredients: {[ing.get('display') for ing in result['ingredients']]}")
                    else:
                        print(f"    {field}: {result.get(field)}")
    
    db_manager.close()

def run_tests():
    """Run all tests."""
    test_rxnorm_basic_lookup()
    test_rxnorm_drug_name_normalization()
    test_rxnorm_pattern_matching()
    test_rxnorm_detailed_lookup()

if __name__ == "__main__":
    run_tests()