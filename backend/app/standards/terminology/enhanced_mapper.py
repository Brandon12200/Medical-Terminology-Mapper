"""Enhanced terminology mapper with advanced features."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from .context_aware_mapper import ContextAwareTerminologyMapper, ClinicalDomain, ContextAwareMapping
from .custom_mapping_rules import CustomMappingRulesEngine, CustomMappingRule, RuleType, RulePriority
from .negation_handler import EnhancedNegationHandler, NegationResult, ModifierType
from .performance_optimizer import PerformanceOptimizer, performance_monitor
from .mapper import TerminologyMapper

logger = logging.getLogger(__name__)

@dataclass
class EnhancedMappingResult:
    """Mapping result with context and rule info."""
    term: str
    mappings: List[Dict[str, Any]]
    context_info: Optional[Dict[str, Any]] = None
    applied_rules: List[Dict[str, Any]] = None
    domain: Optional[ClinicalDomain] = None
    confidence_scores: List[float] = None
    negation_info: Optional[Dict[str, Any]] = None
    processing_metadata: Dict[str, Any] = None
    performance_metrics: Dict[str, Any] = None

class EnhancedTerminologyMapper:
    """Enhanced mapper with advanced features."""
    
    def __init__(self, 
                 terminology_db_path: str = "data/terminology",
                 custom_rules_db_path: str = "data/terminology/custom_rules.sqlite",
                 config: Dict[str, Any] = None):
        """Initialize the enhanced mapper with all Week 6 features
        
        Args:
            terminology_db_path: Path to terminology databases
            custom_rules_db_path: Path to custom rules database
            config: Configuration options
        """
        self.config = config or {}
        
        # Initialize component mappers
        self.base_mapper = TerminologyMapper({"data_dir": terminology_db_path})
        self.context_mapper = ContextAwareTerminologyMapper(
            base_mapper=self.base_mapper,
            config={"data_dir": terminology_db_path}
        )
        self.rules_engine = CustomMappingRulesEngine(custom_rules_db_path)
        
        # Initialize Week 6 advanced features
        self.negation_handler = EnhancedNegationHandler(self.config.get('negation', {}))
        self.performance_optimizer = PerformanceOptimizer(self.config.get('performance', {}))
        
        # Processing statistics
        self.processing_stats = {
            'total_terms_processed': 0,
            'negated_terms': 0,
            'rule_overrides_applied': 0,
            'context_enhanced_mappings': 0,
            'performance_optimizations_used': 0
        }
        
        logger.info("Enhanced terminology mapper initialized")
    
    def map_term(self, term: str, terminology_system: str = "all", 
                 fuzzy_threshold: float = 0.0, max_results: int = 10,
                 context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Map term with legacy interface."""
        result = self.map_term_enhanced(
            term=term,
            context_text=context or "",
            use_performance_optimization=True,
            detect_negation=True
        )
        
        # Filter by system if specified
        if terminology_system and terminology_system != "all":
            filtered_mappings = [
                m for m in result.mappings 
                if m.get("system", "").lower() == terminology_system.lower()
            ]
        else:
            filtered_mappings = result.mappings
            
        # Apply fuzzy threshold
        if fuzzy_threshold > 0:
            filtered_mappings = [
                m for m in filtered_mappings 
                if m.get("confidence", 0) >= fuzzy_threshold
            ]
            
        # Limit results
        return filtered_mappings[:max_results]
    
    @performance_monitor
    def map_term_enhanced(self, 
                         term: str, 
                         context_text: str = "",
                         domain_hint: Optional[ClinicalDomain] = None,
                         use_performance_optimization: bool = True,
                         detect_negation: bool = True) -> EnhancedMappingResult:
        """
        Map a term using all enhanced features from Week 6.
        
        Args:
            term: The term to map
            context_text: Surrounding context text
            domain_hint: Optional clinical domain hint
            use_performance_optimization: Whether to use performance optimizations
            detect_negation: Whether to detect negation and modifiers
            
        Returns:
            EnhancedMappingResult with comprehensive mapping information
        """
        start_time = datetime.now()
        self.processing_stats['total_terms_processed'] += 1
        
        try:
            # Step 1: Context-aware mapping
            context_mapping = self.context_mapper.map_with_context(
                term, context_text, domain_hint
            )
            
            # Step 2: Detect negation and modifiers if requested
            negation_info = None
            if detect_negation and context_text:
                # Find term position in context
                term_start = context_text.lower().find(term.lower())
                if term_start >= 0:
                    term_end = term_start + len(term)
                    negation_result = self.negation_handler.analyze_negation_and_modifiers(
                        context_text, term, term_start, term_end
                    )
                    negation_info = self.negation_handler.get_negation_summary(negation_result)
                    
                    if negation_result.is_negated:
                        self.processing_stats['negated_terms'] += 1
            
            # Step 3: Prepare base mappings from context-aware mapping
            base_mappings = []
            if context_mapping.found:
                base_mappings.append({
                    'code': context_mapping.code,
                    'system': context_mapping.system,
                    'display': context_mapping.display,
                    'confidence': context_mapping.confidence,
                    'source': 'context_aware',
                    'match_type': context_mapping.match_type
                })
            
            # Add alternative mappings
            base_mappings.extend(context_mapping.alternative_mappings)
            
            # Step 4: Apply custom mapping rules
            clinical_context = {
                'domain': context_mapping.clinical_context.domain.value,
                'modifiers': [m.value for m in context_mapping.clinical_context.modifiers],
                'negated': negation_info.get('is_negated', False) if negation_info else False,
                'confidence': context_mapping.clinical_context.confidence
            }
            
            enhanced_mappings = self.rules_engine.apply_rules(
                term, base_mappings, clinical_context
            )
            
            # Track rule applications
            applied_rules = []
            for mapping in enhanced_mappings:
                if mapping.get('source') == 'custom_rule':
                    applied_rules.append({
                        'rule_id': mapping.get('rule_id'),
                        'rule_type': mapping.get('rule_type'),
                        'match_reason': mapping.get('match_reason'),
                        'confidence': mapping.get('confidence', 1.0)
                    })
                    self.processing_stats['rule_overrides_applied'] += 1
            
            # Step 5: Apply negation adjustments to final mappings
            if negation_info and negation_info.get('is_negated'):
                for mapping in enhanced_mappings:
                    # Reduce confidence for negated terms
                    if 'confidence' in mapping:
                        mapping['confidence'] *= 0.3
                    mapping['negated'] = True
                    mapping['negation_cue'] = negation_info.get('negation_cue')
            
            # Step 6: Calculate final confidence scores
            confidence_scores = [m.get('confidence', 0.0) for m in enhanced_mappings]
            
            # Step 7: Prepare processing metadata
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_metadata = {
                'processing_time_ms': processing_time * 1000,
                'context_detected_domain': context_mapping.clinical_context.domain.value,
                'context_confidence': context_mapping.context_score,
                'semantic_score': context_mapping.semantic_score,
                'domain_relevance': context_mapping.domain_relevance,
                'total_mappings_found': len(enhanced_mappings),
                'rules_applied': len(applied_rules),
                'negation_detected': negation_info.get('is_negated', False) if negation_info else False
            }
            
            # Step 8: Performance metrics
            performance_metrics = {}
            if use_performance_optimization:
                self.processing_stats['performance_optimizations_used'] += 1
                performance_metrics = {
                    'cache_used': True,
                    'parallel_processing': False,
                    'optimization_level': 'single_term'
                }
            
            self.processing_stats['context_enhanced_mappings'] += 1
            
            return EnhancedMappingResult(
                term=term,
                mappings=enhanced_mappings,
                context_info={
                    'domain': context_mapping.clinical_context.domain,
                    'modifiers': context_mapping.clinical_context.modifiers,
                    'surrounding_text': context_text,
                    'confidence': context_mapping.clinical_context.confidence
                },
                applied_rules=applied_rules,
                domain=context_mapping.clinical_context.domain,
                confidence_scores=confidence_scores,
                negation_info=negation_info,
                processing_metadata=processing_metadata,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            logger.error(f"Error in enhanced mapping for term '{term}': {e}")
            
            # Return error result
            return EnhancedMappingResult(
                term=term,
                mappings=[],
                context_info={'error': str(e)},
                applied_rules=[],
                domain=ClinicalDomain.GENERAL,
                confidence_scores=[],
                negation_info={'error': str(e)},
                processing_metadata={'error': str(e), 'processing_time_ms': 0},
                performance_metrics={'error': True}
            )
    
    def map_terms_batch_enhanced(self, 
                               terms_with_context: List[Tuple[str, str]],
                               domain_hint: Optional[ClinicalDomain] = None,
                               use_parallel: bool = True,
                               detect_negation: bool = True) -> List[EnhancedMappingResult]:
        """
        Map multiple terms with enhanced features and performance optimization.
        
        Args:
            terms_with_context: List of (term, context) tuples
            domain_hint: Optional domain hint for all terms
            use_parallel: Whether to use parallel processing
            detect_negation: Whether to detect negation and modifiers
            
        Returns:
            List of EnhancedMappingResult objects
        """
        start_time = datetime.now()
        
        if use_parallel and len(terms_with_context) > 5:
            # Use performance optimizer for batch processing
            def mapping_function(term_context_tuple):
                term, context = term_context_tuple
                return self.map_term_enhanced(
                    term, context, domain_hint, 
                    use_performance_optimization=True,
                    detect_negation=detect_negation
                )
            
            results = self.performance_optimizer.optimize_terminology_mapping(
                terms_with_context,
                mapping_function,
                use_parallel=True,
                use_cache=True
            )
            
            self.processing_stats['performance_optimizations_used'] += 1
        else:
            # Sequential processing for small batches
            results = []
            for term, context in terms_with_context:
                result = self.map_term_enhanced(
                    term, context, domain_hint,
                    use_performance_optimization=False,
                    detect_negation=detect_negation
                )
                results.append(result)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Batch enhanced mapping completed: {len(terms_with_context)} terms "
                   f"in {processing_time:.2f}s ({len(terms_with_context)/processing_time:.1f} terms/sec)")
        
        return results
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        performance_report = self.performance_optimizer.get_performance_report()
        
        return {
            'processing_stats': self.processing_stats,
            'performance_optimizer': performance_report,
            'rules_engine_stats': {
                'total_rules': len(self.rules_engine.get_all_rules()),
                'active_rules': len(self.rules_engine.get_all_rules(include_inactive=False))
            },
            'cache_stats': self.performance_optimizer.advanced_cache.get_cache_stats()
        }
    
    def optimize_performance(self):
        """Run performance optimization routines."""
        # Clear expired cache entries
        self.performance_optimizer.advanced_cache.clear_expired_entries()
        
        # Term cache optimization removed with extractors
        
        # Refresh rules cache
        self.rules_engine._load_rules_cache()
        
        logger.info("Performance optimization completed")
    
    def cleanup(self):
        """Clean up resources and connections."""
        self.performance_optimizer.cleanup()
        logger.info("Enhanced terminology mapper cleanup completed")
    
    def map_term_basic(self, 
                      term: str, 
                      context_text: str = "", 
                      domain_hint: Optional[ClinicalDomain] = None,
                      apply_custom_rules: bool = True) -> EnhancedMappingResult:
        """Enhanced term mapping with context awareness and custom rules
        
        Args:
            term: Medical term to map
            context_text: Clinical context surrounding the term
            domain_hint: Hint about the clinical domain
            apply_custom_rules: Whether to apply custom mapping rules
            
        Returns:
            EnhancedMappingResult with comprehensive mapping information
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Get context-aware mapping
            context_mapping = self.context_mapper.map_with_context(
                term, context_text, domain_hint
            )
            
            # Step 2: Convert to base format for rule processing
            base_mappings = []
            
            # Add primary mapping if found
            if context_mapping.found:
                base_mappings.append({
                    'code': context_mapping.code,
                    'system': context_mapping.system,
                    'display': context_mapping.display,
                    'confidence': context_mapping.confidence,
                    'source': 'context_aware'
                })
            
            # Add alternative mappings
            for alt_mapping in context_mapping.alternative_mappings:
                base_mappings.append({
                    'code': alt_mapping.get('code', ''),
                    'system': alt_mapping.get('system', ''),
                    'display': alt_mapping.get('display', ''),
                    'confidence': alt_mapping.get('confidence', 0.0),
                    'source': alt_mapping.get('source', 'context_aware')
                })
            
            # Step 3: Apply custom rules if enabled
            applied_rules = []
            if apply_custom_rules:
                # Prepare context for rule matching
                rule_context = {
                    'domain': context_mapping.clinical_context.domain.value if context_mapping.clinical_context.domain else None,
                    'modifiers': [mod.value for mod in context_mapping.clinical_context.modifiers],
                    'semantic_context': context_mapping.clinical_context.semantic_context,
                    'confidence': context_mapping.confidence
                }
                
                # Apply rules
                enhanced_mappings = self.rules_engine.apply_rules(
                    term, base_mappings, rule_context
                )
                
                # Track which rules were applied
                for mapping in enhanced_mappings:
                    if mapping.get('source') == 'custom_rule':
                        applied_rules.append({
                            'rule_id': mapping.get('rule_id'),
                            'rule_type': mapping.get('rule_type'),
                            'match_reason': mapping.get('match_reason'),
                            'confidence': mapping.get('confidence', 1.0)
                        })
                
                final_mappings = enhanced_mappings
            else:
                final_mappings = base_mappings
            
            # Step 4: Calculate confidence scores
            confidence_scores = [mapping.get('confidence', 0.0) for mapping in final_mappings]
            
            # Step 5: Prepare processing metadata
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_metadata = {
                'processing_time_seconds': processing_time,
                'context_aware_enabled': True,
                'custom_rules_enabled': apply_custom_rules,
                'rules_applied_count': len(applied_rules),
                'base_mappings_count': len(base_mappings),
                'final_mappings_count': len(final_mappings),
                'timestamp': datetime.now().isoformat()
            }
            
            return EnhancedMappingResult(
                term=term,
                mappings=final_mappings,
                context_info={
                    'clinical_context': context_mapping.clinical_context.__dict__ if context_mapping.clinical_context else None,
                    'context_text': context_text,
                    'domain_hint': domain_hint.value if domain_hint else None
                },
                applied_rules=applied_rules,
                domain=context_mapping.clinical_context.domain if context_mapping.clinical_context else None,
                confidence_scores=confidence_scores,
                processing_metadata=processing_metadata
            )
            
        except Exception as e:
            logger.error(f"Error in enhanced term mapping: {e}")
            # Fallback to base mapping
            base_result = self.base_mapper.map_term(term)
            return EnhancedMappingResult(
                term=term,
                mappings=base_result if isinstance(base_result, list) else [base_result],
                processing_metadata={
                    'error': str(e),
                    'fallback_used': True,
                    'timestamp': datetime.now().isoformat()
                }
            )
    
    def batch_map_terms(self, 
                       terms_with_context: List[Tuple[str, str]], 
                       domain_hint: Optional[ClinicalDomain] = None,
                       apply_custom_rules: bool = True) -> List[EnhancedMappingResult]:
        """Batch mapping of terms with context
        
        Args:
            terms_with_context: List of (term, context_text) tuples
            domain_hint: Hint about the clinical domain
            apply_custom_rules: Whether to apply custom mapping rules
            
        Returns:
            List of EnhancedMappingResult objects
        """
        results = []
        
        for term, context in terms_with_context:
            result = self.map_term_enhanced(
                term, context, domain_hint, apply_custom_rules
            )
            results.append(result)
        
        return results
    
    def add_custom_rule(self, 
                       rule_id: str,
                       source_term: str, 
                       target_code: str,
                       target_system: str,
                       target_display: str,
                       rule_type: RuleType = RuleType.EXACT_MATCH,
                       priority: RulePriority = RulePriority.MEDIUM,
                       conditions: Dict[str, Any] = None,
                       metadata: Dict[str, Any] = None,
                       created_by: str = "system") -> bool:
        """Add a custom mapping rule
        
        Args:
            rule_id: Unique identifier for the rule
            source_term: Source medical term
            target_code: Target terminology code
            target_system: Target terminology system
            target_display: Display name for target
            rule_type: Type of rule (exact_match, pattern_match, etc.)
            priority: Rule priority level
            conditions: Additional conditions for rule matching
            metadata: Additional metadata
            created_by: Rule creator identifier
            
        Returns:
            True if rule was added successfully
        """
        conditions = conditions or {}
        metadata = metadata or {}
        
        rule = CustomMappingRule(
            rule_id=rule_id,
            rule_type=rule_type,
            priority=priority,
            source_term=source_term,
            target_code=target_code,
            target_system=target_system,
            target_display=target_display,
            conditions=conditions,
            metadata=metadata,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=created_by
        )
        
        return self.rules_engine.add_rule(rule)
    
    def get_mapping_statistics(self, results: List[EnhancedMappingResult]) -> Dict[str, Any]:
        """Generate statistics from mapping results
        
        Args:
            results: List of mapping results
            
        Returns:
            Dictionary with mapping statistics
        """
        if not results:
            return {}
        
        total_terms = len(results)
        total_mappings = sum(len(r.mappings) for r in results)
        
        # Context statistics
        domains_found = {}
        for result in results:
            if result.domain:
                domain_name = result.domain.value
                domains_found[domain_name] = domains_found.get(domain_name, 0) + 1
        
        # Rules statistics
        rules_applied = {}
        total_rules_applied = 0
        for result in results:
            if result.applied_rules:
                total_rules_applied += len(result.applied_rules)
                for rule in result.applied_rules:
                    rule_type = rule.get('rule_type', 'unknown')
                    rules_applied[rule_type] = rules_applied.get(rule_type, 0) + 1
        
        # Confidence statistics
        all_confidences = []
        for result in results:
            if result.confidence_scores:
                all_confidences.extend(result.confidence_scores)
        
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
        # Processing time statistics
        processing_times = []
        for result in results:
            if result.processing_metadata and 'processing_time_seconds' in result.processing_metadata:
                processing_times.append(result.processing_metadata['processing_time_seconds'])
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            'total_terms': total_terms,
            'total_mappings': total_mappings,
            'avg_mappings_per_term': total_mappings / total_terms if total_terms > 0 else 0,
            'domains_detected': domains_found,
            'rules_applied': rules_applied,
            'total_rules_applied': total_rules_applied,
            'avg_confidence': round(avg_confidence, 3),
            'avg_processing_time_seconds': round(avg_processing_time, 4),
            'confidence_distribution': {
                'high': len([c for c in all_confidences if c >= 0.8]),
                'medium': len([c for c in all_confidences if 0.5 <= c < 0.8]),
                'low': len([c for c in all_confidences if c < 0.5])
            }
        }
    
    def export_custom_rules(self, file_path: str) -> bool:
        """Export custom rules to JSON file"""
        return self.rules_engine.export_rules_to_json(file_path)
    
    def import_custom_rules(self, file_path: str) -> Tuple[int, int, List[str]]:
        """Import custom rules from JSON file"""
        return self.rules_engine.import_rules_from_json(file_path)
    
    def get_custom_rules(self) -> List[CustomMappingRule]:
        """Get all active custom rules"""
        return self.rules_engine.get_all_rules()
    
    def validate_term_mapping(self, term: str, expected_code: str, expected_system: str) -> Dict[str, Any]:
        """Validate that a term maps to expected code/system
        
        Args:
            term: Medical term to validate
            expected_code: Expected terminology code
            expected_system: Expected terminology system
            
        Returns:
            Validation result with details
        """
        result = self.map_term_enhanced(term)
        
        validation = {
            'term': term,
            'expected_code': expected_code,
            'expected_system': expected_system,
            'found_mappings': len(result.mappings),
            'exact_match_found': False,
            'best_match': None,
            'all_matches': []
        }
        
        for mapping in result.mappings:
            match_info = {
                'code': mapping.get('code'),
                'system': mapping.get('system'),
                'display': mapping.get('display'),
                'confidence': mapping.get('confidence'),
                'exact_match': (mapping.get('code') == expected_code and 
                              mapping.get('system') == expected_system)
            }
            
            validation['all_matches'].append(match_info)
            
            if match_info['exact_match']:
                validation['exact_match_found'] = True
                validation['best_match'] = match_info
        
        if not validation['exact_match_found'] and validation['all_matches']:
            # Find best match by confidence
            validation['best_match'] = max(validation['all_matches'], 
                                         key=lambda x: x.get('confidence', 0))
        
        return validation