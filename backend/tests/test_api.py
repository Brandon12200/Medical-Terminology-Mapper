#!/usr/bin/env python
"""
Simple test script to verify API endpoints are working.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_systems():
    """Test systems endpoint."""
    print("Testing systems endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/systems")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_fuzzy_algorithms():
    """Test fuzzy algorithms endpoint."""
    print("Testing fuzzy algorithms endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/fuzzy-algorithms")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_map_term():
    """Test term mapping endpoint."""
    print("Testing term mapping...")
    
    # Test with POST
    data = {
        "term": "diabetes type 2",
        "systems": ["snomed"],
        "fuzzy_threshold": 0.8,
        "max_results": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/map",
        json=data
    )
    print(f"POST Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    # Test with GET
    response = requests.get(
        f"{BASE_URL}/api/v1/map",
        params={
            "term": "hypertension",
            "systems": ["snomed", "loinc"],
            "max_results": 3
        }
    )
    print(f"GET Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_batch_mapping():
    """Test batch mapping endpoint."""
    print("Testing batch mapping...")
    
    data = {
        "terms": ["diabetes", "hypertension", "aspirin"],
        "systems": ["snomed", "rxnorm"],
        "max_results_per_term": 3
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/batch",
        json=data
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def main():
    """Run all tests."""
    print("Testing Medical Terminology Mapper API")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    try:
        test_health_check()
        test_systems()
        test_fuzzy_algorithms()
        test_map_term()
        test_batch_mapping()
        
        print("\nAll tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API. Make sure the server is running.")
        print("Run: python run_api.py")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    main()