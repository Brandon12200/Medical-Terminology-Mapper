#!/usr/bin/env python3
"""Test script for external API services."""

import json
from app.standards.terminology.api_services import TerminologyAPIService
from app.standards.terminology.mapper import TerminologyMapper

def test_direct_api():
    """Test direct API calls."""
    print("Testing Direct API Services\n" + "="*50)
    
    api_service = TerminologyAPIService()
    
    # Test RxNorm
    print("\n1. Testing RxNorm API:")
    print("-" * 30)
    rxnorm_results = api_service.search_rxnorm("aspirin")
    for result in rxnorm_results[:3]:
        print(f"  - {result['display']} ({result['code']}) [TTY: {result.get('tty', 'N/A')}]")
    
    # Test Clinical Tables
    print("\n2. Testing Clinical Tables API:")
    print("-" * 30)
    
    # RxTerms
    print("  RxTerms (medications):")
    rx_results = api_service.search_clinical_tables("metformin", "rxterms")
    for result in rx_results[:3]:
        print(f"    - {result['display']} ({result.get('code', 'N/A')})")
    
    # LOINC
    print("\n  LOINC (lab tests):")
    loinc_results = api_service.search_clinical_tables("glucose", "loinc")
    for result in loinc_results[:3]:
        print(f"    - {result['display']} ({result['code']})")
    
    # ICD-10
    print("\n  ICD-10 (diagnoses):")
    icd_results = api_service.search_clinical_tables("diabetes", "icd10")
    for result in icd_results[:3]:
        print(f"    - {result['display']} ({result['code']})")
    
    # SNOMED
    print("\n  SNOMED CT:")
    snomed_results = api_service.search_clinical_tables("hypertension", "snomed")
    for result in snomed_results[:3]:
        print(f"    - {result['display']} ({result['code']})")
    
    # Test SNOMED Browser
    print("\n3. Testing SNOMED Browser API:")
    print("-" * 30)
    snomed_browser_results = api_service.search_snomed_browser("pneumonia")
    for result in snomed_browser_results[:3]:
        print(f"  - {result['display']} ({result['code']})")
        if result.get('fsn'):
            print(f"    FSN: {result['fsn']}")
    
    # Test multi-system search
    print("\n4. Testing Multi-System Search:")
    print("-" * 30)
    multi_results = api_service.search_all("heart failure")
    for system, results in multi_results.items():
        print(f"\n  {system.upper()}:")
        for result in results[:2]:
            print(f"    - {result['display']} ({result.get('code', 'N/A')})")


def test_mapper_with_api():
    """Test mapper with API fallback."""
    print("\n\nTesting Mapper with API Fallback\n" + "="*50)
    
    # Configure mapper to use external services
    config = {
        "use_external_services": True,
        "use_fuzzy_matching": True,
        "api_cache_dir": "app/cache/api_cache"
    }
    
    mapper = TerminologyMapper(config)
    
    # Test terms that might not be in local DB
    test_terms = [
        ("Rituximab", "rxnorm"),  # Newer medication
        ("COVID-19 vaccine", "rxnorm"),  # Recent medication
        ("SARS-CoV-2 RNA", "loinc"),  # COVID test
        ("Post COVID-19 condition", "snomed"),  # Long COVID
        ("Pembrolizumab", "rxnorm"),  # Cancer drug
        ("Procalcitonin", "loinc"),  # Lab test
    ]
    
    for term, system in test_terms:
        print(f"\nMapping '{term}' to {system.upper()}:")
        print("-" * 40)
        
        if system == "snomed":
            result = mapper.map_to_snomed(term)
        elif system == "loinc":
            result = mapper.map_to_loinc(term)
        elif system == "rxnorm":
            result = mapper.map_to_rxnorm(term)
        
        if result.get('found', False) or result.get('code'):
            print(f"  ✓ Found: {result.get('display', 'N/A')} ({result.get('code', 'N/A')})")
            print(f"    Match type: {result.get('match_type', 'unknown')}")
            print(f"    Confidence: {result.get('confidence', 'N/A')}")
        else:
            print(f"  ✗ Not found")
            print(f"    Attempted methods: {', '.join(result.get('attempted_methods', []))}")


if __name__ == "__main__":
    try:
        test_direct_api()
        test_mapper_with_api()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: Some APIs may require internet connection or have rate limits.")