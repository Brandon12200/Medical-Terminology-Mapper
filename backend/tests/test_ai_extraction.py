"""
Test AI-powered term extraction functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import torch

from app.extractors.term_extractor import TermExtractor


class TestTermExtractor:
    """Test the TermExtractor AI functionality."""
    
    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager."""
        # Mock model manager instance
        mock_manager = Mock()
        
        # Mock tokenizer
        mock_tokenizer = Mock()
        mock_tokenizer.return_value = {
            'input_ids': torch.tensor([[101, 2030, 2003, 102]]),
            'attention_mask': torch.tensor([[1, 1, 1, 1]]),
            'offset_mapping': [(0, 0), (0, 7), (8, 11), (0, 0)]
        }
        
        # Mock model
        mock_model = Mock()
        mock_output = Mock()
        mock_output.logits = torch.randn(1, 4, 11)  # batch_size, seq_len, num_labels
        mock_model.return_value = mock_output
        
        # Setup get methods
        mock_manager.get_tokenizer.return_value = mock_tokenizer
        mock_manager.get_model.return_value = mock_model
        mock_manager.is_initialized = True
        
        return mock_manager
    
    def test_extract_terms_basic(self, mock_model_manager):
        """Test basic term extraction."""
        extractor = TermExtractor(model_manager=mock_model_manager)
        text = "Patient has diabetes"
        
        # Mock predictions
        with patch.object(extractor, '_post_process_predictions') as mock_post:
            mock_post.return_value = [
                {
                    'text': 'diabetes',
                    'entity_type': 'CONDITION',
                    'start_char': 12,
                    'end_char': 20,
                    'confidence': 0.95
                }
            ]
            
            terms = extractor.extract_terms(text)
            
            assert len(terms) == 1
            assert terms[0]['text'] == 'diabetes'
            assert terms[0]['entity_type'] == 'CONDITION'
            assert terms[0]['confidence'] == 0.95
    
    def test_extract_terms_multiple(self, mock_model_manager):
        """Test extraction of multiple terms."""
        extractor = TermExtractor(model_manager=mock_model_manager)
        text = "Patient diagnosed with hypertension, prescribed lisinopril"
        
        # Mock predictions
        with patch.object(extractor, '_post_process_predictions') as mock_post:
            mock_post.return_value = [
                {
                    'text': 'hypertension',
                    'entity_type': 'CONDITION',
                    'start_char': 23,
                    'end_char': 35,
                    'confidence': 0.92
                },
                {
                    'text': 'lisinopril',
                    'entity_type': 'MEDICATION',
                    'start_char': 48,
                    'end_char': 58,
                    'confidence': 0.89
                }
            ]
            
            terms = extractor.extract_terms(text)
            
            assert len(terms) == 2
            assert terms[0]['text'] == 'hypertension'
            assert terms[0]['entity_type'] == 'CONDITION'
            assert terms[1]['text'] == 'lisinopril'
            assert terms[1]['entity_type'] == 'MEDICATION'
    
    def test_extract_terms_empty_text(self, mock_model_manager):
        """Test extraction with empty text."""
        extractor = TermExtractor(model_manager=mock_model_manager)
        
        terms = extractor.extract_terms("")
        assert terms == []
        
        terms = extractor.extract_terms("   ")
        assert terms == []
    
    def test_extract_terms_no_medical_terms(self, mock_model_manager):
        """Test extraction when no medical terms are found."""
        extractor = TermExtractor(model_manager=mock_model_manager)
        text = "The weather is nice today"
        
        # Mock no predictions
        with patch.object(extractor, '_post_process_predictions') as mock_post:
            mock_post.return_value = []
            
            terms = extractor.extract_terms(text)
            assert terms == []
    
    def test_extract_terms_with_negation(self, mock_model_manager):
        """Test extraction handles negated terms."""
        extractor = TermExtractor(model_manager=mock_model_manager)
        text = "Patient denies chest pain"
        
        # Mock predictions
        with patch.object(extractor, '_post_process_predictions') as mock_post:
            mock_post.return_value = [
                {
                    'text': 'chest pain',
                    'entity_type': 'CONDITION',
                    'start_char': 15,
                    'end_char': 25,
                    'confidence': 0.88,
                    'negated': True
                }
            ]
            
            terms = extractor.extract_terms(text)
            
            assert len(terms) == 1
            assert terms[0]['text'] == 'chest pain'
            assert terms[0].get('negated') == True
    
    def test_extract_terms_offline_mode(self, mock_model_manager):
        """Test extraction in offline mode using pattern matching."""
        # Create extractor in offline mode
        extractor = TermExtractor(model_manager=mock_model_manager, offline_mode=True)
        text = "Patient has type 2 diabetes mellitus and takes metformin 500mg"
        
        # In offline mode, it should use pattern matching
        terms = extractor.extract_terms(text)
        
        # Should find at least diabetes and metformin
        term_texts = [t['text'].lower() for t in terms]
        assert any('diabetes' in text for text in term_texts)
        assert any('metformin' in text for text in term_texts)
    
    def test_extract_terms_with_cache(self, mock_model_manager):
        """Test that caching works for repeated terms."""
        extractor = TermExtractor(model_manager=mock_model_manager, use_cache=True)
        text1 = "Patient has diabetes"
        text2 = "Another patient with diabetes"
        
        # Mock predictions
        with patch.object(extractor, '_post_process_predictions') as mock_post:
            mock_post.return_value = [
                {
                    'text': 'diabetes',
                    'entity_type': 'CONDITION',
                    'start_char': 12,
                    'end_char': 20,
                    'confidence': 0.95
                }
            ]
            
            # Extract from first text
            terms1 = extractor.extract_terms(text1)
            
            # Extract from second text - should use cache
            terms2 = extractor.extract_terms(text2)
            
            # Both should find diabetes
            assert any(t['text'] == 'diabetes' for t in terms1)
            assert any(t['text'] == 'diabetes' for t in terms2)