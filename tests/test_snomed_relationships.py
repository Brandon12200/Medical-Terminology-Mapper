#!/usr/bin/env python3
"""
Test script for SNOMED CT relationship functionality.

This script tests the SNOMED CT hierarchy and relationship handling functionality.
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
logger = logging.getLogger("test_snomed_relationships")

def setup_test_db():
    """Ensure the test database is set up with sample data."""
    # Define the path to the data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           "data", "terminology")
    
    # Create the directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Check if the sample database exists
    db_path = os.path.join(data_dir, "snomed_core.sqlite")
    
    if not os.path.exists(db_path):
        logging.info("Creating sample databases")
        create_sample_databases(data_dir)
    
    return data_dir

def test_snomed_hierarchy():
    """Test SNOMED CT hierarchy functionality."""
    data_dir = setup_test_db()
    
    # Initialize the database manager
    db_manager = EmbeddedDatabaseManager(data_dir)
    db_manager.connect()
    
    # Test lookups with hierarchy
    test_cases = [
        # Well-connected concept
        {"code": "73211009", "term": "diabetes mellitus", "expected_parents": 1, "expected_children": 2},
        # Leaf concept
        {"code": "44054006", "term": "diabetes type 2", "expected_parents": 1, "expected_children": 0},
        # Root-like concept
        {"code": "24700007", "term": "multiple sclerosis", "expected_parents": 0, "expected_children": 2}
    ]
    
    print("\n=== Testing SNOMED CT Hierarchy Functionality ===")
    
    for test_case in test_cases:
        code = test_case["code"]
        print(f"\nTesting concept: {test_case['term']} ({code})")
        
        # Test direct lookup with hierarchy
        concept = db_manager.get_snomed_concept(code, include_hierarchy=True)
        if not concept:
            print(f"  ERROR: Concept {code} not found")
            continue
            
        print(f"  Found: {concept['display']}")
        
        # Check for parent concepts
        parents = concept.get("parents", [])
        print(f"  Parents: {len(parents)} found, {test_case['expected_parents']} expected")
        for parent in parents:
            print(f"    - {parent['display']} ({parent['code']})")
            
        # Check for child concepts
        children = concept.get("children", [])
        print(f"  Children: {len(children)} found, {test_case['expected_children']} expected")
        for child in children:
            print(f"    - {child['display']} ({child['code']})")
        
        # Test ancestor/descendant retrieval
        ancestors = db_manager.get_snomed_ancestors(code)
        print(f"  Ancestors: {len(ancestors)} found")
        for ancestor in ancestors[:3]:  # Show first few
            print(f"    - {ancestor['display']} ({ancestor['code']}) distance: {ancestor['distance']}")
            
        descendants = db_manager.get_snomed_descendants(code)
        print(f"  Descendants: {len(descendants)} found")
        for descendant in descendants[:3]:  # Show first few
            print(f"    - {descendant['display']} ({descendant['code']}) distance: {descendant['distance']}")
    
    db_manager.close()

def test_snomed_relationships():
    """Test SNOMED CT relationship functionality."""
    data_dir = setup_test_db()
    
    # Initialize the database manager
    db_manager = EmbeddedDatabaseManager(data_dir)
    db_manager.connect()
    
    # Test relationship cases
    test_cases = [
        {"code": "38341003", "term": "hypertension", "rel_type": "363698007", "expected": 1},  # Finding site
        {"code": "422034002", "term": "diabetic neuropathy", "rel_type": "42752001", "expected": 1},  # Due to
        {"code": "49436004", "term": "atrial fibrillation", "rel_type": "47429007", "expected": 1}  # Associated with
    ]
    
    print("\n=== Testing SNOMED CT Relationship Functionality ===")
    
    for test_case in test_cases:
        code = test_case["code"]
        rel_type = test_case["rel_type"]
        print(f"\nTesting relationships for: {test_case['term']} ({code})")
        
        # Get concept with relationships
        concept = db_manager.get_snomed_concept(code, include_hierarchy=True)
        if not concept:
            print(f"  ERROR: Concept {code} not found")
            continue
            
        print(f"  Found: {concept['display']}")
        
        # Look for specific relationship type in relationships dictionary
        relationships = concept.get("relationships", {})
        specific_rels = relationships.get(rel_type, [])
        print(f"  Relationship type {rel_type}: {len(specific_rels)} found, {test_case['expected']} expected")
        for rel in specific_rels:
            print(f"    - {rel['display']} ({rel['code']})")
        
        # Use the relationship-specific helper method
        related = db_manager.get_snomed_related_concepts(code, rel_type)
        print(f"  Related concepts (helper method): {len(related)} found")
        for rel in related:
            print(f"    - {rel['display']} ({rel['code']}) direction: {rel['direction']}")
    
    db_manager.close()

def run_tests():
    """Run all tests."""
    test_snomed_hierarchy()
    test_snomed_relationships()

if __name__ == "__main__":
    run_tests()