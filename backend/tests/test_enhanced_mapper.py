#!/usr/bin/env python3
"""Tests for Enhanced Terminology Mapper functionality"""

import unittest
import tempfile
import os
from datetime import datetime

from app.standards.terminology.enhanced_mapper import EnhancedTerminologyMapper, EnhancedMappingResult
from app.standards.terminology.context_aware_mapper import ClinicalDomain
from app.standards.terminology.custom_mapping_rules import RuleType, RulePriority

class TestEnhancedMapper(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_terminology_path = "data/terminology"  # Use existing test data
        self.test_rules_db = os.path.join(self.temp_dir, "test_enhanced_rules.sqlite")
        
        # Create enhanced mapper
        self.enhanced_mapper = EnhancedTerminologyMapper(
            terminology_db_path=self.test_terminology_path,
            custom_rules_db_path=self.test_rules_db
        )
        
        # Add some test custom rules
        self._setup_test_rules()
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_test_rules(self):
        """Set up test custom mapping rules"""
        # Add exact match rule
        self.enhanced_mapper.add_custom_rule(
            rule_id="test_chest_pain",
            source_term="chest pain",
            target_code="29857009",
            target_system="SNOMED",
            target_display="Chest pain (finding)",
            rule_type=RuleType.EXACT_MATCH,
            priority=RulePriority.HIGH,
            metadata={"category": "symptom", "test_rule": True},
            created_by="test_setup"
        )
        
        # Add pattern match rule
        self.enhanced_mapper.add_custom_rule(
            rule_id="test_bp_pattern",
            source_term="blood pressure",
            target_code="75367002",
            target_system="SNOMED",
            target_display="Blood pressure (observable entity)",
            rule_type=RuleType.PATTERN_MATCH,
            priority=RulePriority.MEDIUM,
            conditions={"pattern": r"blood\s+pressure|bp"},
            metadata={"category": "vital_sign", "test_rule": True},
            created_by="test_setup"
        )
        
        # Add context-dependent rule
        self.enhanced_mapper.add_custom_rule(
            rule_id="test_cardiac_pain",
            source_term="pain",
            target_code="194828000",
            target_system="SNOMED",
            target_display="Angina (disorder)",
            rule_type=RuleType.CONTEXT_DEPENDENT,
            priority=RulePriority.HIGH,
            conditions={"required_context": {"domain": "cardiology"}},
            metadata={"category": "cardiac_symptom", "test_rule": True},
            created_by="test_setup"
        )
    
    def test_enhanced_mapper_initialization(self):
        """Test that enhanced mapper initializes correctly"""
        self.assertIsNotNone(self.enhanced_mapper.base_mapper)
        self.assertIsNotNone(self.enhanced_mapper.context_mapper)
        self.assertIsNotNone(self.enhanced_mapper.rules_engine)
    
    def test_basic_enhanced_mapping(self):
        """Test basic enhanced term mapping without context"""
        result = self.enhanced_mapper.map_term_enhanced("chest pain")
        
        self.assertIsInstance(result, EnhancedMappingResult)
        self.assertEqual(result.term, "chest pain")
        self.assertGreater(len(result.mappings), 0)
        self.assertIsNotNone(result.processing_metadata)
        
        # Should have applied the custom rule
        custom_mapping = next((m for m in result.mappings if m.get('source') == 'custom_rule'), None)
        self.assertIsNotNone(custom_mapping)
        self.assertEqual(custom_mapping['code'], '29857009')
    
    def test_enhanced_mapping_with_context(self):
        """Test enhanced mapping with clinical context"""
        context_text = "Patient presents with acute chest pain and shortness of breath in the emergency department"
        
        result = self.enhanced_mapper.map_term_enhanced(
            "chest pain", 
            context_text=context_text
        )
        
        self.assertIsNotNone(result.context_info)
        self.assertEqual(result.context_info['context_text'], context_text)
        self.assertIsNotNone(result.domain)
        self.assertIsNotNone(result.confidence_scores)
    
    def test_enhanced_mapping_with_domain_hint(self):
        """Test enhanced mapping with domain hint"""
        result = self.enhanced_mapper.map_term_enhanced(
            "pain",
            context_text="cardiac evaluation",
            domain_hint=ClinicalDomain.CARDIOLOGY
        )
        
        self.assertEqual(result.context_info['domain_hint'], 'cardiology')
        
        # Should apply context-dependent cardiac rule
        custom_mapping = next((m for m in result.mappings if m.get('rule_id') == 'test_cardiac_pain'), None)
        self.assertIsNotNone(custom_mapping)
        self.assertEqual(custom_mapping['code'], '194828000')
    
    def test_pattern_rule_application(self):
        """Test that pattern matching rules are applied"""
        test_terms = ["bp", "Blood Pressure", "blood pressure"]
        
        for term in test_terms:
            result = self.enhanced_mapper.map_term_enhanced(term)
            
            # Should find the pattern rule mapping
            pattern_mapping = next((m for m in result.mappings if m.get('rule_id') == 'test_bp_pattern'), None)
            self.assertIsNotNone(pattern_mapping, f"Pattern rule should match '{term}'")
            self.assertEqual(pattern_mapping['code'], '75367002')
    
    def test_custom_rules_disabled(self):
        """Test enhanced mapping with custom rules disabled"""
        result = self.enhanced_mapper.map_term_enhanced(
            "chest pain", 
            apply_custom_rules=False
        )
        
        # Should not have any custom rule mappings
        custom_mappings = [m for m in result.mappings if m.get('source') == 'custom_rule']
        self.assertEqual(len(custom_mappings), 0)
        
        # Metadata should reflect this
        self.assertFalse(result.processing_metadata['custom_rules_enabled'])
        self.assertEqual(result.processing_metadata['rules_applied_count'], 0)
    
    def test_batch_mapping(self):
        """Test batch mapping functionality"""
        terms_with_context = [
            ("chest pain", "patient with cardiac symptoms"),
            ("blood pressure", "vital signs monitoring"),
            ("headache", "neurological examination")
        ]
        
        results = self.enhanced_mapper.batch_map_terms(
            terms_with_context,
            domain_hint=ClinicalDomain.CARDIOLOGY
        )
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, EnhancedMappingResult)
            self.assertGreater(len(result.mappings), 0)
    
    def test_mapping_statistics(self):
        """Test mapping statistics generation"""
        # Create some mapping results
        results = [
            self.enhanced_mapper.map_term_enhanced("chest pain"),
            self.enhanced_mapper.map_term_enhanced("blood pressure"),
            self.enhanced_mapper.map_term_enhanced("headache")
        ]
        
        stats = self.enhanced_mapper.get_mapping_statistics(results)
        
        self.assertEqual(stats['total_terms'], 3)
        self.assertGreater(stats['total_mappings'], 0)
        self.assertGreaterEqual(stats['avg_mappings_per_term'], 1.0)
        self.assertGreaterEqual(stats['avg_confidence'], 0.0)
        self.assertGreater(stats['avg_processing_time_seconds'], 0.0)
        self.assertIn('confidence_distribution', stats)
    
    def test_add_custom_rule_via_mapper(self):
        """Test adding custom rules through the enhanced mapper"""
        success = self.enhanced_mapper.add_custom_rule(
            rule_id="test_new_rule",
            source_term="fever",
            target_code="386661006",
            target_system="SNOMED",
            target_display="Fever (finding)",
            rule_type=RuleType.EXACT_MATCH,
            priority=RulePriority.MEDIUM,
            metadata={"test": "new_rule"}
        )
        
        self.assertTrue(success)
        
        # Test that the rule is applied
        result = self.enhanced_mapper.map_term_enhanced("fever")
        custom_mapping = next((m for m in result.mappings if m.get('rule_id') == 'test_new_rule'), None)
        self.assertIsNotNone(custom_mapping)
    
    def test_manual_override_rule(self):
        """Test manual override rule behavior"""
        # Add a manual override rule
        success = self.enhanced_mapper.add_custom_rule(
            rule_id="test_override",
            source_term="chest pain",
            target_code="999999",
            target_system="CUSTOM",
            target_display="Custom Override Chest Pain",
            rule_type=RuleType.MANUAL_OVERRIDE,
            priority=RulePriority.CRITICAL,
            metadata={"override": True}
        )
        
        self.assertTrue(success)
        
        # Should replace all other mappings
        result = self.enhanced_mapper.map_term_enhanced("chest pain")
        self.assertEqual(len(result.mappings), 1)
        self.assertEqual(result.mappings[0]['code'], '999999')
        self.assertEqual(result.mappings[0]['source'], 'custom_rule')
    
    def test_get_custom_rules(self):
        """Test retrieving custom rules"""
        rules = self.enhanced_mapper.get_custom_rules()
        
        # Should have the rules we added in setup
        self.assertGreaterEqual(len(rules), 3)
        
        rule_ids = [rule.rule_id for rule in rules]
        self.assertIn("test_chest_pain", rule_ids)
        self.assertIn("test_bp_pattern", rule_ids)
        self.assertIn("test_cardiac_pain", rule_ids)
    
    def test_export_import_custom_rules(self):
        """Test exporting and importing custom rules"""
        export_file = os.path.join(self.temp_dir, "exported_enhanced_rules.json")
        
        # Export rules
        success = self.enhanced_mapper.export_custom_rules(export_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_file))
        
        # Create new mapper and import
        new_rules_db = os.path.join(self.temp_dir, "new_enhanced_rules.sqlite")
        new_mapper = EnhancedTerminologyMapper(
            terminology_db_path=self.test_terminology_path,
            custom_rules_db_path=new_rules_db
        )
        
        successful, failed, errors = new_mapper.import_custom_rules(export_file)
        self.assertGreater(successful, 0)
        self.assertEqual(failed, 0)
        self.assertEqual(len(errors), 0)
    
    def test_validate_term_mapping(self):
        """Test term mapping validation"""
        validation = self.enhanced_mapper.validate_term_mapping(
            "chest pain", 
            "29857009", 
            "SNOMED"
        )
        
        self.assertEqual(validation['term'], "chest pain")
        self.assertEqual(validation['expected_code'], "29857009")
        self.assertEqual(validation['expected_system'], "SNOMED")
        self.assertTrue(validation['exact_match_found'])
        self.assertIsNotNone(validation['best_match'])
    
    def test_error_handling_fallback(self):
        """Test error handling and fallback behavior"""
        # Create mapper with invalid paths to trigger errors in context mapping
        invalid_mapper = EnhancedTerminologyMapper(
            terminology_db_path="/invalid/path",
            custom_rules_db_path=self.test_rules_db
        )
        
        # Should still return a result using fallback
        result = invalid_mapper.map_term_enhanced("test term")
        self.assertIsInstance(result, EnhancedMappingResult)
        self.assertIn('error', result.processing_metadata)
        self.assertTrue(result.processing_metadata.get('fallback_used', False))
    
    def test_confidence_scoring(self):
        """Test confidence scoring in enhanced mappings"""
        result = self.enhanced_mapper.map_term_enhanced("chest pain")
        
        self.assertIsNotNone(result.confidence_scores)
        self.assertGreater(len(result.confidence_scores), 0)
        
        # All confidence scores should be between 0 and 1
        for score in result.confidence_scores:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
    
    def test_processing_metadata(self):
        """Test processing metadata completeness"""
        result = self.enhanced_mapper.map_term_enhanced("chest pain")
        
        metadata = result.processing_metadata
        self.assertIn('processing_time_seconds', metadata)
        self.assertIn('context_aware_enabled', metadata)
        self.assertIn('custom_rules_enabled', metadata)
        self.assertIn('rules_applied_count', metadata)
        self.assertIn('base_mappings_count', metadata)
        self.assertIn('final_mappings_count', metadata)
        self.assertIn('timestamp', metadata)
        
        self.assertGreater(metadata['processing_time_seconds'], 0)
        self.assertTrue(metadata['context_aware_enabled'])
        self.assertTrue(metadata['custom_rules_enabled'])
    
    def test_applied_rules_tracking(self):
        """Test that applied rules are properly tracked"""
        result = self.enhanced_mapper.map_term_enhanced("chest pain")
        
        self.assertIsNotNone(result.applied_rules)
        self.assertGreater(len(result.applied_rules), 0)
        
        # Check rule information
        for applied_rule in result.applied_rules:
            self.assertIn('rule_id', applied_rule)
            self.assertIn('rule_type', applied_rule)
            self.assertIn('match_reason', applied_rule)
            self.assertIn('confidence', applied_rule)
    
    def test_context_info_preservation(self):
        """Test that context information is preserved in results"""
        context_text = "patient with cardiac symptoms"
        domain_hint = ClinicalDomain.CARDIOLOGY
        
        result = self.enhanced_mapper.map_term_enhanced(
            "pain",
            context_text=context_text,
            domain_hint=domain_hint
        )
        
        context_info = result.context_info
        self.assertIsNotNone(context_info)
        self.assertEqual(context_info['context_text'], context_text)
        self.assertEqual(context_info['domain_hint'], domain_hint.value)
        self.assertIn('clinical_context', context_info)

if __name__ == '__main__':
    unittest.main()