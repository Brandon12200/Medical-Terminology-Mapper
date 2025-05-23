"""Custom Mapping Rules Infrastructure for Medical Terminology Mapper

This module provides infrastructure for creating, managing, and applying custom mapping rules
that override default terminology mappings. Supports rule-based overrides, manual mappings,
and custom validation logic.
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class RuleType(Enum):
    """Types of custom mapping rules"""
    EXACT_MATCH = "exact_match"
    PATTERN_MATCH = "pattern_match"
    CONTEXT_DEPENDENT = "context_dependent"
    DOMAIN_SPECIFIC = "domain_specific"
    MANUAL_OVERRIDE = "manual_override"

class RulePriority(Enum):
    """Priority levels for rule application"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class CustomMappingRule:
    """Represents a custom mapping rule"""
    rule_id: str
    rule_type: RuleType
    priority: RulePriority
    source_term: str
    target_code: str
    target_system: str
    target_display: str
    conditions: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: str
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary format"""
        return {
            'rule_id': self.rule_id,
            'rule_type': self.rule_type.value,
            'priority': self.priority.value,
            'source_term': self.source_term,
            'target_code': self.target_code,
            'target_system': self.target_system,
            'target_display': self.target_display,
            'conditions': json.dumps(self.conditions),
            'metadata': json.dumps(self.metadata),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomMappingRule':
        """Create rule from dictionary format"""
        return cls(
            rule_id=data['rule_id'],
            rule_type=RuleType(data['rule_type']),
            priority=RulePriority(data['priority']),
            source_term=data['source_term'],
            target_code=data['target_code'],
            target_system=data['target_system'],
            target_display=data['target_display'],
            conditions=json.loads(data['conditions']) if isinstance(data['conditions'], str) else data['conditions'],
            metadata=json.loads(data['metadata']) if isinstance(data['metadata'], str) else data['metadata'],
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
            updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at'],
            created_by=data['created_by'],
            is_active=data.get('is_active', True)
        )

@dataclass
class RuleMatch:
    """Represents a rule match result"""
    rule: CustomMappingRule
    confidence: float
    match_reason: str
    context_data: Dict[str, Any]

class CustomMappingRulesEngine:
    """Engine for managing and applying custom mapping rules"""
    
    def __init__(self, db_path: str = "data/terminology/custom_rules.sqlite"):
        self.db_path = db_path
        self._ensure_database()
        self._rule_cache: Dict[str, List[CustomMappingRule]] = {}
        self._load_rules_cache()
    
    def _ensure_database(self):
        """Ensure the custom rules database exists with proper schema"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_mapping_rules (
                    rule_id TEXT PRIMARY KEY,
                    rule_type TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    source_term TEXT NOT NULL,
                    target_code TEXT NOT NULL,
                    target_system TEXT NOT NULL,
                    target_display TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_source_term ON custom_mapping_rules(source_term)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rule_type ON custom_mapping_rules(rule_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_priority ON custom_mapping_rules(priority)
            """)
    
    def _load_rules_cache(self):
        """Load active rules into memory cache"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM custom_mapping_rules 
                WHERE is_active = TRUE 
                ORDER BY priority ASC, created_at ASC
            """)
            
            self._rule_cache.clear()
            for row in cursor:
                rule = CustomMappingRule.from_dict(dict(row))
                if rule.source_term not in self._rule_cache:
                    self._rule_cache[rule.source_term] = []
                self._rule_cache[rule.source_term].append(rule)
    
    def add_rule(self, rule: CustomMappingRule) -> bool:
        """Add a new custom mapping rule"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO custom_mapping_rules 
                    (rule_id, rule_type, priority, source_term, target_code, target_system,
                     target_display, conditions, metadata, created_at, updated_at, created_by, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.rule_id, rule.rule_type.value, rule.priority.value,
                    rule.source_term, rule.target_code, rule.target_system,
                    rule.target_display, json.dumps(rule.conditions),
                    json.dumps(rule.metadata), rule.created_at.isoformat(),
                    rule.updated_at.isoformat(), rule.created_by, rule.is_active
                ))
            
            # Update cache
            if rule.source_term not in self._rule_cache:
                self._rule_cache[rule.source_term] = []
            self._rule_cache[rule.source_term].append(rule)
            
            logger.info(f"Added custom mapping rule: {rule.rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding custom mapping rule: {e}")
            return False
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing custom mapping rule"""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [rule_id]
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f"""
                    UPDATE custom_mapping_rules 
                    SET {set_clause}
                    WHERE rule_id = ?
                """, values)
            
            # Refresh cache
            self._load_rules_cache()
            
            logger.info(f"Updated custom mapping rule: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating custom mapping rule: {e}")
            return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a custom mapping rule (soft delete)"""
        return self.update_rule(rule_id, {'is_active': False})
    
    def get_rule(self, rule_id: str) -> Optional[CustomMappingRule]:
        """Get a specific rule by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM custom_mapping_rules WHERE rule_id = ?
                """, (rule_id,))
                
                row = cursor.fetchone()
                if row:
                    return CustomMappingRule.from_dict(dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving custom mapping rule: {e}")
            return None
    
    def find_matching_rules(self, term: str, context: Dict[str, Any] = None) -> List[RuleMatch]:
        """Find all rules that match the given term and context"""
        matches = []
        context = context or {}
        
        # Check all rules for potential matches
        for source_term, rules in self._rule_cache.items():
            for rule in rules:
                match = self._evaluate_rule_match(rule, term, context)
                if match:
                    matches.append(match)
        
        # Sort by priority and confidence
        matches.sort(key=lambda m: (m.rule.priority.value, -m.confidence))
        
        return matches
    
    def _evaluate_rule_match(self, rule: CustomMappingRule, term: str, context: Dict[str, Any]) -> Optional[RuleMatch]:
        """Evaluate if a rule matches the given term and context"""
        try:
            confidence = 0.0
            match_reason = ""
            
            # Check rule type specific matching
            if rule.rule_type == RuleType.EXACT_MATCH:
                if rule.source_term.lower() == term.lower():
                    confidence = 1.0
                    match_reason = "Exact term match"
                else:
                    return None
            
            elif rule.rule_type == RuleType.PATTERN_MATCH:
                import re
                pattern = rule.conditions.get('pattern', rule.source_term)
                if re.search(pattern, term, re.IGNORECASE):
                    confidence = 0.8
                    match_reason = f"Pattern match: {pattern}"
                else:
                    return None
            
            elif rule.rule_type == RuleType.CONTEXT_DEPENDENT:
                # Check if context conditions are met
                required_context = rule.conditions.get('required_context', {})
                if all(context.get(key) == value for key, value in required_context.items()):
                    confidence = 0.9
                    match_reason = "Context conditions met"
                else:
                    return None
            
            elif rule.rule_type == RuleType.DOMAIN_SPECIFIC:
                # Check if domain matches
                required_domain = rule.conditions.get('domain')
                if context.get('domain') == required_domain:
                    confidence = 0.85
                    match_reason = f"Domain match: {required_domain}"
                else:
                    return None
            
            elif rule.rule_type == RuleType.MANUAL_OVERRIDE:
                # Manual overrides always match if term matches
                if rule.source_term.lower() == term.lower():
                    confidence = 1.0
                    match_reason = "Manual override"
                else:
                    return None
            
            # Additional condition checks
            if 'min_confidence' in rule.conditions:
                min_conf = rule.conditions['min_confidence']
                if confidence < min_conf:
                    return None
            
            return RuleMatch(
                rule=rule,
                confidence=confidence,
                match_reason=match_reason,
                context_data=context
            )
            
        except Exception as e:
            logger.error(f"Error evaluating rule match: {e}")
            return None
    
    def apply_rules(self, term: str, base_mappings: List[Dict[str, Any]], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Apply custom mapping rules to enhance base mappings"""
        context = context or {}
        rule_matches = self.find_matching_rules(term, context)
        
        if not rule_matches:
            return base_mappings
        
        # Apply the highest priority rule
        best_match = rule_matches[0]
        rule = best_match.rule
        
        # Create enhanced mapping
        enhanced_mapping = {
            'code': rule.target_code,
            'system': rule.target_system,
            'display': rule.target_display,
            'confidence': best_match.confidence,
            'source': 'custom_rule',
            'rule_id': rule.rule_id,
            'rule_type': rule.rule_type.value,
            'match_reason': best_match.match_reason,
            'metadata': rule.metadata
        }
        
        # Decide whether to replace or prepend
        if rule.rule_type == RuleType.MANUAL_OVERRIDE or rule.priority == RulePriority.CRITICAL:
            # Replace all base mappings
            return [enhanced_mapping]
        else:
            # Prepend to base mappings
            return [enhanced_mapping] + base_mappings
    
    def get_all_rules(self, include_inactive: bool = False) -> List[CustomMappingRule]:
        """Get all rules, optionally including inactive ones"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                query = "SELECT * FROM custom_mapping_rules"
                if not include_inactive:
                    query += " WHERE is_active = TRUE"
                query += " ORDER BY priority ASC, created_at ASC"
                
                cursor = conn.execute(query)
                return [CustomMappingRule.from_dict(dict(row)) for row in cursor]
                
        except Exception as e:
            logger.error(f"Error retrieving all rules: {e}")
            return []
    
    def validate_rule(self, rule: CustomMappingRule) -> Tuple[bool, List[str]]:
        """Validate a custom mapping rule"""
        errors = []
        
        # Basic validation
        if not rule.rule_id:
            errors.append("Rule ID is required")
        
        if not rule.source_term:
            errors.append("Source term is required")
        
        if not rule.target_code:
            errors.append("Target code is required")
        
        if not rule.target_system:
            errors.append("Target system is required")
        
        if not rule.target_display:
            errors.append("Target display is required")
        
        # Rule type specific validation
        if rule.rule_type == RuleType.PATTERN_MATCH:
            pattern = rule.conditions.get('pattern')
            if not pattern:
                errors.append("Pattern match rules require a 'pattern' condition")
            else:
                try:
                    import re
                    re.compile(pattern)
                except re.error as e:
                    errors.append(f"Invalid regex pattern: {e}")
        
        elif rule.rule_type == RuleType.CONTEXT_DEPENDENT:
            if not rule.conditions.get('required_context'):
                errors.append("Context dependent rules require 'required_context' conditions")
        
        elif rule.rule_type == RuleType.DOMAIN_SPECIFIC:
            if not rule.conditions.get('domain'):
                errors.append("Domain specific rules require a 'domain' condition")
        
        # Check for duplicate rule IDs
        existing_rule = self.get_rule(rule.rule_id)
        if existing_rule and existing_rule.rule_id != rule.rule_id:
            errors.append(f"Rule ID '{rule.rule_id}' already exists")
        
        return len(errors) == 0, errors
    
    def import_rules_from_json(self, json_file_path: str) -> Tuple[int, int, List[str]]:
        """Import rules from JSON file"""
        try:
            with open(json_file_path, 'r') as f:
                rules_data = json.load(f)
            
            successful = 0
            failed = 0
            errors = []
            
            for rule_data in rules_data:
                try:
                    rule = CustomMappingRule.from_dict(rule_data)
                    is_valid, validation_errors = self.validate_rule(rule)
                    
                    if is_valid:
                        if self.add_rule(rule):
                            successful += 1
                        else:
                            failed += 1
                            errors.append(f"Failed to add rule {rule.rule_id}")
                    else:
                        failed += 1
                        errors.extend([f"Rule {rule.rule_id}: {err}" for err in validation_errors])
                        
                except Exception as e:
                    failed += 1
                    errors.append(f"Error processing rule: {e}")
            
            return successful, failed, errors
            
        except Exception as e:
            logger.error(f"Error importing rules from JSON: {e}")
            return 0, 0, [str(e)]
    
    def export_rules_to_json(self, json_file_path: str, include_inactive: bool = False) -> bool:
        """Export rules to JSON file"""
        try:
            rules = self.get_all_rules(include_inactive)
            rules_data = [rule.to_dict() for rule in rules]
            
            with open(json_file_path, 'w') as f:
                json.dump(rules_data, f, indent=2, default=str)
            
            logger.info(f"Exported {len(rules)} rules to {json_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting rules to JSON: {e}")
            return False