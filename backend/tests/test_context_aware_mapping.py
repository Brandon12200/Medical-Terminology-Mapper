#!/usr/bin/env python3
"""
Test suite for Context-Aware Terminology Mapping.

Tests the advanced context-aware mapping capabilities including clinical domain
detection, context modifier recognition, and semantic scoring.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.standards.terminology.context_aware_mapper import (
    ContextAwareTerminologyMapper,
    ClinicalDomain,
    ContextModifier,
    ClinicalContext,
    ContextAwareMapping
)
from app.standards.terminology.mapper import TerminologyMapper


class TestContextAwareMapping(unittest.TestCase):
    """Test context-aware mapping functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock base mapper
        self.mock_base_mapper = Mock(spec=TerminologyMapper)
        
        # Configure mock responses
        self.mock_base_mapper.map_term.return_value = {
            'found': True,
            'system': 'http://snomed.info/sct',
            'code': '38341003',
            'display': 'Hypertensive disorder',
            'confidence': 0.9,
            'match_type': 'exact'
        }
        
        # Create context-aware mapper
        self.mapper = ContextAwareTerminologyMapper(
            base_mapper=self.mock_base_mapper,
            config={'enable_context_aware': True}
        )
    
    def test_clinical_domain_detection(self):
        """Test clinical domain detection from context."""
        # Test cardiology domain
        result = self.mapper._detect_clinical_domain(
            "patient presents with chest pain and elevated cardiac enzymes"
        )
        self.assertEqual(result, ClinicalDomain.CARDIOLOGY)
        
        # Test laboratory domain
        result = self.mapper._detect_clinical_domain(
            "blood glucose level was 180 mg/dl"
        )
        self.assertEqual(result, ClinicalDomain.LABORATORY)
        
        # Test pulmonology domain
        result = self.mapper._detect_clinical_domain(
            "patient has shortness of breath and lung consolidation"
        )
        self.assertEqual(result, ClinicalDomain.PULMONOLOGY)
        
        # Test general domain (fallback)
        result = self.mapper._detect_clinical_domain(
            "patient is feeling well today"
        )
        self.assertEqual(result, ClinicalDomain.GENERAL)
    
    def test_context_modifier_detection(self):
        """Test detection of context modifiers."""
        # Test negation detection
        context = self.mapper._detect_clinical_context(
            "hypertension", 
            "patient has no history of hypertension"
        )
        self.assertIn(ContextModifier.NEGATION, context.modifiers)
        
        # Test uncertainty detection
        context = self.mapper._detect_clinical_context(
            "diabetes", 
            "patient possibly has diabetes mellitus"
        )
        self.assertIn(ContextModifier.UNCERTAINTY, context.modifiers)
        
        # Test past history detection
        context = self.mapper._detect_clinical_context(
            "pneumonia", 
            "history of pneumonia last year"
        )
        self.assertIn(ContextModifier.PAST_HISTORY, context.modifiers)
        
        # Test current detection
        context = self.mapper._detect_clinical_context(
            "asthma", 
            "currently experiencing asthma exacerbation"
        )
        self.assertIn(ContextModifier.CURRENT, context.modifiers)
    
    def test_semantic_context_extraction(self):
        """Test semantic context extraction."""
        semantic_context = self.mapper._extract_semantic_context(
            "patient takes aspirin 325mg daily for cardiac protection",
            "aspirin"
        )
        
        self.assertGreater(semantic_context['word_count'], 5)
        self.assertTrue(semantic_context['has_dosage'])
        self.assertGreaterEqual(semantic_context['term_position'], 0)
    
    def test_context_aware_mapping_basic(self):
        """Test basic context-aware mapping."""
        result = self.mapper.map_with_context(
            "hypertension",
            "patient presents with elevated blood pressure and hypertension",
            ClinicalDomain.CARDIOLOGY
        )
        
        self.assertIsInstance(result, ContextAwareMapping)
        self.assertTrue(result.found)
        self.assertEqual(result.clinical_context.domain, ClinicalDomain.CARDIOLOGY)
        self.assertGreater(result.confidence, 0.0)
        self.assertGreater(result.context_score, 0.0)
    
    def test_context_aware_mapping_with_negation(self):
        """Test context-aware mapping with negation."""
        result = self.mapper.map_with_context(
            "diabetes",
            "patient denies any history of diabetes mellitus",
            ClinicalDomain.ENDOCRINOLOGY
        )
        
        self.assertIsInstance(result, ContextAwareMapping)
        self.assertIn(ContextModifier.NEGATION, result.clinical_context.modifiers)
        # Confidence should be reduced due to negation
        self.assertLess(result.confidence, 0.9)
        self.assertIn('negated', result.match_type)
    
    def test_context_aware_mapping_with_uncertainty(self):
        """Test context-aware mapping with uncertainty."""
        result = self.mapper.map_with_context(
            "pneumonia",
            "chest x-ray findings are consistent with possible pneumonia",
            ClinicalDomain.PULMONOLOGY
        )
        
        self.assertIsInstance(result, ContextAwareMapping)
        self.assertIn(ContextModifier.UNCERTAINTY, result.clinical_context.modifiers)
        # Confidence should be slightly reduced due to uncertainty
        self.assertLess(result.confidence, 1.0)
    
    def test_domain_specific_enhancement(self):
        """Test domain-specific mapping enhancement."""
        # Mock LOINC result for laboratory domain
        self.mock_base_mapper.map_term.return_value = {
            'found': True,
            'system': 'http://loinc.org',
            'code': '2339-0',
            'display': 'Glucose [Mass/volume] in Blood',
            'confidence': 0.8,
            'match_type': 'exact'
        }
        
        result = self.mapper.map_with_context(
            "glucose",
            "blood glucose level is 150 mg/dl",
            ClinicalDomain.LABORATORY
        )
        
        self.assertIsInstance(result, ContextAwareMapping)
        self.assertTrue(result.found)
        self.assertEqual(result.clinical_context.domain, ClinicalDomain.LABORATORY)
        # Confidence should be boosted for LOINC in laboratory domain
        self.assertGreater(result.confidence, 0.8)
        self.assertGreaterEqual(result.domain_relevance, 0.9)
    
    def test_batch_context_aware_mapping(self):
        """Test batch context-aware mapping."""
        terms_with_context = [
            ("hypertension", "patient has elevated blood pressure"),
            ("diabetes", "blood sugar levels are high"),
            ("aspirin", "prescribed aspirin 81mg daily")
        ]
        
        results = self.mapper.batch_map_with_context(
            terms_with_context,
            ClinicalDomain.CARDIOLOGY
        )
        
        self.assertEqual(len(results), 3)
        self.assertTrue(all(isinstance(r, ContextAwareMapping) for r in results))
        self.assertTrue(all(r.clinical_context.domain == ClinicalDomain.CARDIOLOGY for r in results))
    
    def test_context_statistics(self):
        """Test context mapping statistics."""
        # Create sample mappings
        mappings = []
        
        # Successful mapping
        mappings.append(ContextAwareMapping(
            original_text="hypertension",
            found=True,
            system="http://snomed.info/sct",
            code="38341003",
            display="Hypertensive disorder",
            confidence=0.9,
            match_type="exact",
            clinical_context=ClinicalContext(
                domain=ClinicalDomain.CARDIOLOGY,
                modifiers=[ContextModifier.CURRENT],
                surrounding_text="current hypertension",
                confidence=0.8,
                semantic_context={}
            ),
            context_score=0.85,
            semantic_score=0.9,
            domain_relevance=0.88,
            alternative_mappings=[]
        ))
        
        # Failed mapping
        mappings.append(ContextAwareMapping(
            original_text="unknown_term",
            found=False,
            system=None,
            code=None,
            display=None,
            confidence=0.0,
            match_type="no_match",
            clinical_context=ClinicalContext(
                domain=ClinicalDomain.GENERAL,
                modifiers=[],
                surrounding_text="",
                confidence=0.5,
                semantic_context={}
            ),
            context_score=0.0,
            semantic_score=0.0,
            domain_relevance=0.0,
            alternative_mappings=[]
        ))
        
        stats = self.mapper.get_context_statistics(mappings)
        
        self.assertEqual(stats['total_mappings'], 2)
        self.assertEqual(stats['successful_mappings'], 1)
        self.assertEqual(stats['success_rate'], 0.5)
        self.assertIn('cardiology', stats['domain_distribution'])
        self.assertIn('current', stats['modifier_distribution'])
        self.assertGreater(stats['average_context_score'], 0)
    
    def test_alternative_mappings(self):
        """Test alternative mapping generation."""
        # Mock fuzzy matcher
        mock_fuzzy_matcher = Mock()
        mock_fuzzy_matcher.find_similar_terms.return_value = [
            {
                'found': True,
                'system': 'http://snomed.info/sct',
                'code': '123456',
                'display': 'Alternative term',
                'confidence': 0.7,
                'match_type': 'fuzzy'
            },
            {
                'found': True,
                'system': 'http://loinc.org',
                'code': '789012',
                'display': 'Another alternative',
                'confidence': 0.6,
                'match_type': 'fuzzy'
            }
        ]
        
        self.mock_base_mapper.fuzzy_matcher = mock_fuzzy_matcher
        
        result = self.mapper.map_with_context(
            "hypertension",
            "patient has high blood pressure",
            ClinicalDomain.CARDIOLOGY
        )
        
        self.assertIsInstance(result, ContextAwareMapping)
        self.assertTrue(len(result.alternative_mappings) > 0)
        # Alternatives should have context_relevance scores
        for alt in result.alternative_mappings:
            self.assertIn('context_relevance', alt)
    
    def test_fallback_mapping(self):
        """Test context-aware fallback mapping when primary mapping fails."""
        # Mock base mapper to return no match
        self.mock_base_mapper.map_term.return_value = {
            'found': False,
            'system': None,
            'code': None,
            'display': None,
            'confidence': 0.0,
            'match_type': 'no_match'
        }
        
        # Mock fuzzy matcher to provide fallback
        mock_fuzzy_matcher = Mock()
        mock_fuzzy_matcher.find_similar_terms.return_value = [
            {
                'found': True,
                'system': 'http://snomed.info/sct',
                'code': '12345',
                'display': 'Fuzzy match',
                'confidence': 0.6,
                'match_type': 'fuzzy'
            }
        ]
        
        self.mock_base_mapper.fuzzy_matcher = mock_fuzzy_matcher
        
        result = self.mapper.map_with_context(
            "rare_condition",
            "patient diagnosed with rare cardiac condition",
            ClinicalDomain.CARDIOLOGY
        )
        
        # Should get fuzzy fallback mapping
        self.assertIsInstance(result, ContextAwareMapping)
        # May or may not find match depending on fallback success
    
    def test_confidence_calculation(self):
        """Test context confidence calculation."""
        # High confidence case
        confidence = self.mapper._calculate_context_confidence(
            "patient presents with acute myocardial infarction and elevated cardiac enzymes",
            ClinicalDomain.CARDIOLOGY,
            [ContextModifier.ACUTE, ContextModifier.CURRENT]
        )
        self.assertGreater(confidence, 0.7)
        
        # Low confidence case
        confidence = self.mapper._calculate_context_confidence(
            "patient feels well",
            ClinicalDomain.GENERAL,
            []
        )
        self.assertLess(confidence, 0.7)
    
    def test_error_handling(self):
        """Test error handling in context-aware mapping."""
        # Mock base mapper to raise exception
        self.mock_base_mapper.map_term.side_effect = Exception("Test error")
        
        result = self.mapper.map_with_context(
            "test_term",
            "test context"
        )
        
        self.assertIsInstance(result, ContextAwareMapping)
        self.assertFalse(result.found)
        self.assertEqual(result.match_type, 'error')
        self.assertEqual(result.confidence, 0.0)


class TestClinicalContext(unittest.TestCase):
    """Test ClinicalContext data class."""
    
    def test_clinical_context_creation(self):
        """Test creating ClinicalContext object."""
        context = ClinicalContext(
            domain=ClinicalDomain.CARDIOLOGY,
            modifiers=[ContextModifier.NEGATION, ContextModifier.CURRENT],
            surrounding_text="patient has no current chest pain",
            confidence=0.8,
            semantic_context={'word_count': 6}
        )
        
        self.assertEqual(context.domain, ClinicalDomain.CARDIOLOGY)
        self.assertEqual(len(context.modifiers), 2)
        self.assertIn(ContextModifier.NEGATION, context.modifiers)
        self.assertEqual(context.confidence, 0.8)
    
    def test_clinical_context_validation(self):
        """Test ClinicalContext validation."""
        # Invalid confidence should raise error
        with self.assertRaises(ValueError):
            ClinicalContext(
                domain=ClinicalDomain.GENERAL,
                modifiers=[],
                surrounding_text="",
                confidence=1.5,  # Invalid confidence > 1.0
                semantic_context={}
            )
        
        with self.assertRaises(ValueError):
            ClinicalContext(
                domain=ClinicalDomain.GENERAL,
                modifiers=[],
                surrounding_text="",
                confidence=-0.1,  # Invalid confidence < 0.0
                semantic_context={}
            )


class TestEnums(unittest.TestCase):
    """Test enum definitions."""
    
    def test_clinical_domain_enum(self):
        """Test ClinicalDomain enum."""
        self.assertEqual(ClinicalDomain.CARDIOLOGY.value, "cardiology")
        self.assertEqual(ClinicalDomain.LABORATORY.value, "laboratory")
        self.assertEqual(ClinicalDomain.GENERAL.value, "general")
    
    def test_context_modifier_enum(self):
        """Test ContextModifier enum."""
        self.assertEqual(ContextModifier.NEGATION.value, "negation")
        self.assertEqual(ContextModifier.UNCERTAINTY.value, "uncertainty")
        self.assertEqual(ContextModifier.TEMPORAL.value, "temporal")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)