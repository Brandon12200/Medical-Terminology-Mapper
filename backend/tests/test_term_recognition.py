"""
Test module for term recognition in Medical Terminology Mapper.
This module contains tests for the term extraction and BioBERT processing pipeline.
"""

import os
import sys
import unittest
import logging
from typing import List, Dict, Any

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from app.models.model_loader import ModelManager
from app.extractors.term_extractor import TermExtractor
from app.models.preprocessing import clean_text, chunk_document, prepare_for_biobert

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestTermRecognition(unittest.TestCase):
    """Test cases for term recognition functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test resources before any tests run."""
        # Initialize model manager in offline mode for faster testing
        cls.model_manager = ModelManager()
        cls.model_manager.initialize()
        
        # Create term extractor with offline mode for faster testing
        cls.term_extractor = TermExtractor(
            cls.model_manager,
            use_cache=False,  # Disable caching for testing
            offline_mode=True,  # Use offline mode for faster testing
            confidence_threshold=0.6  # Lower threshold for testing
        )
        
        # Create another extractor for BioBERT tests (if available)
        try:
            cls.biobert_extractor = TermExtractor(
                cls.model_manager,
                use_cache=False,
                offline_mode=False,  # Use BioBERT if available
                confidence_threshold=0.6
            )
        except Exception as e:
            logger.warning(f"BioBERT test extractor init failed: {e}. Some tests will be skipped.")
            cls.biobert_extractor = None
    
    def test_text_cleaning(self):
        """Test that the text cleaning preserves medical terminology."""
        sample_text = """The patient was prescribed atorvastatin 40mg daily for hypercholesterolemia.
        Blood pressure was 140/90mmHg, and HbA1c was 7.2%."""
        
        cleaned = clean_text(sample_text)
        
        # Check that medical terms are preserved
        self.assertIn("atorvastatin 40mg", cleaned)
        self.assertIn("hypercholesterolemia", cleaned)
        self.assertIn("140/90mmHg", cleaned)
        self.assertIn("HbA1c", cleaned)
        self.assertIn("7.2%", cleaned)
    
    def test_text_chunking(self):
        """Test document chunking for BioBERT processing."""
        long_text = """
        The patient has a history of hypertension, diabetes mellitus type 2, and hypercholesterolemia.
        Current medications include metformin 1000mg twice daily, lisinopril 20mg daily, and atorvastatin 40mg at bedtime.
        Recent lab tests show HbA1c of 7.2%, total cholesterol of 180mg/dL, and fasting glucose of 130mg/dL.
        The patient reports occasional headaches and dizziness, especially in the morning.
        Physical examination reveals BP of 138/88mmHg, heart rate 72bpm, and respiratory rate 16.
        Neurological examination is within normal limits. No signs of peripheral neuropathy detected.
        """ * 5  # Repeat to make it longer
        
        # Test basic chunking
        chunks = chunk_document(long_text, max_length=200, overlap=50)
        self.assertTrue(len(chunks) > 1, "Text should be split into multiple chunks")
        
        # Check that chunks have correct format
        for chunk in chunks:
            self.assertIn('text', chunk)
            self.assertIn('offset', chunk)
            self.assertIsInstance(chunk['offset'], int)
        
        # Test BioBERT-optimized preparation
        prepared = prepare_for_biobert(long_text)
        self.assertIn('chunks', prepared)
        self.assertIn('text', prepared)
        self.assertIn('stats', prepared)
    
    def test_offline_term_extraction(self):
        """Test offline term extraction with regex patterns."""
        text = """
        Patient presents with diabetes mellitus type 2 and hypertension.
        Currently taking metformin 500mg twice daily and lisinopril 10mg daily.
        Recent blood tests show elevated HbA1c of 8.5% and total cholesterol of 220mg/dL.
        """
        
        terms = self.term_extractor.extract_terms(text)
        
        # Check that key terms were extracted
        term_texts = [term['text'].lower() for term in terms]
        
        # Medications
        self.assertTrue(any('metformin' in t for t in term_texts))
        self.assertTrue(any('lisinopril' in t for t in term_texts))
        
        # Conditions
        self.assertTrue(any('diabetes' in t for t in term_texts))
        self.assertTrue(any('hypertension' in t for t in term_texts))
        
        # Lab tests
        self.assertTrue(any('hba1c' in t for t in term_texts))
        self.assertTrue(any('cholesterol' in t for t in term_texts))
    
    def test_term_types(self):
        """Test that terms are assigned the correct types."""
        text = """
        Patient diagnosed with pneumonia and prescribed amoxicillin 500mg three times daily.
        Chest X-ray shows right lower lobe infiltrate. White blood cell count is 12,000/mm3.
        """
        
        terms = self.term_extractor.extract_terms(text)
        
        # Create dictionaries for easier checking
        term_dict = {term['text'].lower(): term for term in terms}
        
        # Check condition
        self.assertIn('pneumonia', term_dict)
        self.assertEqual(term_dict['pneumonia']['type'], 'CONDITION')
        
        # Check medication
        self.assertTrue(any('amoxicillin' in t.lower() for t in term_dict.keys()))
        amoxicillin_term = next(term for term in terms if 'amoxicillin' in term['text'].lower())
        self.assertEqual(amoxicillin_term['type'], 'MEDICATION')
        
        # Check procedure
        self.assertTrue(any('x-ray' in t.lower() for t in term_dict.keys()))
        xray_term = next(term for term in terms if 'x-ray' in term['text'].lower())
        self.assertEqual(xray_term['type'], 'PROCEDURE')
        
        # Check lab test
        self.assertTrue(any('white blood cell' in t.lower() for t in term_dict.keys()))
        wbc_term = next(term for term in terms if 'white blood cell' in term['text'].lower())
        self.assertEqual(wbc_term['type'], 'LAB_TEST')
    
    def test_biobert_extraction(self):
        """Test BioBERT-based term extraction if available."""
        # Skip if BioBERT extractor not available
        if not self.biobert_extractor or self.biobert_extractor.offline_mode:
            logger.info("Skipping BioBERT test as it's not available")
            return
        
        text = """
        Patient presents with chronic obstructive pulmonary disease (COPD) and was recently hospitalized
        for an acute exacerbation. Current medications include albuterol inhaler, tiotropium bromide,
        and prednisone 40mg daily with taper. Pulmonary function tests show FEV1 of 60% predicted.
        """
        
        terms = self.biobert_extractor.extract_terms(text)
        
        # Check that key terms were extracted
        term_texts = [term['text'].lower() for term in terms]
        
        # Must-have terms
        self.assertTrue(any('copd' in t or 'pulmonary disease' in t for t in term_texts))
        self.assertTrue(any('albuterol' in t for t in term_texts))
        self.assertTrue(any('prednisone' in t for t in term_texts))
        
        # Check confidence scores
        for term in terms:
            self.assertIn('confidence', term)
            self.assertGreaterEqual(term['confidence'], 0.6)
    
    def test_terminology_integration(self):
        """Test integration with terminology databases."""
        # Create extractor with terminology integration enabled
        term_extractor_with_terminology = TermExtractor(
            self.model_manager,
            use_cache=False,
            offline_mode=True,
            use_terminology=True
        )
        
        text = "Patient has hypertension and diabetes mellitus type 2."
        
        terms = term_extractor_with_terminology.extract_terms(text)
        
        # Check terminology data structure
        for term in terms:
            self.assertIn('terminology', term)
            self.assertIn('vocabulary', term['terminology'])
            self.assertIn('mapped', term['terminology'])
            
            # Verify vocabulary assignment
            if term['type'] == 'CONDITION':
                self.assertEqual(term['terminology']['vocabulary'], 'SNOMED CT')
            elif term['type'] == 'MEDICATION':
                self.assertEqual(term['terminology']['vocabulary'], 'RXNORM')
            elif term['type'] == 'LAB_TEST':
                self.assertEqual(term['terminology']['vocabulary'], 'LOINC')


if __name__ == '__main__':
    unittest.main()