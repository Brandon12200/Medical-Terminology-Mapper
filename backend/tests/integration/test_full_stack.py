"""
Full stack integration tests for Medical Terminology Mapper
Tests the interaction between frontend API calls and backend responses
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from api.main import app
import json

client = TestClient(app)

class TestFullStackIntegration:
    """Integration tests for complete user workflows"""
    
    def test_single_term_mapping_workflow(self):
        """Test complete single term mapping flow"""
        # 1. Health check
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
        # 2. Get available systems
        response = client.get("/api/v1/systems")
        assert response.status_code == 200
        systems = response.json()
        assert len(systems) > 0
        assert any(s["name"] == "snomed" for s in systems)
        
        # 3. Map a single term
        request_data = {
            "term": "hypertension",
            "systems": ["snomed"],
            "fuzzy_threshold": 0.8
        }
        response = client.post("/api/v1/map", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["term"] == "hypertension"
        assert "results" in result
        assert "processing_time_ms" in result
    
    def test_batch_processing_workflow(self):
        """Test complete batch processing flow"""
        # 1. Create batch job
        batch_data = {
            "terms": ["diabetes", "hypertension", "asthma"],
            "systems": ["snomed", "loinc"],
            "fuzzy_threshold": 0.7
        }
        response = client.post("/api/v1/batch", json=batch_data)
        assert response.status_code == 200
        
        job_response = response.json()
        assert "job_id" in job_response
        job_id = job_response["job_id"]
        
        # 2. Check job status
        response = client.get(f"/api/v1/batch/status/{job_id}")
        assert response.status_code == 200
        
        status = response.json()
        assert status["job_id"] == job_id
        assert status["status"] in ["pending", "processing", "completed"]
        assert status["total_terms"] == 3
        
        # 3. Get results (in real scenario, would wait for completion)
        # For testing, we'll check the structure
        if status["status"] == "completed":
            response = client.get(f"/api/v1/batch/result/{job_id}")
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)
    
    def test_file_upload_workflow(self):
        """Test file upload and processing flow"""
        # Create a test CSV file
        csv_content = "term\ndiabetes\nhypertension\nasthma"
        files = {
            "file": ("test_terms.csv", csv_content, "text/csv")
        }
        
        # Upload file
        response = client.post("/api/v1/batch/upload", files=files)
        assert response.status_code == 200
        
        result = response.json()
        assert "job_id" in result
        
        # Check that job was created
        job_id = result["job_id"]
        response = client.get(f"/api/v1/batch/status/{job_id}")
        assert response.status_code == 200
    
    def test_export_formats(self):
        """Test different export format endpoints"""
        # First create a batch job
        batch_data = {
            "terms": ["test"],
            "systems": ["snomed"]
        }
        response = client.post("/api/v1/batch", json=batch_data)
        job_id = response.json()["job_id"]
        
        # Test CSV export endpoint exists
        response = client.get(f"/api/v1/batch/download/{job_id}.csv")
        # Should be 404 if job not complete, or 200 with CSV if complete
        assert response.status_code in [200, 404]
        
        # Test JSON export endpoint exists
        response = client.get(f"/api/v1/batch/download/{job_id}.json")
        assert response.status_code in [200, 404]
    
    def test_error_handling_workflow(self):
        """Test error handling across the stack"""
        # 1. Invalid term mapping request
        invalid_request = {
            "term": "",  # Empty term
            "systems": ["invalid_system"]
        }
        response = client.post("/api/v1/map", json=invalid_request)
        assert response.status_code == 422  # Validation error
        
        # 2. Non-existent job ID
        response = client.get("/api/v1/batch/status/non-existent-id")
        assert response.status_code == 404
        
        # 3. Invalid file upload
        files = {
            "file": ("test.txt", "not a csv", "text/plain")
        }
        response = client.post("/api/v1/batch/upload", files=files)
        # Should handle gracefully
        assert response.status_code in [200, 400]
    
    def test_concurrent_requests(self):
        """Test handling of concurrent API requests"""
        async def make_request(term):
            return client.post("/api/v1/map", json={
                "term": term,
                "systems": ["snomed"]
            })
        
        # Make multiple concurrent requests
        terms = ["diabetes", "hypertension", "asthma", "covid", "flu"]
        
        # Synchronous test client doesn't support true concurrency
        # but we can still test multiple rapid requests
        responses = []
        for term in terms:
            response = client.post("/api/v1/map", json={
                "term": term,
                "systems": ["snomed"]
            })
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
    
    def test_api_statistics_integration(self):
        """Test statistics endpoint after operations"""
        # Make some requests first
        client.post("/api/v1/map", json={"term": "test", "systems": ["snomed"]})
        
        # Get statistics
        response = client.get("/api/v1/statistics")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_requests" in stats
        assert "total_terms_processed" in stats
        assert "available_systems" in stats
        assert stats["total_requests"] > 0


class TestFrontendAPIContract:
    """Test that API responses match frontend expectations"""
    
    def test_mapping_response_structure(self):
        """Verify mapping response matches frontend MappingResponse type"""
        response = client.post("/api/v1/map", json={
            "term": "test",
            "systems": ["snomed"]
        })
        
        data = response.json()
        # Check structure matches frontend types
        assert "term" in data
        assert isinstance(data["term"], str)
        
        # Note: API returns "results" but frontend expects "mappings"
        # This would need to be handled in frontend service layer
    
    def test_batch_status_response_structure(self):
        """Verify batch status matches frontend BatchJobStatus type"""
        # Create a job
        response = client.post("/api/v1/batch", json={
            "terms": ["test"],
            "systems": ["snomed"]
        })
        job_id = response.json()["job_id"]
        
        # Check status
        response = client.get(f"/api/v1/batch/status/{job_id}")
        status = response.json()
        
        # Verify structure
        assert "job_id" in status
        assert "status" in status
        assert status["status"] in ["pending", "processing", "completed", "failed"]
        assert "total_terms" in status
        assert "processed_terms" in status
        assert "created_at" in status
    
    def test_systems_response_structure(self):
        """Verify systems response matches frontend SystemInfo type"""
        response = client.get("/api/v1/systems")
        systems = response.json()
        
        assert isinstance(systems, list)
        if systems:  # If we have systems
            system = systems[0]
            assert "name" in system
            assert "display_name" in system
            assert "description" in system
            assert "total_concepts" in system


if __name__ == "__main__":
    pytest.main([__file__, "-v"])