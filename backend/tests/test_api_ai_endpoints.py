"""
Test AI API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from api.main import app


client = TestClient(app)


class TestAIEndpoints:
    """Test AI-related API endpoints."""
    
    def test_ai_status_endpoint(self):
        """Test the AI status endpoint."""
        response = client.get("/api/v1/ai/status")
        assert response.status_code == 200
        
        data = response.json()
        assert 'ai_enabled' in data
        assert 'model_info' in data
        
        # Check model info structure when AI is enabled
        if data['ai_enabled']:
            assert 'model_name' in data['model_info']
            assert 'version' in data['model_info']
            assert 'device' in data['model_info']
    
    @patch('api.v1.routers.ai.terminology_service')
    def test_extract_and_map_endpoint(self, mock_service):
        """Test the extract and map endpoint."""
        # Mock the service response
        mock_service.extract_and_map_terms.return_value = {
            "extracted_terms": [
                {
                    "text": "diabetes",
                    "entity_type": "CONDITION",
                    "start_char": 12,
                    "end_char": 20,
                    "confidence": 0.95,
                    "mappings": [
                        {
                            "code": "73211009",
                            "display": "Diabetes mellitus",
                            "system": "snomed",
                            "confidence": 0.88
                        }
                    ]
                }
            ],
            "processing_time": 0.123
        }
        
        request_data = {
            "text": "Patient has diabetes",
            "terminology_system": "snomed"
        }
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 'extracted_terms' in data
        assert len(data['extracted_terms']) == 1
        
        term = data['extracted_terms'][0]
        assert term['text'] == 'diabetes'
        assert term['entity_type'] == 'CONDITION'
        assert 'mappings' in term
        assert len(term['mappings']) == 1
        assert term['mappings'][0]['system'] == 'snomed'
    
    @patch('api.v1.routers.ai.terminology_service')
    def test_extract_only_endpoint(self, mock_service):
        """Test the extract only endpoint."""
        # Mock the service response
        mock_service.extract_terms_only.return_value = {
            "extracted_terms": [
                {
                    "text": "hypertension",
                    "entity_type": "CONDITION",
                    "start_char": 23,
                    "end_char": 35,
                    "confidence": 0.92
                },
                {
                    "text": "lisinopril",
                    "entity_type": "MEDICATION",
                    "start_char": 48,
                    "end_char": 58,
                    "confidence": 0.89
                }
            ],
            "processing_time": 0.087
        }
        
        request_data = {
            "text": "Patient diagnosed with hypertension, prescribed lisinopril"
        }
        
        response = client.post("/api/v1/ai/extract-only", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 'extracted_terms' in data
        assert len(data['extracted_terms']) == 2
        
        # Check first term
        assert data['extracted_terms'][0]['text'] == 'hypertension'
        assert data['extracted_terms'][0]['entity_type'] == 'CONDITION'
        
        # Check second term
        assert data['extracted_terms'][1]['text'] == 'lisinopril'
        assert data['extracted_terms'][1]['entity_type'] == 'MEDICATION'
    
    def test_extract_empty_text(self):
        """Test extraction with empty text."""
        request_data = {"text": ""}
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data['extracted_terms'] == []
    
    def test_extract_invalid_system(self):
        """Test extraction with invalid terminology system."""
        request_data = {
            "text": "Patient has diabetes",
            "terminology_system": "invalid_system"
        }
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_extract_missing_text(self):
        """Test extraction without text field."""
        request_data = {}
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        assert response.status_code == 422  # Validation error
    
    @patch('api.v1.routers.ai.terminology_service')
    def test_extract_with_all_systems(self, mock_service):
        """Test extraction with all terminology systems."""
        # Mock the service response
        mock_service.extract_and_map_terms.return_value = {
            "extracted_terms": [
                {
                    "text": "diabetes",
                    "entity_type": "CONDITION",
                    "start_char": 12,
                    "end_char": 20,
                    "confidence": 0.95,
                    "mappings": [
                        {
                            "code": "73211009",
                            "display": "Diabetes mellitus",
                            "system": "snomed",
                            "confidence": 0.88
                        },
                        {
                            "code": "E11",
                            "display": "Type 2 diabetes mellitus",
                            "system": "icd10",
                            "confidence": 0.85
                        }
                    ]
                }
            ],
            "processing_time": 0.156
        }
        
        request_data = {
            "text": "Patient has diabetes",
            "terminology_system": "all"
        }
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        term = data['extracted_terms'][0]
        assert len(term['mappings']) == 2
        
        # Check that multiple systems are returned
        systems = {m['system'] for m in term['mappings']}
        assert 'snomed' in systems
        assert 'icd10' in systems
    
    @patch('api.v1.routers.ai.terminology_service')
    def test_extract_complex_clinical_text(self, mock_service):
        """Test extraction from complex clinical text."""
        clinical_text = """
        Chief Complaint: Chest pain and shortness of breath.
        History: 65-year-old male with diabetes, hypertension.
        Medications: metformin 1000mg BID, lisinopril 10mg daily.
        """
        
        # Mock complex response
        mock_service.extract_and_map_terms.return_value = {
            "extracted_terms": [
                {
                    "text": "Chest pain",
                    "entity_type": "CONDITION",
                    "start_char": 25,
                    "end_char": 35,
                    "confidence": 0.93,
                    "mappings": [{"code": "29857009", "display": "Chest pain", "system": "snomed", "confidence": 0.95}]
                },
                {
                    "text": "shortness of breath",
                    "entity_type": "CONDITION",
                    "start_char": 40,
                    "end_char": 59,
                    "confidence": 0.91,
                    "mappings": [{"code": "267036007", "display": "Dyspnea", "system": "snomed", "confidence": 0.89}]
                },
                {
                    "text": "diabetes",
                    "entity_type": "CONDITION",
                    "start_char": 110,
                    "end_char": 118,
                    "confidence": 0.95,
                    "mappings": [{"code": "73211009", "display": "Diabetes mellitus", "system": "snomed", "confidence": 0.92}]
                },
                {
                    "text": "hypertension",
                    "entity_type": "CONDITION",
                    "start_char": 120,
                    "end_char": 132,
                    "confidence": 0.94,
                    "mappings": [{"code": "38341003", "display": "Hypertensive disorder", "system": "snomed", "confidence": 0.90}]
                },
                {
                    "text": "metformin",
                    "entity_type": "MEDICATION",
                    "start_char": 148,
                    "end_char": 157,
                    "confidence": 0.96,
                    "mappings": [{"code": "6809", "display": "metformin", "system": "rxnorm", "confidence": 0.98}]
                },
                {
                    "text": "lisinopril",
                    "entity_type": "MEDICATION",
                    "start_char": 171,
                    "end_char": 181,
                    "confidence": 0.95,
                    "mappings": [{"code": "29046", "display": "lisinopril", "system": "rxnorm", "confidence": 0.97}]
                }
            ],
            "processing_time": 0.234
        }
        
        request_data = {
            "text": clinical_text,
            "terminology_system": "all"
        }
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data['extracted_terms']) == 6
        
        # Check entity type distribution
        conditions = [t for t in data['extracted_terms'] if t['entity_type'] == 'CONDITION']
        medications = [t for t in data['extracted_terms'] if t['entity_type'] == 'MEDICATION']
        
        assert len(conditions) == 4
        assert len(medications) == 2
        
        # Verify medications are mapped to RxNorm
        for med in medications:
            assert any(m['system'] == 'rxnorm' for m in med['mappings'])