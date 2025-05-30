#!/usr/bin/env python
"""
Tests for enhanced LOINC functionality in the Medical Terminology Mapper.

This module tests the enhanced LOINC-specific features, including the multiaxial 
hierarchy, panel-component relationships, and advanced lookup capabilities.
"""

import os
import sys
import unittest
import logging
from typing import Dict, List, Any, Optional

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.standards.terminology.embedded_db import EmbeddedDatabaseManager
from app.standards.terminology.mapper import TerminologyMapper
from app.standards.terminology.db_updater import create_sample_databases

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data directory for storing test databases
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")

class TestLOINCFeatures(unittest.TestCase):
    """Test enhanced LOINC functionality in the Medical Terminology Mapper."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment once for all tests."""
        os.makedirs(TEST_DATA_DIR, exist_ok=True)
        
        # Create sample databases for testing
        create_sample_databases(TEST_DATA_DIR)
        
        # Set up database manager with test data directory
        cls.db_manager = EmbeddedDatabaseManager(data_dir=TEST_DATA_DIR)
        cls.db_manager.connect()
        
        # Set up terminology mapper
        cls.mapper = TerminologyMapper({
            "data_dir": TEST_DATA_DIR,
            "use_fuzzy_matching": True
        })
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        cls.db_manager.close()
        cls.mapper.close()
    
    def test_basic_loinc_lookup(self):
        """Test basic LOINC concept lookup functionality."""
        # Test exact match lookup
        result = self.db_manager.lookup_loinc("hemoglobin a1c")
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "4548-4")
        self.assertEqual(result["system"], "http://loinc.org")
        
        # Test case-insensitive lookup
        result = self.db_manager.lookup_loinc("Hemoglobin A1C")
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "4548-4")
        
        # Test via component match
        result = self.db_manager.lookup_loinc("glucose")
        self.assertIsNotNone(result)
        self.assertTrue(result["code"] in ["2339-0", "25428-4"])
        
        # Test non-existent term
        result = self.db_manager.lookup_loinc("nonexistent term")
        self.assertIsNone(result)
    
    def test_detailed_loinc_lookup(self):
        """Test detailed LOINC concept lookup with additional fields."""
        # Test lookup with details
        result = self.db_manager.lookup_loinc("hemoglobin a1c", include_details=True)
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "4548-4")
        self.assertEqual(result["component"], "Hemoglobin A1c")
        self.assertEqual(result["property"], "MFr")
        self.assertEqual(result["system"], "http://loinc.org")
        self.assertEqual(result["specimen"], "Bld")
        self.assertEqual(result["scale"], "Qn")
        
        # Test via the mapper which adds context enhancement
        result = self.mapper.map_to_loinc("hemoglobin a1c", 
                                          context="Patient's hemoglobin A1c level is 6.5%", 
                                          include_details=True)
        self.assertTrue(result["found"])
        self.assertEqual(result["code"], "4548-4")
        self.assertTrue("component" in result)
        self.assertTrue("property" in result)
        # Context enhancement should have been applied
        self.assertTrue(result.get("context_enhanced", False))
    
    def test_loinc_normalized_lookup(self):
        """Test LOINC lookups with term normalization."""
        # Test with abbreviation normalization
        result = self.db_manager.lookup_loinc("hba1c")
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "4548-4")
        
        # Test with prefix/suffix normalization
        result = self.db_manager.lookup_loinc("serum sodium level")
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "2951-2")
        
        # Test with consumer name
        result = self.db_manager.lookup_loinc("Blood Glucose")
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "2339-0")
    
    def test_loinc_pattern_matching(self):
        """Test LOINC specialized pattern matching."""
        # Test specimen pattern matching
        conn = self.db_manager.connections.get("loinc")
        cursor = conn.cursor()
        
        # Test with a specimen pattern (e.g., "glucose in blood")
        result = self.db_manager._try_common_lab_patterns(cursor, "glucose in blood")
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "2339-0")
        self.assertEqual(result["match_type"], "specimen_pattern")
        
        # Test with common component matching
        result = self.db_manager._try_common_lab_patterns(cursor, "cholesterol")
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "2093-3")
        self.assertEqual(result["match_type"], "common_component")
        
        # Use the mapper for pattern-based lookup
        result = self.mapper.map_to_loinc("potassium in blood")
        self.assertTrue(result["found"])
        self.assertEqual(result["code"], "2823-3")
    
    def test_loinc_hierarchy(self):
        """Test LOINC hierarchical relationship lookups."""
        # Test panel-component relationships
        hierarchy = self.db_manager.get_loinc_hierarchy("57735-3")  # Comprehensive metabolic panel
        self.assertTrue(len(hierarchy) > 0)
        
        # Check that it contains children
        child_items = [item for item in hierarchy if item["relationship"] == "child"]
        self.assertTrue(len(child_items) > 0)
        
        # Verify some expected components of the CMP
        components = [item["code"] for item in child_items]
        self.assertTrue("2339-0" in components)  # Glucose
        self.assertTrue("2951-2" in components)  # Sodium
        
        # Test CBC panel components
        hierarchy = self.db_manager.get_loinc_hierarchy("58410-2")  # CBC panel
        child_items = [item for item in hierarchy if item["relationship"] == "child"]
        self.assertTrue(len(child_items) > 0)
        
        components = [item["code"] for item in child_items]
        self.assertTrue("6690-2" in components)  # WBC
        self.assertTrue("718-7" in components)   # Hemoglobin
        
        # Test specific relationship type filtering
        relations = self.db_manager.get_loinc_hierarchy("2160-0", relationship_type="CALCULATED_FROM")
        self.assertTrue(len(relations) > 0)
        calculated_items = [item["code"] for item in relations]
        self.assertTrue("59238-6" in calculated_items)  # GFR
    
    def test_loinc_parts(self):
        """Test LOINC multiaxial part lookup."""
        # Test retrieving parts for a specific LOINC code
        concept = self.db_manager.get_loinc_concept("2339-0", include_details=True)
        self.assertIsNotNone(concept)
        self.assertTrue("parts" in concept)
        
        # Verify that parts include expected component, property, etc.
        component_parts = [part for part in concept.get("parts", []) 
                          if part["part_type"] == "COMPONENT"]
        self.assertTrue(len(component_parts) > 0)
        self.assertEqual(component_parts[0]["part_number"], "LP14998-8")  # Glucose
        
        # Test looking up LOINC codes by part
        glucose_codes = self.db_manager.get_loinc_by_part("LP14998-8")  # Glucose component
        self.assertTrue(len(glucose_codes) > 0)
        
        glucose_code_list = [item["code"] for item in glucose_codes]
        self.assertTrue("2339-0" in glucose_code_list)  # Blood glucose
        
        # Test specific part type filtering
        serum_codes = self.db_manager.get_loinc_by_part("LP14162-0", "SYSTEM")  # Serum/Plasma
        self.assertTrue(len(serum_codes) > 0)
    
    def test_find_similar_tests(self):
        """Test finding similar LOINC tests."""
        # Test finding similar tests to a given term
        similar_tests = self.mapper.find_similar_lab_tests("cholesterol", limit=5)
        self.assertTrue(len(similar_tests) > 0)
        
        # Should include various cholesterol tests (total, HDL, LDL)
        codes = [test["code"] for test in similar_tests]
        self.assertTrue(any(code in codes for code in ["2093-3", "2085-9", "13457-7"]))
        
        # Test with a non-specific term
        similar_tests = self.mapper.find_similar_lab_tests("liver", limit=3)
        self.assertTrue(len(similar_tests) > 0)
        
        # Should return a manageable number of results
        self.assertTrue(len(similar_tests) <= 3)
    
    def test_specialized_panel_lookup(self):
        """Test identifying and looking up lab panels."""
        # Test lookup of a panel
        result = self.db_manager.lookup_loinc("cbc", include_details=True)
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "58410-2")
        self.assertEqual(result["order_obs"], "ORDER")  # Should be identified as an order
        
        # Test via the mapper
        result = self.mapper.map_to_loinc("Complete Blood Count", include_details=True)
        self.assertTrue(result["found"])
        self.assertEqual(result["code"], "58410-2")
        
        # Verify panel components are included
        self.assertTrue("child_items" in result)
        self.assertTrue(len(result["child_items"]) > 0)
        
        # Test for lipid panel by common name
        result = self.mapper.map_to_loinc("lipid panel", include_details=True)
        self.assertTrue(result["found"])
        self.assertEqual(result["code"], "24331-1")
        
        # Verify panel components are included
        self.assertTrue("child_items" in result)
        self.assertTrue(len(result["child_items"]) > 0)

if __name__ == "__main__":
    unittest.main()