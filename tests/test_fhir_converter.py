#!/usr/bin/env python3
"""
Test script for FHIR Terminology Converter functionality.

This script tests the FHIR output generation for terminology mappings.
"""

import os
import sys
import logging
import json
from typing import Dict, Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from app modules
from app.standards.fhir.converters import FHIRTerminologyConverter
from app.standards.fhir.validators import FHIRTerminologyValidator
from app.standards.terminology.embedded_db import EmbeddedDatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_fhir_converter")

def create_test_mappings():
    """Create sample terminology mappings for testing."""
    return [
        {
            'original_text': 'aspirin',
            'found': True,
            'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
            'code': '1191',
            'display': 'aspirin',
            'confidence': 1.0,
            'match_type': 'exact'
        },
        {
            'original_text': 'lisinopril',
            'found': True,
            'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
            'code': '29046',
            'display': 'lisinopril',
            'confidence': 1.0,
            'match_type': 'exact'
        },
        {
            'original_text': 'pneumonia',
            'found': True,
            'system': 'http://snomed.info/sct',
            'code': '233604007',
            'display': 'Pneumonia',
            'confidence': 0.95,
            'match_type': 'exact'
        },
        {
            'original_text': 'glucose',
            'found': True,
            'system': 'http://loinc.org', 
            'code': '33747-0',
            'display': 'Glucose [Mass/volume] in Serum or Plasma',
            'confidence': 0.9,
            'match_type': 'exact'
        }
    ]

def test_codeable_concept_conversion():
    """Test conversion of mappings to CodeableConcept."""
    print("\n=== Testing CodeableConcept Conversion ===")
    
    converter = FHIRTerminologyConverter()
    test_mappings = create_test_mappings()
    
    for i, mapping in enumerate(test_mappings):
        print(f"\nTesting mapping {i+1}: {mapping['original_text']}")
        
        # Convert to CodeableConcept
        codeable_concept = converter.convert_mapping_to_codeable_concept(
            mapping, mapping['original_text']
        )
        
        print(f"  Generated CodeableConcept:")
        print(f"    System: {codeable_concept['coding'][0]['system'] if codeable_concept.get('coding') else 'None'}")
        print(f"    Code: {codeable_concept['coding'][0]['code'] if codeable_concept.get('coding') else 'None'}")
        print(f"    Display: {codeable_concept['coding'][0]['display'] if codeable_concept.get('coding') else 'None'}")
        print(f"    Text: {codeable_concept.get('text', 'None')}")
        
        # Check for extensions
        if codeable_concept.get('coding') and codeable_concept['coding'][0].get('extension'):
            print(f"    Extensions: {len(codeable_concept['coding'][0]['extension'])}")

def test_valueset_conversion():
    """Test conversion of mappings to ValueSet."""
    print("\n=== Testing ValueSet Conversion ===")
    
    converter = FHIRTerminologyConverter()
    test_mappings = create_test_mappings()
    
    # Convert to ValueSet
    valueset = converter.convert_mappings_to_valueset(
        test_mappings, 
        {
            'title': 'Test Terminology ValueSet',
            'description': 'ValueSet for testing terminology mappings'
        }
    )
    
    print(f"  ValueSet ID: {valueset['id']}")
    print(f"  Title: {valueset['title']}")
    print(f"  Status: {valueset['status']}")
    print(f"  Include sections: {len(valueset['compose']['include'])}")
    
    # Check expansion
    if 'expansion' in valueset:
        print(f"  Expansion concepts: {valueset['expansion']['total']}")
        for i, concept in enumerate(valueset['expansion']['contains'][:3]):  # Show first 3
            print(f"    Concept {i+1}: {concept['system']} | {concept['code']} | {concept['display']}")

def test_conceptmap_conversion():
    """Test conversion of mappings to ConceptMap."""
    print("\n=== Testing ConceptMap Conversion ===")
    
    converter = FHIRTerminologyConverter()
    test_mappings = create_test_mappings()
    
    # Add source information to mappings
    for mapping in test_mappings:
        mapping['source_system'] = 'http://example.org/terminology/original'
        mapping['source_code'] = mapping['original_text']
        mapping['source_display'] = mapping['original_text']
    
    # Convert to ConceptMap
    conceptmap = converter.convert_mappings_to_conceptmap(
        test_mappings,
        source_system='http://example.org/terminology/original',
        conceptmap_info={
            'title': 'Test Terminology ConceptMap',
            'description': 'ConceptMap for testing terminology mappings'
        }
    )
    
    print(f"  ConceptMap ID: {conceptmap['id']}")
    print(f"  Title: {conceptmap['title']}")
    print(f"  Status: {conceptmap['status']}")
    print(f"  Groups: {len(conceptmap['group'])}")
    
    # Show group details
    for i, group in enumerate(conceptmap['group']):
        print(f"    Group {i+1}: {group['source']} -> {group['target']}")
        print(f"      Elements: {len(group['element'])}")

def test_bundle_creation():
    """Test creation of Bundle with terminology resources."""
    print("\n=== Testing Bundle Creation ===")
    
    converter = FHIRTerminologyConverter()
    test_mappings = create_test_mappings()
    
    # Create Bundle
    bundle = converter.create_terminology_bundle(
        test_mappings,
        {
            'valueset_info': {
                'title': 'Test Bundle ValueSet',
                'description': 'ValueSet within test bundle'
            },
            'conceptmap_info': {
                'title': 'Test Bundle ConceptMap',
                'description': 'ConceptMap within test bundle'
            }
        }
    )
    
    print(f"  Bundle ID: {bundle['id']}")
    print(f"  Bundle type: {bundle['type']}")
    print(f"  Total entries: {bundle['total']}")
    
    # Show entry types
    entry_types = {}
    for entry in bundle['entry']:
        resource_type = entry['resource']['resourceType']
        entry_types[resource_type] = entry_types.get(resource_type, 0) + 1
    
    print(f"  Resource types in bundle:")
    for resource_type, count in entry_types.items():
        print(f"    {resource_type}: {count}")

def test_fhir_validation():
    """Test FHIR validation of generated resources."""
    print("\n=== Testing FHIR Validation ===")
    
    converter = FHIRTerminologyConverter()
    validator = FHIRTerminologyValidator()
    test_mappings = create_test_mappings()
    
    # Create resources to validate
    valueset = converter.convert_mappings_to_valueset(test_mappings)
    conceptmap = converter.convert_mappings_to_conceptmap(test_mappings)
    bundle = converter.create_terminology_bundle(test_mappings)
    
    # Validate each resource type
    resources_to_validate = [
        ("ValueSet", valueset),
        ("ConceptMap", conceptmap), 
        ("Bundle", bundle)
    ]
    
    for resource_name, resource in resources_to_validate:
        print(f"\n  Validating {resource_name}:")
        validation_result = validator.validate(resource)
        
        print(f"    Valid: {validation_result['valid']}")
        print(f"    Issues: {len(validation_result['issues'])}")
        
        if validation_result['issues']:
            for issue in validation_result['issues'][:3]:  # Show first 3 issues
                print(f"      - {issue}")

def test_batch_conversion():
    """Test batch conversion of multiple mapping categories."""
    print("\n=== Testing Batch Conversion ===")
    
    converter = FHIRTerminologyConverter()
    
    # Create batch mappings by category
    batch_mappings = {
        'medications': [
            {
                'original_text': 'aspirin',
                'found': True,
                'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                'code': '1191',
                'display': 'aspirin',
                'confidence': 1.0,
                'match_type': 'exact'
            },
            {
                'original_text': 'lisinopril',
                'found': True,
                'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                'code': '29046',
                'display': 'lisinopril',
                'confidence': 1.0,
                'match_type': 'exact'
            }
        ],
        'conditions': [
            {
                'original_text': 'pneumonia',
                'found': True,
                'system': 'http://snomed.info/sct',
                'code': '233604007',
                'display': 'Pneumonia',
                'confidence': 0.95,
                'match_type': 'exact'
            }
        ],
        'lab_tests': [
            {
                'original_text': 'glucose',
                'found': True,
                'system': 'http://loinc.org',
                'code': '33747-0',
                'display': 'Glucose [Mass/volume] in Serum or Plasma',
                'confidence': 0.9,
                'match_type': 'exact'
            }
        ]
    }
    
    # Test different output formats
    formats = ['bundle', 'valueset', 'conceptmap']
    
    for format_type in formats:
        print(f"\n  Testing {format_type} format:")
        result = converter.convert_batch_mappings(batch_mappings, format_type)
        
        if format_type == 'bundle':
            print(f"    Bundle entries: {result['total']}")
        else:
            print(f"    Generated resources: {len(result)}")
            for category in result.keys():
                print(f"      {category}: {result[category]['resourceType']}")

def test_with_real_terminology_data():
    """Test with real terminology database lookups."""
    print("\n=== Testing with Real Terminology Data ===")
    
    try:
        # Initialize database manager
        db_manager = EmbeddedDatabaseManager()
        if not db_manager.connect():
            print("  Could not connect to terminology databases - skipping real data test")
            return
        
        converter = FHIRTerminologyConverter()
        
        # Test with actual lookups
        test_terms = ['aspirin', 'lisinopril', 'glucose', 'pneumonia']
        real_mappings = []
        
        for term in test_terms:
            # Try different terminology systems
            result = None
            
            # Try RxNorm first
            result = db_manager.lookup_rxnorm(term)
            if not result:
                # Try SNOMED
                result = db_manager.lookup_snomed(term)
            if not result:
                # Try LOINC
                result = db_manager.lookup_loinc(term)
            
            if result:
                real_mappings.append(result)
                print(f"    Found mapping for {term}: {result['system']} | {result['code']}")
        
        if real_mappings:
            # Convert to FHIR
            valueset = converter.convert_mappings_to_valueset(
                real_mappings,
                {'title': 'Real Terminology Data ValueSet'}
            )
            
            print(f"  Created ValueSet with {len(real_mappings)} real mappings")
            print(f"  ValueSet ID: {valueset['id']}")
            
            # Validate
            validator = FHIRTerminologyValidator()
            validation_result = validator.validate(valueset)
            print(f"  Validation result: {validation_result['valid']}")
        
        db_manager.close()
        
    except Exception as e:
        print(f"  Error testing with real data: {e}")

def run_tests():
    """Run all FHIR converter tests."""
    print("=== FHIR Terminology Converter Tests ===")
    
    test_codeable_concept_conversion()
    test_valueset_conversion()
    test_conceptmap_conversion()
    test_bundle_creation()
    test_fhir_validation()
    test_batch_conversion()
    test_with_real_terminology_data()
    
    print("\n=== All FHIR Tests Completed ===")

if __name__ == "__main__":
    run_tests()