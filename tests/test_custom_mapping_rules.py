#!/usr/bin/env python3
"""Tests for Custom Mapping Rules functionality"""

import unittest
import tempfile
import os
import json
from datetime import datetime

from app.standards.terminology.custom_mapping_rules import (
    CustomMappingRulesEngine, CustomMappingRule, RuleType, RulePriority, RuleMatch
)

class TestCustomMappingRules(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_custom_rules.sqlite")
        self.rules_engine = CustomMappingRulesEngine(self.test_db_path)
        
        # Create sample rules
        self.sample_rule_exact = CustomMappingRule(
            rule_id="test_exact_001",
            rule_type=RuleType.EXACT_MATCH,
            priority=RulePriority.HIGH,
            source_term="chest pain",
            target_code="29857009",
            target_system="SNOMED",
            target_display="Chest pain",
            conditions={},
            metadata={"category": "symptom"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test_user"
        )
        
        self.sample_rule_pattern = CustomMappingRule(
            rule_id="test_pattern_001",
            rule_type=RuleType.PATTERN_MATCH,
            priority=RulePriority.MEDIUM,
            source_term="blood pressure",
            target_code="75367002",
            target_system="SNOMED",
            target_display="Blood pressure",
            conditions={"pattern": r"blood\s+pressure|bp"},
            metadata={"category": "vital_sign"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test_user"
        )
        
        self.sample_rule_context = CustomMappingRule(
            rule_id="test_context_001",
            rule_type=RuleType.CONTEXT_DEPENDENT,
            priority=RulePriority.HIGH,
            source_term="pain",
            target_code="22253000",
            target_system="SNOMED",
            target_display="Pain",
            conditions={"required_context": {"domain": "cardiology"}},
            metadata={"category": "symptom"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test_user"
        )
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_database_initialization(self):
        """Test that the database is properly initialized"""
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Test that we can create another engine instance
        engine2 = CustomMappingRulesEngine(self.test_db_path)
        self.assertIsInstance(engine2, CustomMappingRulesEngine)
    
    def test_add_rule(self):
        """Test adding a custom rule"""
        success = self.rules_engine.add_rule(self.sample_rule_exact)
        self.assertTrue(success)
        
        # Verify rule was added
        retrieved_rule = self.rules_engine.get_rule("test_exact_001")
        self.assertIsNotNone(retrieved_rule)
        self.assertEqual(retrieved_rule.source_term, "chest pain")
        self.assertEqual(retrieved_rule.target_code, "29857009")
    
    def test_update_rule(self):
        """Test updating a custom rule"""
        # First add a rule
        self.rules_engine.add_rule(self.sample_rule_exact)
        
        # Update it
        updates = {
            "target_display": "Updated Chest Pain",
            "metadata": json.dumps({"category": "updated_symptom"})
        }
        success = self.rules_engine.update_rule("test_exact_001", updates)
        self.assertTrue(success)
        
        # Verify update
        retrieved_rule = self.rules_engine.get_rule("test_exact_001")
        self.assertEqual(retrieved_rule.target_display, "Updated Chest Pain")
        self.assertEqual(retrieved_rule.metadata["category"], "updated_symptom")
    
    def test_delete_rule(self):
        """Test deleting (deactivating) a custom rule"""
        # Add rule
        self.rules_engine.add_rule(self.sample_rule_exact)
        
        # Delete it
        success = self.rules_engine.delete_rule("test_exact_001")
        self.assertTrue(success)
        
        # Rule should still exist but be inactive
        retrieved_rule = self.rules_engine.get_rule("test_exact_001")
        self.assertIsNotNone(retrieved_rule)
        self.assertFalse(retrieved_rule.is_active)
    
    def test_exact_match_rule(self):
        """Test exact match rule evaluation"""
        self.rules_engine.add_rule(self.sample_rule_exact)
        
        # Should match exact term
        matches = self.rules_engine.find_matching_rules("chest pain")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].confidence, 1.0)
        self.assertEqual(matches[0].match_reason, "Exact term match")
        
        # Should match case-insensitive
        matches = self.rules_engine.find_matching_rules("CHEST PAIN")
        self.assertEqual(len(matches), 1)
        
        # Should not match different term
        matches = self.rules_engine.find_matching_rules("stomach pain")
        self.assertEqual(len(matches), 0)
    
    def test_pattern_match_rule(self):
        """Test pattern match rule evaluation"""
        self.rules_engine.add_rule(self.sample_rule_pattern)
        
        # Should match pattern variations
        test_terms = [
            "blood pressure",
            "Blood Pressure",
            "bp",
            "BP",
            "blood  pressure"  # Extra space
        ]
        
        for term in test_terms:
            matches = self.rules_engine.find_matching_rules(term)
            self.assertGreater(len(matches), 0, f"Pattern should match '{term}'")
            self.assertEqual(matches[0].confidence, 0.8)
        
        # Should not match unrelated terms
        matches = self.rules_engine.find_matching_rules("heart rate")
        self.assertEqual(len(matches), 0)
    
    def test_context_dependent_rule(self):
        """Test context-dependent rule evaluation"""
        self.rules_engine.add_rule(self.sample_rule_context)
        
        # Should match with correct context
        context = {"domain": "cardiology"}
        matches = self.rules_engine.find_matching_rules("pain", context)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].confidence, 0.9)
        
        # Should not match with wrong context
        context = {"domain": "neurology"}
        matches = self.rules_engine.find_matching_rules("pain", context)
        self.assertEqual(len(matches), 0)
        
        # Should not match without context
        matches = self.rules_engine.find_matching_rules("pain")
        self.assertEqual(len(matches), 0)
    
    def test_rule_priority_ordering(self):
        """Test that rules are returned in priority order"""
        # Create rules with different priorities
        high_priority_rule = CustomMappingRule(
            rule_id="high_priority",
            rule_type=RuleType.EXACT_MATCH,
            priority=RulePriority.HIGH,
            source_term="test term",
            target_code="001",
            target_system="SNOMED",
            target_display="Test Term High",
            conditions={},
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test"
        )
        
        low_priority_rule = CustomMappingRule(
            rule_id="low_priority",
            rule_type=RuleType.EXACT_MATCH,
            priority=RulePriority.LOW,
            source_term="test term",
            target_code="002",
            target_system="SNOMED",
            target_display="Test Term Low",
            conditions={},
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test"
        )
        
        # Add in reverse priority order
        self.rules_engine.add_rule(low_priority_rule)
        self.rules_engine.add_rule(high_priority_rule)
        
        # Should return high priority first
        matches = self.rules_engine.find_matching_rules("test term")
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0].rule.priority, RulePriority.HIGH)
        self.assertEqual(matches[1].rule.priority, RulePriority.LOW)
    
    def test_apply_rules_to_mappings(self):
        """Test applying rules to enhance base mappings"""
        self.rules_engine.add_rule(self.sample_rule_exact)
        
        # Base mappings from standard terminology
        base_mappings = [
            {
                'code': '123456',
                'system': 'LOINC',
                'display': 'Generic chest pain',
                'confidence': 0.7,
                'source': 'fuzzy_match'
            }
        ]
        
        # Apply rules
        enhanced_mappings = self.rules_engine.apply_rules("chest pain", base_mappings)
        
        # Should prepend the custom rule mapping
        self.assertEqual(len(enhanced_mappings), 2)
        self.assertEqual(enhanced_mappings[0]['source'], 'custom_rule')
        self.assertEqual(enhanced_mappings[0]['code'], '29857009')
        self.assertEqual(enhanced_mappings[1]['code'], '123456')  # Original mapping
    
    def test_manual_override_rule(self):
        """Test that manual override rules replace all other mappings"""
        override_rule = CustomMappingRule(
            rule_id="override_001",
            rule_type=RuleType.MANUAL_OVERRIDE,
            priority=RulePriority.CRITICAL,
            source_term="chest pain",
            target_code="999999",
            target_system="CUSTOM",
            target_display="Custom Chest Pain",
            conditions={},
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test"
        )
        
        self.rules_engine.add_rule(override_rule)
        
        base_mappings = [
            {'code': '123456', 'system': 'LOINC', 'display': 'Generic', 'confidence': 0.7}
        ]
        
        enhanced_mappings = self.rules_engine.apply_rules("chest pain", base_mappings)
        
        # Should replace all base mappings
        self.assertEqual(len(enhanced_mappings), 1)
        self.assertEqual(enhanced_mappings[0]['source'], 'custom_rule')
        self.assertEqual(enhanced_mappings[0]['code'], '999999')
    
    def test_rule_validation(self):
        """Test custom rule validation"""
        # Valid rule should pass
        is_valid, errors = self.rules_engine.validate_rule(self.sample_rule_exact)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Invalid rule with missing fields
        invalid_rule = CustomMappingRule(
            rule_id="",  # Missing
            rule_type=RuleType.EXACT_MATCH,
            priority=RulePriority.HIGH,
            source_term="",  # Missing
            target_code="",  # Missing
            target_system="SNOMED",
            target_display="Test",
            conditions={},
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test"
        )
        
        is_valid, errors = self.rules_engine.validate_rule(invalid_rule)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_pattern_rule_validation(self):
        """Test validation of pattern match rules"""
        # Valid pattern rule
        pattern_rule = CustomMappingRule(
            rule_id="pattern_test",
            rule_type=RuleType.PATTERN_MATCH,
            priority=RulePriority.MEDIUM,
            source_term="test",
            target_code="123",
            target_system="SNOMED",
            target_display="Test",
            conditions={"pattern": r"\d+"},  # Valid regex
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test"
        )
        
        is_valid, errors = self.rules_engine.validate_rule(pattern_rule)
        self.assertTrue(is_valid)
        
        # Invalid pattern rule with bad regex
        pattern_rule.conditions = {"pattern": r"["}  # Invalid regex
        is_valid, errors = self.rules_engine.validate_rule(pattern_rule)
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid regex pattern" in error for error in errors))
    
    def test_export_import_rules(self):
        """Test exporting and importing rules to/from JSON"""
        # Add some rules
        self.rules_engine.add_rule(self.sample_rule_exact)
        self.rules_engine.add_rule(self.sample_rule_pattern)
        
        # Export to JSON
        export_file = os.path.join(self.temp_dir, "exported_rules.json")
        success = self.rules_engine.export_rules_to_json(export_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_file))
        
        # Create new engine and import
        new_db_path = os.path.join(self.temp_dir, "new_rules.sqlite")
        new_engine = CustomMappingRulesEngine(new_db_path)
        
        successful, failed, errors = new_engine.import_rules_from_json(export_file)
        self.assertEqual(successful, 2)
        self.assertEqual(failed, 0)
        self.assertEqual(len(errors), 0)
        
        # Verify imported rules
        imported_rules = new_engine.get_all_rules()
        self.assertEqual(len(imported_rules), 2)
    
    def test_get_all_rules(self):
        """Test retrieving all rules"""
        # Initially empty
        rules = self.rules_engine.get_all_rules()
        self.assertEqual(len(rules), 0)
        
        # Add rules
        self.rules_engine.add_rule(self.sample_rule_exact)
        self.rules_engine.add_rule(self.sample_rule_pattern)
        
        # Should return active rules
        rules = self.rules_engine.get_all_rules()
        self.assertEqual(len(rules), 2)
        
        # Deactivate one rule
        self.rules_engine.delete_rule("test_exact_001")
        
        # Should return only active rules by default
        rules = self.rules_engine.get_all_rules()
        self.assertEqual(len(rules), 1)
        
        # Should return all rules including inactive when requested
        rules = self.rules_engine.get_all_rules(include_inactive=True)
        self.assertEqual(len(rules), 2)
    
    def test_domain_specific_rule(self):
        """Test domain-specific rule evaluation"""
        domain_rule = CustomMappingRule(
            rule_id="domain_test",
            rule_type=RuleType.DOMAIN_SPECIFIC,
            priority=RulePriority.HIGH,
            source_term="murmur",
            target_code="cardiac_murmur_001",
            target_system="SNOMED",
            target_display="Cardiac murmur",
            conditions={"domain": "cardiology"},
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test"
        )
        
        self.rules_engine.add_rule(domain_rule)
        
        # Should match with correct domain
        context = {"domain": "cardiology"}
        matches = self.rules_engine.find_matching_rules("murmur", context)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].confidence, 0.85)
        
        # Should not match with different domain
        context = {"domain": "neurology"}
        matches = self.rules_engine.find_matching_rules("murmur", context)
        self.assertEqual(len(matches), 0)

if __name__ == '__main__':
    unittest.main()