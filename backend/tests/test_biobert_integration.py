"""
Tests for BioBERT integration and entity extraction

This test suite covers the BioBERT model manager, service, and API endpoints
to ensure proper functionality of medical entity extraction.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from app.ml.biobert.model_manager import BioBERTModelManager, EntityPrediction
from app.ml.biobert.biobert_service import BioBERTService, MedicalEntity
from app.extractors.term_extractor import EnhancedTermExtractor


class TestBioBERTModelManager:
    """Test BioBERT model manager functionality"""
    
    def test_singleton_pattern(self):
        """Test that model manager follows singleton pattern"""
        manager1 = BioBERTModelManager()
        manager2 = BioBERTModelManager()
        assert manager1 is manager2
    
    def test_model_info(self):
        """Test getting model information"""
        manager = BioBERTModelManager()
        info = manager.get_model_info()
        
        assert "model_name" in info
        assert "is_loaded" in info
        assert "entity_types" in info
        assert "max_length" in info
        assert info["model_name"] == "dmis-lab/biobert-base-cased-v1.2"
        assert info["entity_types"] == ["CONDITION", "MEDICATION", "PROCEDURE", "LAB_TEST", "OBSERVATION"]
    
    @patch('torch.cuda.is_available')
    @patch('app.ml.biobert.model_manager.AutoTokenizer')
    @patch('app.ml.biobert.model_manager.AutoModelForTokenClassification')
    def test_model_initialization_success(self, mock_model, mock_tokenizer, mock_cuda):
        """Test successful model initialization"""
        # Mock CUDA availability
        mock_cuda.return_value = False
        
        # Mock tokenizer and model
        mock_tokenizer.from_pretrained.return_value = Mock()
        mock_model.from_pretrained.return_value = Mock()
        
        manager = BioBERTModelManager()
        success = manager.initialize_model()
        
        assert success is True
        assert manager._is_loaded is True
        mock_tokenizer.from_pretrained.assert_called_once()
        mock_model.from_pretrained.assert_called_once()
    
    def test_extract_entities_without_initialization(self):
        """Test entity extraction without model initialization"""
        manager = BioBERTModelManager()
        manager._is_loaded = False
        
        # Should attempt initialization and return empty list on failure
        entities = manager.extract_entities("Patient has diabetes")
        assert entities == []
    
    @patch('app.ml.biobert.model_manager.pipeline')
    def test_extract_entities_with_mock_pipeline(self, mock_pipeline):
        """Test entity extraction with mocked pipeline"""
        # Mock pipeline results
        mock_pipeline.return_value = [
            {
                'word': 'diabetes',
                'entity_group': 'CONDITION',
                'start': 12,
                'end': 20,
                'score': 0.95
            }
        ]
        
        manager = BioBERTModelManager()
        manager._is_loaded = True
        manager.pipeline = mock_pipeline.return_value
        
        entities = manager.extract_entities("Patient has diabetes", confidence_threshold=0.7)
        
        assert len(entities) == 1
        assert entities[0].text == 'diabetes'
        assert entities[0].entity_type == 'CONDITION'
        assert entities[0].confidence == 0.95


class TestBioBERTService:
    """Test BioBERT service functionality"""
    
    @pytest.fixture
    def mock_model_manager(self):
        """Mock model manager for testing"""
        manager = Mock()
        manager.extract_entities.return_value = [
            EntityPrediction(
                text="diabetes",
                entity_type="CONDITION",
                start=12,
                end=20,
                confidence=0.95,
                token_indices=[1, 2]
            )
        ]
        manager.get_model_info.return_value = {
            "is_loaded": True,
            "model_name": "test-model"
        }
        return manager
    
    @patch('app.ml.biobert.biobert_service.get_biobert_manager')
    def test_service_initialization(self, mock_get_manager, mock_model_manager):
        """Test BioBERT service initialization"""
        mock_get_manager.return_value = mock_model_manager
        
        service = BioBERTService(
            use_regex_patterns=True,
            use_ensemble=True,
            confidence_threshold=0.8
        )
        
        assert service.confidence_threshold == 0.8
        assert service.use_ensemble is True
        assert service.use_regex_patterns is True
    
    @patch('app.ml.biobert.biobert_service.get_biobert_manager')
    def test_extract_entities(self, mock_get_manager, mock_model_manager):
        """Test entity extraction from service"""
        mock_get_manager.return_value = mock_model_manager
        
        service = BioBERTService()
        entities = service.extract_entities("Patient has diabetes mellitus")
        
        assert len(entities) == 1
        assert entities[0].text == "diabetes"
        assert entities[0].entity_type == "CONDITION"
        assert entities[0].confidence == 0.95
    
    @patch('app.ml.biobert.biobert_service.get_biobert_manager')
    def test_analyze_document(self, mock_get_manager, mock_model_manager):
        """Test document analysis"""
        mock_get_manager.return_value = mock_model_manager
        
        service = BioBERTService()
        analysis = service.analyze_document("Patient has diabetes mellitus type 2")
        
        assert "entities" in analysis
        assert "entity_summary" in analysis
        assert "processing_time" in analysis
        assert len(analysis.entities) == 1
        assert analysis.entity_summary["CONDITION"] == 1
    
    @patch('app.ml.biobert.biobert_service.get_biobert_manager')
    def test_confidence_filtering(self, mock_get_manager, mock_model_manager):
        """Test that entities below confidence threshold are filtered"""
        # Mock low confidence entity
        mock_model_manager.extract_entities.return_value = [
            EntityPrediction(
                text="diabetes",
                entity_type="CONDITION",
                start=12,
                end=20,
                confidence=0.5,  # Below default threshold of 0.7
                token_indices=[1, 2]
            )
        ]
        mock_get_manager.return_value = mock_model_manager
        
        service = BioBERTService(confidence_threshold=0.7)
        entities = service.extract_entities("Patient has diabetes")
        
        # Should be filtered out due to low confidence
        assert len(entities) == 0


class TestEnhancedTermExtractor:
    """Test enhanced term extractor"""
    
    @patch('app.extractors.term_extractor.create_biobert_service')
    def test_initialization(self, mock_create_service):
        """Test enhanced term extractor initialization"""
        mock_service = Mock()
        mock_create_service.return_value = mock_service
        
        extractor = EnhancedTermExtractor(
            use_cache=True,
            confidence_threshold=0.8,
            use_terminology_mapping=True
        )
        
        assert extractor.confidence_threshold == 0.8
        assert extractor.use_cache is True
        mock_create_service.assert_called_once()
    
    @patch('app.extractors.term_extractor.create_biobert_service')
    def test_extract_terms_legacy_format(self, mock_create_service):
        """Test that extracted terms are in legacy format"""
        # Mock BioBERT service
        mock_service = Mock()
        mock_entity = MedicalEntity(
            text="diabetes",
            normalized_text="diabetes",
            entity_type="CONDITION",
            start_position=12,
            end_position=20,
            confidence=0.95,
            source="biobert",
            context="Patient has [diabetes] mellitus",
            terminology_mappings={"snomed": [{"code": "73211009", "display": "Diabetes mellitus"}]}
        )
        mock_service.extract_entities.return_value = [mock_entity]
        mock_create_service.return_value = mock_service
        
        extractor = EnhancedTermExtractor()
        terms = extractor.extract_terms("Patient has diabetes")
        
        assert len(terms) == 1
        term = terms[0]
        assert term["text"] == "diabetes"
        assert term["type"] == "CONDITION"
        assert term["start"] == 12
        assert term["end"] == 20
        assert term["confidence"] == 0.95
        assert term["source"] == "biobert"
        assert "terminology" in term
        assert term["terminology"]["mapped"] is True


@pytest.mark.asyncio
class TestBioBERTAPI:
    """Test BioBERT API endpoints"""
    
    @pytest.fixture
    def mock_service(self):
        """Mock BioBERT service for API testing"""
        service = Mock()
        service.extract_entities.return_value = [
            MedicalEntity(
                text="diabetes",
                normalized_text="diabetes",
                entity_type="CONDITION",
                start_position=12,
                end_position=20,
                confidence=0.95,
                source="biobert"
            )
        ]
        service.get_service_info.return_value = {
            "service": "BioBERT Medical Entity Recognition",
            "model": {"is_loaded": True},
            "configuration": {"confidence_threshold": 0.7}
        }
        return service
    
    @patch('api.v1.routers.ai.get_biobert_service')
    async def test_extract_entities_endpoint(self, mock_get_service, mock_service):
        """Test entity extraction endpoint"""
        mock_get_service.return_value = mock_service
        
        from api.v1.routers.ai import extract_entities, EntityExtractionRequest
        
        request = EntityExtractionRequest(
            text="Patient has diabetes mellitus",
            confidence_threshold=0.7,
            extract_context=True,
            map_to_terminologies=True,
            use_ensemble=True
        )
        
        response = await extract_entities(request)
        
        assert response.entity_count == 1
        assert len(response.entities) == 1
        assert response.entities[0].text == "diabetes"
        assert response.entities[0].entity_type == "CONDITION"
    
    @patch('api.v1.routers.ai.get_biobert_service')
    async def test_model_status_endpoint(self, mock_get_service, mock_service):
        """Test model status endpoint"""
        mock_get_service.return_value = mock_service
        
        from api.v1.routers.ai import get_model_status
        
        response = await get_model_status()
        
        assert response.service_name == "BioBERT Medical Entity Recognition"
        assert response.model_loaded is True


class TestIntegration:
    """Integration tests for the complete BioBERT pipeline"""
    
    def test_sample_medical_texts(self):
        """Test extraction on sample medical texts"""
        # Sample medical texts for testing
        sample_texts = [
            "Patient has diabetes mellitus type 2 and hypertension",
            "Prescribed metformin 500mg twice daily",
            "Blood glucose level 126 mg/dL, HbA1c 7.2%",
            "CT scan showed no acute findings"
        ]
        
        # This would be an integration test that requires actual model loading
        # For unit testing, we'll mock the components
        
        with patch('app.ml.biobert.model_manager.AutoTokenizer'), \
             patch('app.ml.biobert.model_manager.AutoModelForTokenClassification'), \
             patch('torch.cuda.is_available', return_value=False):
            
            service = BioBERTService()
            
            # Mock the model manager to return realistic entities
            service.model_manager.extract_entities = Mock(return_value=[
                EntityPrediction("diabetes", "CONDITION", 12, 20, 0.95, []),
                EntityPrediction("metformin", "MEDICATION", 10, 18, 0.92, [])
            ])
            
            for text in sample_texts[:2]:  # Test first 2 samples
                entities = service.extract_entities(text)
                assert isinstance(entities, list)
                # Should extract at least one entity from medical text
                assert len(entities) >= 1 if "diabetes" in text or "metformin" in text else True


if __name__ == "__main__":
    pytest.main([__file__])