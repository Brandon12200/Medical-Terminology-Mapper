"""Test API endpoints for the Medical Terminology Mapper API."""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data

def test_get_systems():
    """Test systems endpoint."""
    response = client.get("/api/v1/systems")
    assert response.status_code == 200
    data = response.json()
    assert "systems" in data
    assert len(data["systems"]) > 0
    
    # Check system structure
    system = data["systems"][0]
    assert "name" in system
    assert "display_name" in system
    assert "description" in system
    assert "supported" in system

def test_get_fuzzy_algorithms():
    """Test fuzzy algorithms endpoint."""
    response = client.get("/api/v1/fuzzy-algorithms")
    assert response.status_code == 200
    data = response.json()
    assert "algorithms" in data
    assert len(data["algorithms"]) > 0
    
    # Check algorithm structure
    algo = data["algorithms"][0]
    assert "name" in algo
    assert "display_name" in algo
    assert "description" in algo
    assert "best_for" in algo

def test_map_term_post():
    """Test term mapping with POST."""
    request_data = {
        "term": "diabetes",
        "systems": ["snomed"],
        "fuzzy_threshold": 0.7,
        "max_results": 5
    }
    
    response = client.post("/api/v1/map", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "term" in data
    assert data["term"] == "diabetes"
    assert "results" in data
    assert "total_matches" in data
    assert "processing_time_ms" in data

def test_map_term_get():
    """Test term mapping with GET."""
    response = client.get("/api/v1/map?term=hypertension&systems=snomed&max_results=3")
    assert response.status_code == 200
    data = response.json()
    
    assert "term" in data
    assert data["term"] == "hypertension"
    assert "results" in data
    assert "processing_time_ms" in data

def test_batch_mapping():
    """Test batch mapping endpoint."""
    request_data = {
        "terms": ["diabetes", "hypertension", "aspirin"],
        "systems": ["snomed", "rxnorm"],
        "max_results_per_term": 3
    }
    
    response = client.post("/api/v1/batch", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "results" in data
    assert "total_terms" in data
    assert data["total_terms"] == 3
    assert "successful_mappings" in data
    assert "failed_mappings" in data
    assert "total_processing_time_ms" in data
    
    # Check results structure
    assert len(data["results"]) == 3
    for result in data["results"]:
        assert "term" in result
        assert "results" in result
        assert "total_matches" in result

def test_invalid_term_mapping():
    """Test mapping with invalid parameters."""
    request_data = {
        "term": "",  # Empty term
        "systems": ["snomed"]
    }
    
    response = client.post("/api/v1/map", json=request_data)
    assert response.status_code == 422  # Validation error

def test_statistics_endpoint():
    """Test statistics endpoint."""
    response = client.get("/api/v1/statistics")
    assert response.status_code == 200
    data = response.json()
    
    assert "database_status" in data
    assert "cache_status" in data
    assert "performance" in data

def test_context_aware_mapping():
    """Test term mapping with context."""
    request_data = {
        "term": "glucose",
        "systems": ["loinc"],
        "context": "diabetes monitoring",
        "max_results": 5
    }
    
    response = client.post("/api/v1/map", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "term" in data
    assert "results" in data
    # Context should potentially improve results

def test_multiple_systems_mapping():
    """Test mapping across multiple systems."""
    request_data = {
        "term": "insulin",
        "systems": ["snomed", "rxnorm", "loinc"],
        "max_results": 3
    }
    
    response = client.post("/api/v1/map", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "results" in data
    # Should have results from multiple systems if available

def test_fuzzy_algorithm_selection():
    """Test specific fuzzy algorithm selection."""
    request_data = {
        "term": "diabetis",  # Misspelled
        "systems": ["snomed"],
        "fuzzy_algorithms": ["phonetic", "levenshtein"],
        "fuzzy_threshold": 0.6,
        "max_results": 5
    }
    
    response = client.post("/api/v1/map", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "results" in data
    # Should find matches despite misspelling

if __name__ == "__main__":
    pytest.main([__file__, "-v"])