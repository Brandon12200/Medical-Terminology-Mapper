#!/usr/bin/env python3
"""
Comprehensive Standards Testing Suite for Medical Terminology Mapper.

This script tests FHIR and OMOP validation with various terminology inputs,
edge cases, and performance scenarios.
"""

import os
import sys
import logging
import time
from datetime import date, datetime
from typing import Dict, Any, List

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from app modules
from app.standards.fhir.converters import FHIRTerminologyConverter
from app.standards.fhir.validators import FHIRTerminologyValidator
from app.standards.omop.converters import OMOPTerminologyConverter
from app.standards.omop.validators import OMOPTerminologyValidator
from app.standards.terminology.embedded_db import EmbeddedDatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_standards_validation")

class StandardsTestSuite:
    """Comprehensive testing suite for FHIR and OMOP standards."""
    
    def __init__(self):
        """Initialize test suite."""
        self.fhir_converter = FHIRTerminologyConverter()
        self.fhir_validator = FHIRTerminologyValidator()
        self.omop_converter = OMOPTerminologyConverter()
        self.omop_validator = OMOPTerminologyValidator()
        
        # Test statistics
        self.test_results = {
            'fhir': {'passed': 0, 'failed': 0, 'total': 0},
            'omop': {'passed': 0, 'failed': 0, 'total': 0},
            'performance': {'tests': [], 'avg_time': 0}
        }
    
    def create_edge_case_mappings(self) -> List[Dict[str, Any]]:
        """Create various edge case terminology mappings for testing."""
        return [
            # Valid standard mapping
            {
                'original_text': 'aspirin',
                'found': True,
                'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                'code': '1191',
                'display': 'aspirin',
                'confidence': 1.0,
                'match_type': 'exact'
            },
            # Low confidence mapping
            {
                'original_text': 'headache pills',
                'found': True,
                'system': 'http://snomed.info/sct',
                'code': '387207008',
                'display': 'Aspirin',
                'confidence': 0.3,
                'match_type': 'fuzzy'
            },
            # Empty display name
            {
                'original_text': 'unknown medication',
                'found': True,
                'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                'code': '999999',
                'display': '',
                'confidence': 0.5,
                'match_type': 'partial'
            },
            # Special characters in text
            {
                'original_text': 'Aspirin® 325mg (acetylsalicylic acid)',
                'found': True,
                'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                'code': '1191',
                'display': 'aspirin',
                'confidence': 0.9,
                'match_type': 'normalized'
            },
            # Very long term name
            {
                'original_text': 'This is an extremely long medication name that exceeds normal limits and contains multiple descriptive phrases about the medication including dosage strength route of administration and various clinical indications',
                'found': True,
                'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                'code': '12345',
                'display': 'Long medication name',
                'confidence': 0.7,
                'match_type': 'partial'
            },
            # Non-ASCII characters
            {
                'original_text': 'Médication française',
                'found': True,
                'system': 'http://snomed.info/sct',
                'code': '123456',
                'display': 'French medication',
                'confidence': 0.8,
                'match_type': 'exact'
            },
            # Missing system
            {
                'original_text': 'unknown system drug',
                'found': True,
                'system': '',
                'code': '777777',
                'display': 'Unknown system drug',
                'confidence': 0.6,
                'match_type': 'unknown'
            },
            # Unmapped concept
            {
                'original_text': 'completely unknown term',
                'found': False,
                'system': None,
                'code': None,
                'display': None,
                'confidence': 0.0,
                'match_type': 'no_match'
            },
            # Multiple mappings (same term, different systems)
            {
                'original_text': 'glucose',
                'found': True,
                'system': 'http://loinc.org',
                'code': '33747-0',
                'display': 'Glucose [Mass/volume] in Serum or Plasma',
                'confidence': 0.95,
                'match_type': 'exact'
            },
            {
                'original_text': 'glucose',
                'found': True,
                'system': 'http://snomed.info/sct',
                'code': '33747001',
                'display': 'Glucose measurement',
                'confidence': 0.9,
                'match_type': 'exact'
            }
        ]
    
    def create_invalid_mappings(self) -> List[Dict[str, Any]]:
        """Create invalid mappings to test error handling."""
        return [
            # Missing required fields
            {
                'original_text': 'invalid mapping 1',
                'found': True
                # Missing system, code, display
            },
            # Invalid confidence value
            {
                'original_text': 'invalid mapping 2',
                'found': True,
                'system': 'http://snomed.info/sct',
                'code': '123',
                'display': 'Test',
                'confidence': 1.5,  # Invalid > 1.0
                'match_type': 'exact'
            },
            # Invalid system URI
            {
                'original_text': 'invalid mapping 3',
                'found': True,
                'system': 'not-a-valid-uri',
                'code': '456',
                'display': 'Test',
                'confidence': 0.8,
                'match_type': 'exact'
            }
        ]
    
    def test_fhir_validation_edge_cases(self):
        """Test FHIR validation with various edge cases."""
        print("\n=== Testing FHIR Validation Edge Cases ===")
        
        edge_cases = self.create_edge_case_mappings()
        invalid_cases = self.create_invalid_mappings()
        
        # Test valid edge cases
        print("\n  Testing valid edge cases:")
        for i, mapping in enumerate(edge_cases):
            if not mapping.get('found', False):
                continue
                
            try:
                # Convert to CodeableConcept
                codeable_concept = self.fhir_converter.convert_mapping_to_codeable_concept(
                    mapping, mapping.get('original_text')
                )
                
                # Create minimal ValueSet
                valueset = self.fhir_converter.convert_mappings_to_valueset([mapping])
                
                # Validate
                validation_result = self.fhir_validator.validate(valueset)
                
                if validation_result['valid']:
                    print(f"    ✅ Edge case {i+1}: {mapping['original_text'][:30]}...")
                    self.test_results['fhir']['passed'] += 1
                else:
                    print(f"    ❌ Edge case {i+1}: {len(validation_result['issues'])} issues")
                    self.test_results['fhir']['failed'] += 1
                
                self.test_results['fhir']['total'] += 1
                
            except Exception as e:
                print(f"    ❌ Edge case {i+1}: Exception - {str(e)[:50]}...")
                self.test_results['fhir']['failed'] += 1
                self.test_results['fhir']['total'] += 1
        
        # Test invalid cases
        print("\n  Testing invalid cases (should fail validation):")
        for i, mapping in enumerate(invalid_cases):
            try:
                # Convert to CodeableConcept (may succeed)
                codeable_concept = self.fhir_converter.convert_mapping_to_codeable_concept(
                    mapping, mapping.get('original_text')
                )
                
                # Try to create ValueSet (may fail)
                try:
                    valueset = self.fhir_converter.convert_mappings_to_valueset([mapping])
                    validation_result = self.fhir_validator.validate(valueset)
                    
                    # Invalid cases should ideally fail validation
                    if not validation_result['valid']:
                        print(f"    ✅ Invalid case {i+1}: Correctly caught {len(validation_result['issues'])} issues")
                        self.test_results['fhir']['passed'] += 1
                    else:
                        print(f"    ⚠️  Invalid case {i+1}: Should have failed validation")
                        self.test_results['fhir']['failed'] += 1
                    
                except Exception as e:
                    print(f"    ✅ Invalid case {i+1}: Correctly threw exception - {str(e)[:30]}...")
                    self.test_results['fhir']['passed'] += 1
                
                self.test_results['fhir']['total'] += 1
                
            except Exception as e:
                print(f"    ✅ Invalid case {i+1}: Correctly threw exception - {str(e)[:30]}...")
                self.test_results['fhir']['passed'] += 1
                self.test_results['fhir']['total'] += 1
    
    def test_omop_validation_edge_cases(self):
        """Test OMOP validation with various edge cases."""
        print("\n=== Testing OMOP Validation Edge Cases ===")
        
        edge_cases = self.create_edge_case_mappings()
        
        # Test valid edge cases
        print("\n  Testing valid edge cases:")
        for i, mapping in enumerate(edge_cases):
            if not mapping.get('found', False):
                continue
                
            try:
                # Convert to OMOP CONCEPT
                concepts = self.omop_converter.convert_mappings_to_concepts([mapping])
                
                # Convert to domain tables
                domain_tables = self.omop_converter.convert_mappings_to_domain_tables(
                    [mapping], person_id=1, record_date=date.today()
                )
                
                # Validate concepts
                if concepts:
                    concept_validation = self.omop_validator.validate_table('concept', concepts)
                    
                    if concept_validation['valid']:
                        print(f"    ✅ Edge case {i+1} (CONCEPT): {mapping['original_text'][:30]}...")
                        self.test_results['omop']['passed'] += 1
                    else:
                        print(f"    ❌ Edge case {i+1} (CONCEPT): {len(concept_validation['issues'])} issues")
                        for issue in concept_validation['issues'][:2]:
                            print(f"       - {issue}")
                        self.test_results['omop']['failed'] += 1
                    
                    self.test_results['omop']['total'] += 1
                
                # Validate domain tables
                for table_name, records in domain_tables.items():
                    if records:
                        table_validation = self.omop_validator.validate_table(table_name, records)
                        
                        if table_validation['valid']:
                            print(f"    ✅ Edge case {i+1} ({table_name.upper()}): Valid")
                            self.test_results['omop']['passed'] += 1
                        else:
                            print(f"    ❌ Edge case {i+1} ({table_name.upper()}): {len(table_validation['issues'])} issues")
                            self.test_results['omop']['failed'] += 1
                        
                        self.test_results['omop']['total'] += 1
                
            except Exception as e:
                print(f"    ❌ Edge case {i+1}: Exception - {str(e)[:50]}...")
                self.test_results['omop']['failed'] += 1
                self.test_results['omop']['total'] += 1
    
    def test_large_dataset_performance(self):
        """Test performance with large datasets."""
        print("\n=== Testing Large Dataset Performance ===")
        
        # Create large dataset
        base_mapping = {
            'found': True,
            'system': 'http://snomed.info/sct',
            'display': 'Test concept',
            'confidence': 0.9,
            'match_type': 'exact'
        }
        
        dataset_sizes = [10, 50, 100, 500]
        
        for size in dataset_sizes:
            print(f"\n  Testing with {size} mappings:")
            
            # Generate dataset
            large_dataset = []
            for i in range(size):
                mapping = base_mapping.copy()
                mapping['original_text'] = f'test_term_{i}'
                mapping['code'] = str(1000000 + i)
                mapping['display'] = f'Test concept {i}'
                large_dataset.append(mapping)
            
            # Test FHIR performance
            start_time = time.time()
            try:
                fhir_valueset = self.fhir_converter.convert_mappings_to_valueset(large_dataset)
                fhir_bundle = self.fhir_converter.create_terminology_bundle(large_dataset)
                fhir_validation = self.fhir_validator.validate(fhir_bundle)
                
                fhir_time = time.time() - start_time
                print(f"    FHIR processing: {fhir_time:.3f}s ({fhir_time/size*1000:.2f}ms per mapping)")
                
                self.test_results['performance']['tests'].append({
                    'type': 'FHIR',
                    'size': size,
                    'time': fhir_time,
                    'per_item': fhir_time/size
                })
                
            except Exception as e:
                print(f"    FHIR processing failed: {str(e)[:50]}...")
            
            # Test OMOP performance
            start_time = time.time()
            try:
                omop_data = self.omop_converter.convert_batch_mappings(
                    {'large_dataset': large_dataset}, 
                    output_format='full'
                )
                omop_validation = self.omop_validator.validate(omop_data)
                
                omop_time = time.time() - start_time
                print(f"    OMOP processing: {omop_time:.3f}s ({omop_time/size*1000:.2f}ms per mapping)")
                
                self.test_results['performance']['tests'].append({
                    'type': 'OMOP',
                    'size': size,
                    'time': omop_time,
                    'per_item': omop_time/size
                })
                
            except Exception as e:
                print(f"    OMOP processing failed: {str(e)[:50]}...")
    
    def test_cross_standard_consistency(self):
        """Test consistency between FHIR and OMOP outputs."""
        print("\n=== Testing Cross-Standard Consistency ===")
        
        test_mappings = self.create_edge_case_mappings()[:5]  # Use first 5 valid mappings
        valid_mappings = [m for m in test_mappings if m.get('found', False)]
        
        print(f"\n  Testing with {len(valid_mappings)} mappings:")
        
        # Generate FHIR output
        fhir_valueset = self.fhir_converter.convert_mappings_to_valueset(valid_mappings)
        fhir_conceptmap = self.fhir_converter.convert_mappings_to_conceptmap(valid_mappings)
        
        # Generate OMOP output
        omop_concepts = self.omop_converter.convert_mappings_to_concepts(valid_mappings)
        omop_domain_tables = self.omop_converter.convert_mappings_to_domain_tables(valid_mappings)
        
        # Check consistency
        consistency_issues = []
        
        # Compare concept counts
        fhir_concept_count = len(fhir_valueset.get('expansion', {}).get('contains', []))
        omop_concept_count = len([c for c in omop_concepts if c.get('standard_concept') == 'S'])
        
        if fhir_concept_count != omop_concept_count:
            consistency_issues.append(f"Concept count mismatch: FHIR {fhir_concept_count}, OMOP {omop_concept_count}")
        
        # Compare systems used
        fhir_systems = set()
        for include in fhir_valueset.get('compose', {}).get('include', []):
            fhir_systems.add(include.get('system', ''))
        
        omop_vocabularies = set()
        for concept in omop_concepts:
            omop_vocabularies.add(concept.get('vocabulary_id', ''))
        
        # Map OMOP vocabularies to FHIR systems for comparison
        vocab_mapping = {
            'SNOMED': 'http://snomed.info/sct',
            'LOINC': 'http://loinc.org',
            'RxNorm': 'http://www.nlm.nih.gov/research/umls/rxnorm'
        }
        
        omop_systems = set()
        for vocab in omop_vocabularies:
            if vocab in vocab_mapping:
                omop_systems.add(vocab_mapping[vocab])
        
        missing_in_omop = fhir_systems - omop_systems
        missing_in_fhir = omop_systems - fhir_systems
        
        if missing_in_omop:
            consistency_issues.append(f"Systems in FHIR but not OMOP: {missing_in_omop}")
        if missing_in_fhir:
            consistency_issues.append(f"Systems in OMOP but not FHIR: {missing_in_fhir}")
        
        # Report consistency results
        if consistency_issues:
            print(f"    ⚠️  Found {len(consistency_issues)} consistency issues:")
            for issue in consistency_issues:
                print(f"       - {issue}")
        else:
            print("    ✅ No consistency issues found")
    
    def test_real_terminology_integration(self):
        """Test with real terminology database."""
        print("\n=== Testing Real Terminology Integration ===")
        
        try:
            # Initialize database manager
            db_manager = EmbeddedDatabaseManager()
            if not db_manager.connect():
                print("  ⚠️  Could not connect to terminology databases - skipping real data test")
                return
            
            # Test terms from different systems
            test_terms = [
                ('aspirin', 'rxnorm'),
                ('lisinopril', 'rxnorm'),
                ('pneumonia', 'snomed'),
                ('hypertension', 'snomed')
            ]
            
            real_mappings = []
            
            for term, expected_system in test_terms:
                print(f"\n  Testing term: {term} (expected: {expected_system})")
                
                # Try lookup
                result = None
                if expected_system == 'rxnorm':
                    result = db_manager.lookup_rxnorm(term)
                elif expected_system == 'snomed':
                    result = db_manager.lookup_snomed(term)
                elif expected_system == 'loinc':
                    result = db_manager.lookup_loinc(term)
                
                if result and result.get('found', False):
                    result['original_text'] = term
                    real_mappings.append(result)
                    print(f"    ✅ Found: {result['system']} | {result['code']}")
                    
                    # Test FHIR conversion
                    try:
                        fhir_cc = self.fhir_converter.convert_mapping_to_codeable_concept(result, term)
                        fhir_vs = self.fhir_converter.convert_mappings_to_valueset([result])
                        fhir_validation = self.fhir_validator.validate(fhir_vs)
                        
                        if fhir_validation['valid']:
                            print(f"    ✅ FHIR conversion successful")
                        else:
                            print(f"    ❌ FHIR validation failed: {len(fhir_validation['issues'])} issues")
                    
                    except Exception as e:
                        print(f"    ❌ FHIR conversion error: {str(e)[:50]}...")
                    
                    # Test OMOP conversion
                    try:
                        omop_concepts = self.omop_converter.convert_mappings_to_concepts([result])
                        omop_domain = self.omop_converter.convert_mappings_to_domain_tables([result])
                        
                        if omop_concepts:
                            concept_validation = self.omop_validator.validate_table('concept', omop_concepts)
                            if concept_validation['valid']:
                                print(f"    ✅ OMOP conversion successful")
                            else:
                                print(f"    ❌ OMOP validation failed: {len(concept_validation['issues'])} issues")
                    
                    except Exception as e:
                        print(f"    ❌ OMOP conversion error: {str(e)[:50]}...")
                
                else:
                    print(f"    ❌ Not found in {expected_system}")
            
            db_manager.close()
            
        except Exception as e:
            print(f"  ❌ Error in real terminology integration test: {str(e)}")
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*60)
        print("COMPREHENSIVE STANDARDS TESTING REPORT")
        print("="*60)
        
        # FHIR Results
        fhir_total = self.test_results['fhir']['total']
        fhir_passed = self.test_results['fhir']['passed']
        fhir_failed = self.test_results['fhir']['failed']
        fhir_pass_rate = (fhir_passed / fhir_total * 100) if fhir_total > 0 else 0
        
        print(f"\n📊 FHIR Testing Results:")
        print(f"   Total Tests: {fhir_total}")
        print(f"   Passed: {fhir_passed}")
        print(f"   Failed: {fhir_failed}")
        print(f"   Pass Rate: {fhir_pass_rate:.1f}%")
        
        # OMOP Results
        omop_total = self.test_results['omop']['total']
        omop_passed = self.test_results['omop']['passed']
        omop_failed = self.test_results['omop']['failed']
        omop_pass_rate = (omop_passed / omop_total * 100) if omop_total > 0 else 0
        
        print(f"\n📊 OMOP Testing Results:")
        print(f"   Total Tests: {omop_total}")
        print(f"   Passed: {omop_passed}")
        print(f"   Failed: {omop_failed}")
        print(f"   Pass Rate: {omop_pass_rate:.1f}%")
        
        # Performance Results
        if self.test_results['performance']['tests']:
            print(f"\n⚡ Performance Results:")
            
            fhir_tests = [t for t in self.test_results['performance']['tests'] if t['type'] == 'FHIR']
            omop_tests = [t for t in self.test_results['performance']['tests'] if t['type'] == 'OMOP']
            
            if fhir_tests:
                avg_fhir_time = sum(t['per_item'] for t in fhir_tests) / len(fhir_tests)
                print(f"   FHIR avg time per mapping: {avg_fhir_time*1000:.2f}ms")
            
            if omop_tests:
                avg_omop_time = sum(t['per_item'] for t in omop_tests) / len(omop_tests)
                print(f"   OMOP avg time per mapping: {avg_omop_time*1000:.2f}ms")
        
        # Overall Assessment
        total_tests = fhir_total + omop_total
        total_passed = fhir_passed + omop_passed
        overall_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 Overall Assessment:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Overall Pass Rate: {overall_pass_rate:.1f}%")
        
        if overall_pass_rate >= 90:
            print("   Status: ✅ EXCELLENT - Standards compliance is very high")
        elif overall_pass_rate >= 75:
            print("   Status: ✅ GOOD - Standards compliance is acceptable")
        elif overall_pass_rate >= 50:
            print("   Status: ⚠️  FAIR - Some issues need attention")
        else:
            print("   Status: ❌ POOR - Significant issues require fixing")
        
        print("\n" + "="*60)
    
    def run_all_tests(self):
        """Run the complete standards testing suite."""
        print("🧪 COMPREHENSIVE STANDARDS TESTING SUITE")
        print("Testing FHIR and OMOP validation with various scenarios...")
        
        # Run all test categories
        self.test_fhir_validation_edge_cases()
        self.test_omop_validation_edge_cases()
        self.test_large_dataset_performance()
        self.test_cross_standard_consistency()
        self.test_real_terminology_integration()
        
        # Generate final report
        self.generate_test_report()

def main():
    """Main test execution."""
    test_suite = StandardsTestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()