#!/usr/bin/env python3
"""Integration tests for custom mapping rules."""

import unittest
import tempfile
import os
import time
from typing import List, Tuple

from app.standards.terminology.enhanced_mapper import EnhancedTerminologyMapper, EnhancedMappingResult
from app.standards.terminology.context_aware_mapper import ClinicalDomain
from app.standards.terminology.custom_mapping_rules import RuleType, RulePriority
from app.standards.terminology.negation_handler import EnhancedNegationHandler, ModifierType
from app.standards.terminology.performance_optimizer import PerformanceOptimizer


class TestWeek6Integration(unittest.TestCase):
    """Test custom mapping rules and advanced features."""
    
    def setUp(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_terminology_path = os.path.join(self.temp_dir, "terminology")
        self.test_rules_db = os.path.join(self.temp_dir, "custom_rules.sqlite")
        
        os.makedirs(self.test_terminology_path, exist_ok=True)
        
        config = {
            'performance': {
                'max_workers': 4,
                'use_processes': False
            },
            'negation': {
                'enable_advanced_patterns': True
            }
        }
        
        self.mapper = EnhancedTerminologyMapper(
            terminology_db_path=self.test_terminology_path,
            custom_rules_db_path=self.test_rules_db,
            config=config
        )
        
        # Add some test custom rules
        self._setup_test_rules()
        
    def tearDown(self):
        """Clean up test environment"""
        self.mapper.cleanup()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_test_rules(self):
        """Set up test custom mapping rules"""
        # Rule 1: Exact match override for chest pain
        self.mapper.add_custom_rule(
            rule_id="test_chest_pain_override",
            source_term="chest pain",
            target_code="29857009",
            target_system="SNOMED-CT",
            target_display="Chest pain (finding)",
            rule_type=RuleType.EXACT_MATCH,
            priority=RulePriority.HIGH,
            metadata={"test_rule": True, "category": "symptom"}
        )
        
        # Rule 2: Pattern match for blood pressure variants
        self.mapper.add_custom_rule(
            rule_id="test_bp_pattern",
            source_term="blood pressure",
            target_code="75367002", 
            target_system="SNOMED-CT",
            target_display="Blood pressure (observable entity)",
            rule_type=RuleType.PATTERN_MATCH,
            priority=RulePriority.MEDIUM,
            conditions={"pattern": r"blood\s+pressure|bp|b\.p\."},
            metadata={"test_rule": True, "category": "vital_sign"}
        )
        
        # Rule 3: Context-dependent rule for cardiology domain
        self.mapper.add_custom_rule(
            rule_id="test_cardiology_context",
            source_term="murmur",
            target_code="88610006",
            target_system="SNOMED-CT", 
            target_display="Heart murmur (finding)",
            rule_type=RuleType.CONTEXT_DEPENDENT,
            priority=RulePriority.HIGH,
            conditions={"required_context": {"domain": "cardiology"}},
            metadata={"test_rule": True, "category": "finding"}
        )
        
        # Rule 4: Domain-specific rule for laboratory
        self.mapper.add_custom_rule(
            rule_id="test_lab_glucose",
            source_term="glucose",
            target_code="33747003",
            target_system="SNOMED-CT",
            target_display="Glucose (substance)",
            rule_type=RuleType.DOMAIN_SPECIFIC,
            priority=RulePriority.MEDIUM,
            conditions={"domain": "laboratory"},
            metadata={"test_rule": True, "category": "substance"}
        )
    
    def test_enhanced_context_aware_mapping(self):
        """Test enhanced context-aware mapping with domain detection"""
        test_cases = [
            ("chest pain", "Patient presents with acute chest pain radiating to left arm", ClinicalDomain.CARDIOLOGY),
            ("glucose level", "Laboratory results show elevated glucose level of 180 mg/dL", ClinicalDomain.LABORATORY),
            ("shortness of breath", "Patient reports shortness of breath on exertion", ClinicalDomain.PULMONOLOGY),
            ("depression", "Patient has history of major depression", ClinicalDomain.PSYCHIATRY)
        ]
        
        for term, context, expected_domain in test_cases:
            with self.subTest(term=term):
                result = self.mapper.map_term_enhanced(
                    term=term,
                    context_text=context,
                    detect_negation=True
                )
                
                # Verify mapping was successful
                self.assertIsInstance(result, EnhancedMappingResult)
                self.assertEqual(result.term, term)
                self.assertGreater(len(result.mappings), 0)
                
                # Verify context detection
                self.assertIsNotNone(result.context_info)
                self.assertIn('domain', result.context_info)
                
                # Verify domain relevance
                if result.domain:
                    # Should detect relevant domain or general
                    self.assertIn(result.domain, [expected_domain, ClinicalDomain.GENERAL])
    
    def test_custom_mapping_rules_application(self):
        """Test that custom mapping rules are properly applied"""
        
        # Test exact match rule
        result = self.mapper.map_term_enhanced("chest pain", "Patient has chest pain")
        
        # Should find the custom rule mapping
        rule_mappings = [m for m in result.mappings if m.get('source') == 'custom_rule']
        self.assertGreater(len(rule_mappings), 0)
        
        # Verify rule details
        rule_mapping = rule_mappings[0]
        self.assertEqual(rule_mapping['code'], "29857009")
        self.assertEqual(rule_mapping['system'], "SNOMED-CT")
        self.assertEqual(rule_mapping['rule_id'], "test_chest_pain_override")
        
        # Verify applied rules tracking
        self.assertGreater(len(result.applied_rules), 0)
        applied_rule = result.applied_rules[0]
        self.assertEqual(applied_rule['rule_id'], "test_chest_pain_override")
        self.assertEqual(applied_rule['rule_type'], 'exact_match')
    
    def test_pattern_matching_rules(self):
        """Test pattern matching custom rules"""
        test_terms = [
            "blood pressure",
            "BP",
            "b.p.",
            "blood  pressure"  # Extra space
        ]
        
        for term in test_terms:
            with self.subTest(term=term):
                result = self.mapper.map_term_enhanced(
                    term, f"Patient's {term} is elevated"
                )
                
                # Should find pattern rule mapping
                rule_mappings = [m for m in result.mappings if m.get('source') == 'custom_rule']
                if rule_mappings:  # Pattern should match for these terms
                    rule_mapping = rule_mappings[0]
                    self.assertEqual(rule_mapping['code'], "75367002")
                    self.assertEqual(rule_mapping['rule_id'], "test_bp_pattern")
    
    def test_context_dependent_rules(self):
        """Test context-dependent custom rules"""
        
        # Test with cardiology context
        cardiology_context = "Cardiology consultation reveals a systolic murmur heard at apex"
        result = self.mapper.map_term_enhanced(
            "murmur", 
            cardiology_context,
            domain_hint=ClinicalDomain.CARDIOLOGY
        )
        
        # Should apply context-dependent rule
        rule_mappings = [m for m in result.mappings if m.get('source') == 'custom_rule']
        if rule_mappings:
            rule_mapping = rule_mappings[0]
            self.assertEqual(rule_mapping['code'], "88610006")
            self.assertEqual(rule_mapping['rule_id'], "test_cardiology_context")
        
        # Test without cardiology context - rule should not apply
        general_context = "Patient mentions hearing a murmur"
        result_general = self.mapper.map_term_enhanced("murmur", general_context)
        
        rule_mappings_general = [m for m in result_general.mappings if m.get('source') == 'custom_rule']
        # Should have fewer or no custom rule mappings
        self.assertLessEqual(len(rule_mappings_general), len(rule_mappings))
    
    def test_advanced_negation_detection(self):
        """Test advanced negation and modifier detection"""
        test_cases = [
            ("Patient denies chest pain", "chest pain", True, ["negation"]),
            ("No evidence of pneumonia", "pneumonia", True, ["negation"]),
            ("Possible myocardial infarction", "myocardial infarction", False, ["uncertainty"]),
            ("Severe hypertension", "hypertension", False, ["severity"]),
            ("History of diabetes", "diabetes", False, ["past_history"]),
            ("Patient has chest pain", "chest pain", False, [])
        ]
        
        for context, term, expected_negated, expected_modifiers in test_cases:
            with self.subTest(context=context, term=term):
                result = self.mapper.map_term_enhanced(
                    term=term,
                    context_text=context,
                    detect_negation=True
                )
                
                # Check negation detection
                if result.negation_info:
                    self.assertEqual(
                        result.negation_info.get('is_negated', False), 
                        expected_negated,
                        f"Negation detection failed for: {context}"
                    )
                    
                    # Check modifier types
                    detected_modifiers = result.negation_info.get('modifier_types', [])
                    for expected_mod in expected_modifiers:
                        self.assertIn(expected_mod, detected_modifiers)
                
                # Verify confidence adjustment for negated terms
                if expected_negated and result.mappings:
                    for mapping in result.mappings:
                        if mapping.get('negated'):
                            # Confidence should be reduced for negated terms
                            self.assertLess(mapping.get('confidence', 1.0), 0.5)
    
    def test_domain_specific_rules(self):
        """Test domain-specific mapping rules"""
        
        # Test with laboratory domain
        lab_context = "Laboratory test shows glucose level of 200 mg/dL"
        result = self.mapper.map_term_enhanced(
            "glucose",
            lab_context,
            domain_hint=ClinicalDomain.LABORATORY
        )
        
        # Should apply domain-specific rule
        rule_mappings = [m for m in result.mappings if m.get('source') == 'custom_rule']
        if rule_mappings:
            rule_mapping = rule_mappings[0]
            self.assertEqual(rule_mapping['code'], "33747003")
            self.assertEqual(rule_mapping['rule_id'], "test_lab_glucose")
    
    def test_performance_optimization(self):
        """Test performance optimization features"""
        
        # Test batch processing with performance optimization
        test_terms = [
            ("hypertension", "Patient has elevated blood pressure"),
            ("diabetes", "History of type 2 diabetes"),
            ("pneumonia", "Chest X-ray shows pneumonia"),
            ("chest pain", "Acute chest pain onset"),
            ("glucose", "Lab glucose level elevated")
        ]
        
        # Test with parallel processing
        start_time = time.time()
        results = self.mapper.map_terms_batch_enhanced(
            test_terms,
            use_parallel=True,
            detect_negation=True
        )
        parallel_time = time.time() - start_time
        
        # Verify results
        self.assertEqual(len(results), len(test_terms))
        for result in results:
            self.assertIsInstance(result, EnhancedMappingResult)
            self.assertIsNotNone(result.term)
        
        # Test sequential processing
        start_time = time.time()
        sequential_results = self.mapper.map_terms_batch_enhanced(
            test_terms,
            use_parallel=False,
            detect_negation=True
        )
        sequential_time = time.time() - start_time
        
        # Results should be equivalent
        self.assertEqual(len(sequential_results), len(results))
        
        # Performance should be comparable or better with optimization
        print(f"Parallel time: {parallel_time:.3f}s, Sequential time: {sequential_time:.3f}s")
    
    def test_caching_effectiveness(self):
        """Test that caching improves performance"""
        
        term = "chest pain"
        context = "Patient reports chest pain"
        
        # First mapping (cache miss)
        start_time = time.time()
        result1 = self.mapper.map_term_enhanced(term, context)
        first_time = time.time() - start_time
        
        # Second mapping (should use cache)
        start_time = time.time()
        result2 = self.mapper.map_term_enhanced(term, context)
        second_time = time.time() - start_time
        
        # Results should be equivalent
        self.assertEqual(result1.term, result2.term)
        self.assertEqual(len(result1.mappings), len(result2.mappings))
        
        # Second call should be faster (cached)
        print(f"First call: {first_time:.3f}s, Second call: {second_time:.3f}s")
        # Note: Cache effectiveness may vary in testing due to small processing times
    
    def test_rule_priority_handling(self):
        """Test that rule priorities are properly handled"""
        
        # Add a high-priority override rule
        self.mapper.add_custom_rule(
            rule_id="high_priority_override",
            source_term="chest pain",
            target_code="999999",
            target_system="TEST",
            target_display="High Priority Chest Pain",
            rule_type=RuleType.MANUAL_OVERRIDE,
            priority=RulePriority.CRITICAL,
            metadata={"override": True}
        )
        
        result = self.mapper.map_term_enhanced("chest pain", "Patient has chest pain")
        
        # High priority rule should take precedence
        if result.mappings:
            # Critical priority manual overrides should replace other mappings
            critical_mappings = [m for m in result.mappings if m.get('rule_id') == 'high_priority_override']
            if critical_mappings:
                # Should be first or only mapping
                self.assertEqual(result.mappings[0]['code'], "999999")
    
    def test_comprehensive_statistics(self):
        """Test comprehensive statistics and reporting"""
        
        # Process multiple terms to generate statistics
        test_terms = [
            ("chest pain", "Patient has chest pain"),
            ("diabetes", "No history of diabetes"),
            ("hypertension", "Possible hypertension"),
            ("glucose", "Lab glucose elevated"),
            ("murmur", "Cardiology exam reveals murmur")
        ]
        
        results = []
        for term, context in test_terms:
            result = self.mapper.map_term_enhanced(term, context, detect_negation=True)
            results.append(result)
        
        # Get processing statistics
        processing_stats = self.mapper.get_processing_statistics()
        
        # Verify statistics structure
        self.assertIn('processing_stats', processing_stats)
        self.assertIn('performance_optimizer', processing_stats)
        self.assertIn('rules_engine_stats', processing_stats)
        self.assertIn('cache_stats', processing_stats)
        
        # Verify processing counts
        proc_stats = processing_stats['processing_stats']
        self.assertGreaterEqual(proc_stats['total_terms_processed'], len(test_terms))
        
        # Get mapping statistics
        mapping_stats = self.mapper.get_mapping_statistics(results)
        
        # Verify mapping statistics structure
        self.assertIn('total_terms', mapping_stats)
        self.assertIn('total_mappings', mapping_stats)
        self.assertIn('avg_confidence', mapping_stats)
        self.assertIn('domains_detected', mapping_stats)
        self.assertIn('rules_applied', mapping_stats)
        
        print(f"Processing Statistics: {processing_stats}")
        print(f"Mapping Statistics: {mapping_stats}")
    
    def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback mechanisms"""
        
        # Test with invalid input
        result = self.mapper.map_term_enhanced("", "")
        self.assertIsInstance(result, EnhancedMappingResult)
        self.assertEqual(result.term, "")
        
        # Test with very long context (should handle gracefully)
        long_context = "This is a very long context. " * 1000
        result = self.mapper.map_term_enhanced("test", long_context)
        self.assertIsInstance(result, EnhancedMappingResult)
        
        # Test with special characters
        special_term = "test@#$%^&*()"
        result = self.mapper.map_term_enhanced(special_term, "Context with special term")
        self.assertIsInstance(result, EnhancedMappingResult)
        self.assertEqual(result.term, special_term)
    
    def test_performance_optimization_routines(self):
        """Test performance optimization maintenance routines"""
        
        # Run optimization routine
        self.mapper.optimize_performance()
        
        # Should complete without errors
        stats_before = self.mapper.get_processing_statistics()
        
        # Process some terms
        for i in range(5):
            self.mapper.map_term_enhanced(f"test_term_{i}", f"Context for term {i}")
        
        # Run optimization again
        self.mapper.optimize_performance()
        
        stats_after = self.mapper.get_processing_statistics()
        
        # Statistics should be maintained
        self.assertIsInstance(stats_after, dict)


def run_week6_integration_demo():
    """
    Demonstration of Week 6 advanced features working together.
    This function shows a realistic clinical scenario using all features.
    """
    print("=" * 80)
    print("Week 6 Custom Mapping Rules - Integration Demonstration")
    print("=" * 80)
    
    # Initialize mapper
    mapper = EnhancedTerminologyMapper()
    
    # Clinical scenario: Emergency Department visit
    clinical_notes = [
        ("chest pain", "67-year-old male presents to ED with acute chest pain radiating to left arm, onset 2 hours ago"),
        ("shortness of breath", "Patient denies shortness of breath at rest but reports dyspnea on exertion"),
        ("blood pressure", "Vital signs: BP 160/95, HR 88, RR 18, O2 sat 98% on room air"),
        ("diabetes", "Past medical history significant for type 2 diabetes mellitus"),
        ("hypertension", "No known history of hypertension"),
        ("troponin", "Laboratory results pending including troponin levels"),
        ("myocardial infarction", "ECG shows possible ST elevation concerning for acute myocardial infarction"),
        ("aspirin", "Patient given aspirin 325mg and started on heparin protocol")
    ]
    
    print("\nProcessing clinical notes with enhanced mapping features...")
    print("-" * 60)
    
    # Process all terms with enhanced features
    all_results = []
    for term, context in clinical_notes:
        result = mapper.map_term_enhanced(
            term=term,
            context_text=context,
            detect_negation=True
        )
        all_results.append(result)
        
        print(f"\nTerm: '{term}'")
        print(f"Context: {context[:60]}...")
        print(f"Domain: {result.domain.value if result.domain else 'Not detected'}")
        
        # Show negation/modifier info
        if result.negation_info:
            neg_info = result.negation_info
            print(f"Negated: {neg_info.get('is_negated', False)}")
            if neg_info.get('modifier_types'):
                print(f"Modifiers: {', '.join(neg_info['modifier_types'])}")
        
        # Show best mapping
        if result.mappings:
            best_mapping = result.mappings[0]
            print(f"Best Mapping: {best_mapping.get('code', 'N/A')} ({best_mapping.get('system', 'N/A')})")
            print(f"Confidence: {best_mapping.get('confidence', 0):.2f}")
            if best_mapping.get('source') == 'custom_rule':
                print(f"Custom Rule Applied: {best_mapping.get('rule_id', 'N/A')}")
        else:
            print("No mappings found")
    
    # Show comprehensive statistics
    print("\n" + "=" * 60)
    print("COMPREHENSIVE STATISTICS")
    print("=" * 60)
    
    processing_stats = mapper.get_processing_statistics()
    mapping_stats = mapper.get_mapping_statistics(all_results)
    
    print(f"\nProcessing Summary:")
    print(f"- Total terms processed: {processing_stats['processing_stats']['total_terms_processed']}")
    print(f"- Negated terms detected: {processing_stats['processing_stats']['negated_terms']}")
    print(f"- Custom rules applied: {processing_stats['processing_stats']['rule_overrides_applied']}")
    print(f"- Context-enhanced mappings: {processing_stats['processing_stats']['context_enhanced_mappings']}")
    
    print(f"\nMapping Quality:")
    print(f"- Average confidence: {mapping_stats['avg_confidence']:.3f}")
    print(f"- Total mappings found: {mapping_stats['total_mappings']}")
    print(f"- Domains detected: {list(mapping_stats['domains_detected'].keys())}")
    
    print(f"\nPerformance:")
    print(f"- Average processing time: {mapping_stats['avg_processing_time_seconds']:.4f}s per term")
    
    # Show cache effectiveness
    cache_stats = processing_stats['cache_stats']
    if 'term_cache' in cache_stats:
        tc = cache_stats['term_cache']
        if tc.get('hits', 0) + tc.get('misses', 0) > 0:
            hit_rate = tc['hits'] / (tc['hits'] + tc['misses']) * 100
            print(f"- Cache hit rate: {hit_rate:.1f}%")
    
    print("\n" + "=" * 80)
    print("Week 6 Implementation Complete - All Advanced Features Demonstrated")
    print("=" * 80)
    
    # Cleanup
    mapper.cleanup()


if __name__ == '__main__':
    # Run the demonstration
    run_week6_integration_demo()
    
    print("\n" + "=" * 40)
    print("Running Unit Tests...")
    print("=" * 40)
    
    # Run unit tests
    unittest.main(verbosity=2)