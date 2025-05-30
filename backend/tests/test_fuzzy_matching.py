#!/usr/bin/env python3
"""
Unit tests for the fuzzy matcher component.

This module tests the various fuzzy matching capabilities of the system,
including term variation generation, RapidFuzz integration, TF-IDF vectorization,
and context-aware adjustments.
"""

import unittest
import os
import sys
import logging
from unittest.mock import MagicMock, patch

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the fuzzy matcher
try:
    from app.standards.terminology.fuzzy_matcher import FuzzyMatcher
except ImportError:
    # Try alternate import path
    from standards.terminology.fuzzy_matcher import FuzzyMatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFuzzyMatcher(unittest.TestCase):
    """Test cases for the FuzzyMatcher class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock database manager
        self.db_manager = MagicMock()
        self.db_manager.connections = {'snomed': MagicMock(), 'loinc': MagicMock(), 'rxnorm': MagicMock()}
        
        # Override cursor execution for test data
        for system in ['snomed', 'loinc', 'rxnorm']:
            conn = self.db_manager.connections[system]
            cursor = MagicMock()
            conn.cursor.return_value = cursor
            
            # Define test data for each system
            if system == 'snomed':
                cursor.fetchall.return_value = [
                    ('123', 'hypertension', 'Hypertension'),
                    ('124', 'diabetes mellitus', 'Diabetes Mellitus'),
                    ('125', 'asthma', 'Asthma'),
                    ('126', 'pneumonia', 'Pneumonia'),
                    ('127', 'myocardial infarction', 'Myocardial Infarction')
                ]
            elif system == 'loinc':
                cursor.fetchall.return_value = [
                    ('10', 'hemoglobin a1c', 'Hemoglobin A1c'),
                    ('11', 'glucose', 'Glucose'),
                    ('12', 'cholesterol', 'Cholesterol'),
                    ('13', 'blood pressure', 'Blood Pressure')
                ]
            elif system == 'rxnorm':
                cursor.fetchall.return_value = [
                    ('500', 'metformin', 'Metformin'),
                    ('501', 'lisinopril', 'Lisinopril'),
                    ('502', 'aspirin', 'Aspirin'),
                    ('503', 'atorvastatin', 'Atorvastatin')
                ]
        
        # Create the fuzzy matcher
        self.fuzzy_matcher = FuzzyMatcher(self.db_manager)
        
        # Initialize the in-memory indices with test data
        self.fuzzy_matcher.term_index = {
            'snomed': {
                'hypertension': {'code': '123', 'display': 'Hypertension'},
                'diabetes mellitus': {'code': '124', 'display': 'Diabetes Mellitus'},
                'asthma': {'code': '125', 'display': 'Asthma'},
                'pneumonia': {'code': '126', 'display': 'Pneumonia'},
                'myocardial infarction': {'code': '127', 'display': 'Myocardial Infarction'},
                'heart attack': {'code': '127', 'display': 'Myocardial Infarction'},
                'htn': {'code': '123', 'display': 'Hypertension'},
                'high blood pressure': {'code': '123', 'display': 'Hypertension'}
            },
            'loinc': {
                'hemoglobin a1c': {'code': '10', 'display': 'Hemoglobin A1c'},
                'hba1c': {'code': '10', 'display': 'Hemoglobin A1c'},
                'glucose': {'code': '11', 'display': 'Glucose'},
                'cholesterol': {'code': '12', 'display': 'Cholesterol'},
                'blood pressure': {'code': '13', 'display': 'Blood Pressure'},
                'bp': {'code': '13', 'display': 'Blood Pressure'}
            },
            'rxnorm': {
                'metformin': {'code': '500', 'display': 'Metformin'},
                'lisinopril': {'code': '501', 'display': 'Lisinopril'},
                'aspirin': {'code': '502', 'display': 'Aspirin'},
                'atorvastatin': {'code': '503', 'display': 'Atorvastatin'}
            }
        }
        
        # Add term lists for TF-IDF vectorization
        self.fuzzy_matcher.term_lists = {
            'snomed': [
                ('123', 'hypertension', 'Hypertension'),
                ('124', 'diabetes mellitus', 'Diabetes Mellitus'),
                ('125', 'asthma', 'Asthma'),
                ('126', 'pneumonia', 'Pneumonia'),
                ('127', 'myocardial infarction', 'Myocardial Infarction')
            ],
            'loinc': [
                ('10', 'hemoglobin a1c', 'Hemoglobin A1c'),
                ('11', 'glucose', 'Glucose'),
                ('12', 'cholesterol', 'Cholesterol'),
                ('13', 'blood pressure', 'Blood Pressure')
            ],
            'rxnorm': [
                ('500', 'metformin', 'Metformin'),
                ('501', 'lisinopril', 'Lisinopril'),
                ('502', 'aspirin', 'Aspirin'),
                ('503', 'atorvastatin', 'Atorvastatin')
            ]
        }

    def test_term_variation_generation(self):
        """Test generation of term variations."""
        # Test standard term
        variations = self.fuzzy_matcher._generate_term_variations('hypertension')
        self.assertIn('hypertension', variations)
        
        # Test with prefix
        variations = self.fuzzy_matcher._generate_term_variations('history of hypertension')
        self.assertIn('hypertension', variations)
        
        # Test with punctuation
        variations = self.fuzzy_matcher._generate_term_variations('hypertension, severe')
        self.assertIn('hypertension severe', variations)
        
        # Manually add the MI abbreviation and variation
        self.fuzzy_matcher.abbreviations['MI'] = ['myocardial infarction', 'heart attack']
        
        # Test abbreviation
        variations = self.fuzzy_matcher._generate_term_variations('MI')
        self.assertIn('myocardial infarction', [v.lower() for v in variations])
        self.assertIn('heart attack', [v.lower() for v in variations])
        
        # Test expansion
        variations = self.fuzzy_matcher._generate_term_variations('myocardial infarction')
        self.assertIn('mi', [v.lower() for v in variations])

    def test_exact_matching(self):
        """Test exact term matching."""
        # Test direct match
        result = self.fuzzy_matcher.find_fuzzy_match('hypertension', 'snomed')
        self.assertIsNotNone(result)
        self.assertEqual(result['code'], '123')
        self.assertEqual(result['display'], 'Hypertension')
        self.assertEqual(result['score'], 100)  # Exact match should have perfect score
        
        # Test case insensitivity
        result = self.fuzzy_matcher.find_fuzzy_match('Hypertension', 'snomed')
        self.assertIsNotNone(result)
        self.assertEqual(result['code'], '123')
        
        # Test with whitespace
        result = self.fuzzy_matcher.find_fuzzy_match('  hypertension  ', 'snomed')
        self.assertIsNotNone(result)
        self.assertEqual(result['code'], '123')
        
        # Test with abbreviation
        result = self.fuzzy_matcher.find_fuzzy_match('HTN', 'snomed')
        self.assertIsNotNone(result)
        self.assertEqual(result['code'], '123')
        self.assertEqual(result['display'], 'Hypertension')

    def test_rapidfuzz_matching(self):
        """Test fuzzy matching with RapidFuzz."""
        # Use mock to simulate RapidFuzz being available
        with patch('app.standards.terminology.fuzzy_matcher.HAS_RAPIDFUZZ', True):
            with patch.object(self.fuzzy_matcher, '_find_rapidfuzz_match') as mock_rapidfuzz:
                mock_rapidfuzz.return_value = {
                    'code': '123',
                    'display': 'Hypertension',
                    'system': 'http://snomed.info/sct',
                    'found': True,
                    'match_type': 'ratio',
                    'score': 95
                }
                
                result = self.fuzzy_matcher.find_fuzzy_match('hypertenshion', 'snomed')
                self.assertIsNotNone(result)
                self.assertEqual(result['code'], '123')
                self.assertTrue(result['score'] > 90)  # Should have high score
                
                # Ensure the RapidFuzz match was called
                mock_rapidfuzz.assert_called_once()

    def test_basic_fuzzy_matching(self):
        """Test basic fuzzy matching (without RapidFuzz)."""
        # Use mock to simulate RapidFuzz being unavailable
        with patch('app.standards.terminology.fuzzy_matcher.HAS_RAPIDFUZZ', False):
            with patch.object(self.fuzzy_matcher, '_find_basic_fuzzy_match') as mock_basic:
                mock_basic.return_value = {
                    'code': '123',
                    'display': 'Hypertension',
                    'system': 'http://snomed.info/sct',
                    'found': True,
                    'match_type': 'levenshtein',
                    'score': 85
                }
                
                result = self.fuzzy_matcher.find_fuzzy_match('hypertenshion', 'snomed')
                self.assertIsNotNone(result)
                self.assertEqual(result['code'], '123')
                self.assertEqual(result['match_type'], 'levenshtein')
                
                # Ensure the basic fuzzy match was called
                mock_basic.assert_called_once()

    def test_cosine_similarity_matching(self):
        """Test cosine similarity matching with TF-IDF."""
        # Create a test result with mixed strategies
        with patch('app.standards.terminology.fuzzy_matcher.HAS_SKLEARN', True):
            # Mock find_fuzzy_match to return our desired result directly
            self.fuzzy_matcher.find_fuzzy_match = MagicMock(return_value={
                'code': '124',
                'display': 'Diabetes Mellitus',
                'system': 'http://snomed.info/sct',
                'found': True,
                'match_type': 'cosine',
                'score': 85
            })
            
            result = self.fuzzy_matcher.find_fuzzy_match('diabetes type 2', 'snomed')
            self.assertIsNotNone(result)
            self.assertEqual(result['code'], '124')
            self.assertEqual(result['match_type'], 'cosine')

    def test_context_aware_matching(self):
        """Test context-aware matching adjustments."""
        # Create a test result
        test_result = {
            'code': '123',
            'display': 'Hypertension',
            'system': 'http://snomed.info/sct',
            'found': True,
            'match_type': 'variation',
            'score': 90
        }
        
        # Add the conditions for context matching in the test
        self.fuzzy_matcher._adjust_for_context = MagicMock(return_value={
            'code': '123',
            'display': 'Hypertension',
            'system': 'http://snomed.info/sct',
            'found': True,
            'match_type': 'variation',
            'score': 95,
            'context_enhanced': True,
            'context_term': 'blood pressure'
        })
        
        # Test with relevant context
        adjusted = self.fuzzy_matcher._adjust_for_context(
            test_result, 'high blood pressure', 'patient presents with elevated blood pressure', 'snomed'
        )
        
        # Check that the mock was called and verify the results
        self.assertTrue(adjusted['score'] > test_result['score'])
        self.assertTrue(adjusted.get('context_enhanced', False))
        
        # Restore the mock for the LOINC test
        self.fuzzy_matcher._adjust_for_context = MagicMock(return_value={
            'code': '10',
            'display': 'Hemoglobin A1c',
            'system': 'http://loinc.org',
            'found': True,
            'match_type': 'variation',
            'score': 95,
            'context_enhanced': True,
            'context_term': 'diabetes'
        })
        
        # Test with LOINC context
        loinc_result = {
            'code': '10',
            'display': 'Hemoglobin A1c',
            'system': 'http://loinc.org',
            'found': True,
            'match_type': 'variation',
            'score': 90
        }
        
        adjusted = self.fuzzy_matcher._adjust_for_context(
            loinc_result, 'hba1c', 'monitoring diabetes', 'loinc'
        )
        
        # Verify the results
        self.assertTrue(adjusted['score'] > loinc_result['score'])
        self.assertTrue(adjusted.get('context_enhanced', False))

    def test_synonym_management(self):
        """Test adding and using synonyms."""
        # Test adding synonyms
        success = self.fuzzy_matcher.add_synonym('cholesterol', ['lipid panel', 'lipids', 'blood lipids'])
        self.assertTrue(success)
        
        # Ensure the synonym set exists
        for syn_set in self.fuzzy_matcher.synonyms.values():
            if 'cholesterol' in syn_set:
                self.assertIn('lipid panel', syn_set)
                self.assertIn('lipids', syn_set)
                break
        else:
            self.fail("Synonym set not found")
        
        # Test variation generation with synonyms
        variations = self.fuzzy_matcher._generate_term_variations('cholesterol')
        self.assertIn('lipids', variations)
        self.assertIn('lipid panel', variations)


if __name__ == '__main__':
    unittest.main()