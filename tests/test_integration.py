"""
Integration tests for the Medical Terminology Mapper.
Tests the complete workflow from text input to mapped terminology.
"""

import os
import sys
import unittest
import logging
from typing import Dict, List, Any, Set

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from app.models.model_loader import ModelManager
from app.extractors.term_extractor import TermExtractor
from app.extractors.terminology_mapper import TerminologyMapper
from app.models.preprocessing import prepare_for_biobert

# Import test data
from test_data import SAMPLE_TEXTS, EXPECTED_TERM_TYPES

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestIntegration(unittest.TestCase):
    """Integration tests for the full term recognition and mapping pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test resources before any tests run."""
        # Initialize model manager
        cls.model_manager = ModelManager()
        cls.model_manager.initialize()
        
        # Create extractor with all features enabled
        cls.extractor = TermExtractor(
            cls.model_manager,
            use_cache=False,
            offline_mode=True,  # Start with offline mode for faster tests
            use_terminology=True
        )
        
        # Create separate components for component testing
        cls.terminology_mapper = TerminologyMapper()
        
        # Flag to track if BioBERT is available
        cls.biobert_available = hasattr(cls.model_manager, 'model') and cls.model_manager.model is not None
        
        # Only create online extractor if BioBERT is available
        if cls.biobert_available:
            try:
                cls.online_extractor = TermExtractor(
                    cls.model_manager,
                    use_cache=False,
                    offline_mode=False,
                    use_terminology=True
                )
            except Exception as e:
                logger.warning(f"BioBERT extractor failed to initialize: {e}")
                cls.biobert_available = False
    
    def _get_extractor(self, use_biobert: bool = False):
        """Get the appropriate extractor based on test needs."""
        if use_biobert and self.biobert_available:
            return self.online_extractor
        return self.extractor
    
    def test_full_pipeline_general_medical(self):
        """Integration test for general medical text processing."""
        # Get test text
        text = SAMPLE_TEXTS['general_medical_history']
        expected_terms = EXPECTED_TERM_TYPES['general_medical_history']
        
        # Process text through the full pipeline
        terms = self.extractor.extract_terms(text)
        
        # Verify results
        self._verify_terms(terms, expected_terms)
        
        # Verify terminology mapping
        self._verify_terminology_mapping(terms)
    
    def test_full_pipeline_medications(self):
        """Integration test for medication-focused text processing."""
        # Get test text
        text = SAMPLE_TEXTS['medication_list']
        expected_terms = EXPECTED_TERM_TYPES['medication_list']
        
        # Process text through the full pipeline
        terms = self.extractor.extract_terms(text)
        
        # Verify results
        self._verify_terms(terms, expected_terms)
        
        # Check for dosage information
        dosage_count = sum(1 for term in terms if term.get('subtype') == 'DOSAGE')
        self.assertGreater(dosage_count, 0, "Should extract dosage information from medication list")
        
        # Verify RxNorm mapping for medications
        for term in terms:
            if term['type'] == 'MEDICATION':
                self.assertEqual(term['terminology']['vocabulary'], 'RXNORM', 
                               f"Medication {term['text']} should map to RxNorm")
    
    def test_full_pipeline_lab_results(self):
        """Integration test for lab results text processing."""
        # Get test text
        text = SAMPLE_TEXTS['lab_results']
        expected_terms = EXPECTED_TERM_TYPES['lab_results']
        
        # Process text through the full pipeline
        terms = self.extractor.extract_terms(text)
        
        # Verify results
        self._verify_terms(terms, expected_terms)
        
        # Verify LOINC mapping for lab tests
        for term in terms:
            if term['type'] == 'LAB_TEST':
                self.assertEqual(term['terminology']['vocabulary'], 'LOINC', 
                               f"Lab test {term['text']} should map to LOINC")
    
    def test_biobert_integration(self):
        """Integration test for BioBERT processing if available."""
        # Skip test if BioBERT not available
        if not self.biobert_available:
            logger.info("Skipping BioBERT integration test - model not available")
            return
        
        # Get test text
        text = SAMPLE_TEXTS['clinical_note']
        
        # Process with standard extractor
        standard_terms = self.extractor.extract_terms(text)
        
        # Process with BioBERT extractor
        biobert_terms = self.online_extractor.extract_terms(text)
        
        # Verify BioBERT results
        self.assertGreater(len(biobert_terms), 0, "BioBERT should extract terms")
        
        # Log comparative results
        logger.info(f"Standard extraction: {len(standard_terms)} terms")
        logger.info(f"BioBERT extraction: {len(biobert_terms)} terms")
        
        # BioBERT should generally find all terms from pattern matching plus more
        standard_term_texts = {term['text'].lower() for term in standard_terms}
        biobert_term_texts = {term['text'].lower() for term in biobert_terms}
        
        # Calculate overlap and unique terms
        common_terms = standard_term_texts.intersection(biobert_term_texts)
        unique_to_standard = standard_term_texts - biobert_term_texts
        unique_to_biobert = biobert_term_texts - standard_term_texts
        
        logger.info(f"Common terms: {len(common_terms)}")
        logger.info(f"Terms unique to pattern matching: {len(unique_to_standard)}")
        logger.info(f"Terms unique to BioBERT: {len(unique_to_biobert)}")
        
        # BioBERT should generally find more unique terms
        if len(biobert_terms) > len(standard_terms) * 0.8:  # Allow some variance
            self.assertGreaterEqual(len(unique_to_biobert), len(unique_to_standard),
                                  "BioBERT should find additional terms beyond pattern matching")
    
    def test_component_integration(self):
        """Test integration of individual components."""
        # Get test text
        text = SAMPLE_TEXTS['procedures']
        
        # STEP 1: Preprocessing
        prepared = prepare_for_biobert(text)
        self.assertIn('chunks', prepared, "Preprocessing should produce chunks")
        
        # STEP 2: Process each chunk individually
        all_terms = []
        for chunk in prepared['chunks']:
            # Extract terms from chunk - using direct methods to test component integration
            if self.extractor.offline_mode:
                chunk_terms = self.extractor._extract_terms_offline(chunk['text'], 0.6)
            else:
                chunk_terms = self.extractor._extract_from_chunk(chunk['text'], 0.6)
            
            # Adjust positions based on chunk offset
            for term in chunk_terms:
                term['start'] += chunk['offset']
                term['end'] += chunk['offset']
                all_terms.append(term)
        
        # STEP 3: Deduplicate overlapping terms
        terms = self.extractor._resolve_overlapping_terms(all_terms)
        self.assertGreater(len(terms), 0, "Should extract terms from chunks")
        
        # STEP 4: Map to terminology
        if self.terminology_mapper:
            terms = self.terminology_mapper.map_terms(terms)
            
            # Verify mapping
            self._verify_terminology_mapping(terms)
        
        # Verify final results against expected terms
        expected_terms = EXPECTED_TERM_TYPES['procedures']
        self._verify_terms(terms, expected_terms)
    
    def test_error_handling(self):
        """Test error handling in the pipeline."""
        # Test with empty text
        terms = self.extractor.extract_terms("")
        self.assertEqual(len(terms), 0, "Empty text should return empty results")
        
        # Test with None
        terms = self.extractor.extract_terms(None)
        self.assertEqual(len(terms), 0, "None input should return empty results")
        
        # Test with very short text
        terms = self.extractor.extract_terms("Hello")
        self.assertEqual(len(terms), 0, "Very short non-medical text should return empty results")
        
        # Test with malformed text (mix of valid and invalid content)
        mixed_text = "Patient has hypertension.\n\x00\x1F Invalid characters \x7F\n More valid text about diabetes."
        terms = self.extractor.extract_terms(mixed_text)
        self.assertGreater(len(terms), 0, "Should extract terms despite some invalid content")
    
    def _verify_terms(self, terms: List[Dict[str, Any]], expected_terms: Dict[str, List[str]]):
        """Verify that extracted terms match expected terms."""
        # Extract term texts by type for easier comparison
        extracted_term_dict = {}
        for term in terms:
            term_type = term['type']
            if term_type not in extracted_term_dict:
                extracted_term_dict[term_type] = []
            extracted_term_dict[term_type].append(term['text'].lower())
        
        # Check each expected term type
        for term_type, expected_texts in expected_terms.items():
            # Verify this term type was found
            self.assertIn(term_type, extracted_term_dict, f"Should extract terms of type {term_type}")
            
            # Convert to sets for easier matching (account for variations in extraction)
            extracted_set = {t for t in extracted_term_dict[term_type]}
            
            # For each expected term, verify at least one extracted term contains it
            for expected_text in expected_texts:
                expected_text_lower = expected_text.lower()
                
                # Check if any extracted term contains this expected term
                found = False
                for extracted_text in extracted_set:
                    if expected_text_lower in extracted_text or extracted_text in expected_text_lower:
                        found = True
                        break
                
                self.assertTrue(found, f"Should extract term '{expected_text}' of type {term_type}")
    
    def _verify_terminology_mapping(self, terms: List[Dict[str, Any]]):
        """Verify that terminology mapping was performed correctly."""
        for term in terms:
            # Check terminology structure
            self.assertIn('terminology', term, f"Term '{term['text']}' should have terminology data")
            terminology = term['terminology']
            
            self.assertIn('vocabulary', terminology, "Terminology data should include vocabulary")
            self.assertIn('mapped', terminology, "Terminology data should indicate mapping status")
            
            # Verify correct vocabulary based on term type
            if term['type'] == 'CONDITION' or term['type'] == 'OBSERVATION':
                self.assertEqual(terminology['vocabulary'], 'SNOMED CT', 
                               f"Condition '{term['text']}' should map to SNOMED CT")
            elif term['type'] == 'MEDICATION':
                self.assertEqual(terminology['vocabulary'], 'RXNORM', 
                               f"Medication '{term['text']}' should map to RxNorm")
            elif term['type'] == 'LAB_TEST':
                self.assertEqual(terminology['vocabulary'], 'LOINC', 
                               f"Lab test '{term['text']}' should map to LOINC")
            elif term['type'] == 'PROCEDURE':
                self.assertIn(terminology['vocabulary'], ['SNOMED CT', 'LOINC'], 
                            f"Procedure '{term['text']}' should map to SNOMED CT or LOINC")


if __name__ == '__main__':
    unittest.main()