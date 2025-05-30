#!/usr/bin/env python3
"""
Test core functionality of the Medical Terminology Mapper.

This test focuses on the core functionality without relying on external dependencies,
allowing us to verify the basic operations are working correctly.
"""

import os
import sys
import unittest

# Add parent directory to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestCoreFunctionality(unittest.TestCase):
    """Test core functionality of the application."""
    
    def test_import_paths(self):
        """Ensure that core modules can be imported."""
        try:
            from app.standards.terminology import mapper
            self.assertTrue(hasattr(mapper, 'TerminologyMapper'))
            print("Successfully imported TerminologyMapper")
        except ImportError as e:
            self.fail(f"Failed to import TerminologyMapper: {e}")
        
        try:
            from app.standards.terminology import fuzzy_matcher
            self.assertTrue(hasattr(fuzzy_matcher, 'FuzzyMatcher'))
            print("Successfully imported FuzzyMatcher")
        except ImportError as e:
            self.fail(f"Failed to import FuzzyMatcher: {e}")
    
    def test_fuzzy_matcher_creation(self):
        """Test that a FuzzyMatcher instance can be created."""
        from app.standards.terminology.fuzzy_matcher import FuzzyMatcher
        
        # Create a minimal mock database manager
        class MockDBManager:
            def __init__(self):
                self.connections = {}
        
        db_manager = MockDBManager()
        fuzzy_matcher = FuzzyMatcher(db_manager)
        
        # Check attributes
        self.assertTrue(hasattr(fuzzy_matcher, 'term_index'))
        self.assertTrue(hasattr(fuzzy_matcher, 'term_lists'))
        self.assertTrue(hasattr(fuzzy_matcher, 'thresholds'))
        
        # Check abbreviation expansion
        self.assertIn('HTN', fuzzy_matcher.abbreviations)
        self.assertIn('hypertension', fuzzy_matcher.abbreviations['HTN'])
    
    def test_term_variations(self):
        """Test term variation generation."""
        from app.standards.terminology.fuzzy_matcher import FuzzyMatcher
        
        # Create a minimal mock database manager
        class MockDBManager:
            def __init__(self):
                self.connections = {}
        
        db_manager = MockDBManager()
        fuzzy_matcher = FuzzyMatcher(db_manager)
        
        # Test basic variations
        variations = fuzzy_matcher._generate_term_variations("diabetes")
        self.assertIn("diabetes", variations)
        
        # Test prefix removal
        variations = fuzzy_matcher._generate_term_variations("history of hypertension")
        self.assertIn("hypertension", variations)
        
        # Test abbreviation expansion if configured
        if "HTN" in fuzzy_matcher.abbreviations:
            variations = fuzzy_matcher._generate_term_variations("HTN")
            self.assertTrue(any("hypertension" in v for v in variations))

if __name__ == "__main__":
    unittest.main()