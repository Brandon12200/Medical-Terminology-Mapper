#!/usr/bin/env python3
"""
Test script for OMOP Terminology Converter functionality.

This script tests the OMOP CDM output generation for terminology mappings.
"""

import os
import sys
import logging
from datetime import date, datetime
from typing import Dict, Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from app modules
from app.standards.omop.converters import OMOPTerminologyConverter
from app.standards.omop.validators import OMOPTerminologyValidator
from app.standards.terminology.embedded_db import EmbeddedDatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_omop_converter")

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
            'match_type': 'exact',
            'category': 'medication'
        },
        {
            'original_text': 'lisinopril',
            'found': True,
            'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
            'code': '29046',
            'display': 'lisinopril',
            'confidence': 1.0,
            'match_type': 'exact',
            'category': 'medication'
        },
        {
            'original_text': 'pneumonia',
            'found': True,
            'system': 'http://snomed.info/sct',
            'code': '233604007',
            'display': 'Pneumonia',
            'confidence': 0.95,
            'match_type': 'exact',
            'category': 'condition'
        },
        {
            'original_text': 'glucose',
            'found': True,
            'system': 'http://loinc.org', 
            'code': '33747-0',
            'display': 'Glucose [Mass/volume] in Serum or Plasma',
            'confidence': 0.9,
            'match_type': 'exact',
            'category': 'lab_test'
        },
        {
            'original_text': 'blood pressure check',
            'found': True,
            'system': 'http://snomed.info/sct',
            'code': '163020007',
            'display': 'Blood pressure taking',
            'confidence': 0.85,
            'match_type': 'partial',
            'category': 'procedure'
        }
    ]

def test_concept_conversion():
    """Test conversion of mappings to CONCEPT records."""
    print("\n=== Testing CONCEPT Conversion ===")
    
    converter = OMOPTerminologyConverter()
    test_mappings = create_test_mappings()
    
    # Convert to CONCEPT records
    concepts = converter.convert_mappings_to_concepts(test_mappings, include_source_concepts=True)
    
    print(f"  Generated {len(concepts)} CONCEPT records")
    
    # Show some examples
    for i, concept in enumerate(concepts[:3]):
        print(f"    Concept {i+1}:")
        print(f"      ID: {concept['concept_id']}")
        print(f"      Name: {concept['concept_name']}")
        print(f"      Domain: {concept['domain_id']}")
        print(f"      Vocabulary: {concept['vocabulary_id']}")
        print(f"      Class: {concept['concept_class_id']}")
        print(f"      Standard: {concept['standard_concept']}")
        print(f"      Code: {concept['concept_code']}")

def test_concept_relationship_conversion():
    """Test conversion of mappings to CONCEPT_RELATIONSHIP records."""
    print("\n=== Testing CONCEPT_RELATIONSHIP Conversion ===")
    
    converter = OMOPTerminologyConverter()
    test_mappings = create_test_mappings()
    
    # First create concepts
    concepts = converter.convert_mappings_to_concepts(test_mappings, include_source_concepts=True)
    
    # Then create relationships
    relationships = converter.convert_mappings_to_concept_relationships(test_mappings, concepts)
    
    print(f"  Generated {len(relationships)} CONCEPT_RELATIONSHIP records")
    
    # Show some examples
    for i, relationship in enumerate(relationships[:3]):
        print(f"    Relationship {i+1}:")
        print(f"      Concept 1: {relationship['concept_id_1']}")
        print(f"      Concept 2: {relationship['concept_id_2']}")
        print(f"      Relationship: {relationship['relationship_id']}")
        print(f"      Valid Start: {relationship['valid_start_date']}")

def test_domain_table_conversion():
    """Test conversion of mappings to domain tables."""
    print("\n=== Testing Domain Table Conversion ===")
    
    converter = OMOPTerminologyConverter()
    test_mappings = create_test_mappings()
    
    # Convert to domain tables
    domain_tables = converter.convert_mappings_to_domain_tables(
        test_mappings, 
        person_id=12345,
        record_date=date.today(),
        record_type='protocol_record'
    )
    
    print(f"  Generated {len(domain_tables)} domain tables")
    
    # Show table contents
    for table_name, records in domain_tables.items():
        print(f"    {table_name.upper()}: {len(records)} records")
        
        if records:
            # Show first record structure
            first_record = records[0]
            print(f"      Sample record keys: {list(first_record.keys())[:8]}...")
            
            # Show key values
            for key, value in list(first_record.items())[:5]:
                print(f"        {key}: {value}")

def test_batch_conversion():
    """Test batch conversion of multiple mapping categories."""
    print("\n=== Testing Batch Conversion ===")
    
    converter = OMOPTerminologyConverter()
    
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
    formats = ['concepts', 'domain_tables', 'full']
    
    for format_type in formats:
        print(f"\n  Testing {format_type} format:")
        result = converter.convert_batch_mappings(batch_mappings, format_type, person_id=12345)
        
        print(f"    Generated tables: {list(result.keys())}")
        
        for table_name, records in result.items():
            if isinstance(records, list):
                print(f"      {table_name}: {len(records)} records")

def test_omop_validation():
    """Test OMOP validation of generated data."""
    print("\n=== Testing OMOP Validation ===")
    
    converter = OMOPTerminologyConverter()
    validator = OMOPTerminologyValidator()
    test_mappings = create_test_mappings()
    
    # Generate OMOP data
    concepts = converter.convert_mappings_to_concepts(test_mappings)
    relationships = converter.convert_mappings_to_concept_relationships(test_mappings, concepts)
    domain_tables = converter.convert_mappings_to_domain_tables(test_mappings, person_id=12345)
    
    # Combine all tables
    all_tables = {
        'concept': concepts,
        'concept_relationship': relationships,
        **domain_tables
    }
    
    # Validate
    validation_result = validator.validate(all_tables)
    
    print(f"  Validation result: {validation_result['valid']}")
    print(f"  Tables validated: {validation_result['tables_validated']}")
    print(f"  Total records: {validation_result['total_records']}")
    print(f"  Issues found: {len(validation_result['issues'])}")
    
    # Show some issues if any
    for issue in validation_result['issues'][:5]:
        print(f"    - {issue}")

def test_csv_export():
    """Test CSV export functionality."""
    print("\n=== Testing CSV Export ===")
    
    converter = OMOPTerminologyConverter()
    test_mappings = create_test_mappings()
    
    # Generate full OMOP data
    omop_data = converter.convert_batch_mappings(
        {'test_mappings': test_mappings}, 
        output_format='full',
        person_id=12345
    )
    
    # Create temporary output directory
    output_dir = "/tmp/omop_test_output"
    
    try:
        # Export to CSV
        file_paths = converter.export_to_csv(omop_data, output_dir)
        
        print(f"  Exported {len(file_paths)} CSV files")
        
        for table_name, file_path in file_paths.items():
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"    {table_name}: {file_path} ({file_size} bytes)")
            else:
                print(f"    {table_name}: File not found at {file_path}")
    
    except Exception as e:
        print(f"  Error during CSV export: {e}")

def test_with_real_terminology_data():
    """Test with real terminology database lookups."""
    print("\n=== Testing with Real Terminology Data ===")
    
    try:
        # Initialize database manager
        db_manager = EmbeddedDatabaseManager()
        if not db_manager.connect():
            print("  Could not connect to terminology databases - skipping real data test")
            return
        
        converter = OMOPTerminologyConverter()
        validator = OMOPTerminologyValidator()
        
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
                result['original_text'] = term
                real_mappings.append(result)
                print(f"    Found mapping for {term}: {result['system']} | {result['code']}")
        
        if real_mappings:
            # Convert to OMOP
            omop_data = converter.convert_batch_mappings(
                {'real_mappings': real_mappings}, 
                output_format='full',
                person_id=12345
            )
            
            print(f"  Created OMOP data with {len(omop_data)} tables")
            
            # Validate
            validation_result = validator.validate(omop_data)
            print(f"  Validation result: {validation_result['valid']}")
            print(f"  Issues: {len(validation_result['issues'])}")
            
            # Show table record counts
            for table_name, records in omop_data.items():
                if isinstance(records, list):
                    print(f"    {table_name}: {len(records)} records")
        
        db_manager.close()
        
    except Exception as e:
        print(f"  Error testing with real data: {e}")

def test_individual_table_validation():
    """Test validation of individual tables."""
    print("\n=== Testing Individual Table Validation ===")
    
    converter = OMOPTerminologyConverter()
    validator = OMOPTerminologyValidator()
    test_mappings = create_test_mappings()
    
    # Generate domain tables
    domain_tables = converter.convert_mappings_to_domain_tables(test_mappings, person_id=12345)
    
    # Validate each table individually
    for table_name, records in domain_tables.items():
        print(f"\n  Validating {table_name}:")
        validation_result = validator.validate_table(table_name, records)
        
        print(f"    Valid: {validation_result['valid']}")
        print(f"    Records: {validation_result['record_count']}")
        print(f"    Issues: {len(validation_result['issues'])}")
        
        # Show first few issues
        for issue in validation_result['issues'][:3]:
            print(f"      - {issue}")

def run_tests():
    """Run all OMOP converter tests."""
    print("=== OMOP Terminology Converter Tests ===")
    
    test_concept_conversion()
    test_concept_relationship_conversion()
    test_domain_table_conversion()
    test_batch_conversion()
    test_omop_validation()
    test_csv_export()
    test_individual_table_validation()
    test_with_real_terminology_data()
    
    print("\n=== All OMOP Tests Completed ===")

if __name__ == "__main__":
    run_tests()