"""Context-aware terminology mapper with clinical domain understanding."""

import logging
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from app.standards.terminology.mapper import TerminologyMapper
from app.standards.terminology.embedded_db import EmbeddedDatabaseManager

logger = logging.getLogger(__name__)


class ClinicalDomain(Enum):
    """Clinical domain classifications."""
    CARDIOLOGY = "cardiology"
    ONCOLOGY = "oncology"
    ENDOCRINOLOGY = "endocrinology"
    NEUROLOGY = "neurology"
    PULMONOLOGY = "pulmonology"
    GASTROENTEROLOGY = "gastroenterology"
    NEPHROLOGY = "nephrology"
    RHEUMATOLOGY = "rheumatology"
    INFECTIOUS_DISEASE = "infectious_disease"
    PSYCHIATRY = "psychiatry"
    LABORATORY = "laboratory"
    RADIOLOGY = "radiology"
    SURGERY = "surgery"
    EMERGENCY = "emergency"
    GENERAL = "general"


class ContextModifier(Enum):
    """Context modifiers for mapping."""
    NEGATION = "negation"
    UNCERTAINTY = "uncertainty"
    SEVERITY = "severity"
    TEMPORAL = "temporal"
    FAMILIAL = "familial"
    PAST_HISTORY = "past_history"
    CURRENT = "current"
    CHRONIC = "chronic"
    ACUTE = "acute"


@dataclass
class ClinicalContext:
    """Clinical context for term mapping."""
    domain: ClinicalDomain
    modifiers: List[ContextModifier]
    surrounding_text: str
    confidence: float
    semantic_context: Dict[str, Any]
    
    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class ContextAwareMapping:
    """Mapping result with context."""
    original_text: str
    found: bool
    system: Optional[str]
    code: Optional[str]
    display: Optional[str]
    confidence: float
    match_type: str
    clinical_context: ClinicalContext
    context_score: float
    semantic_score: float
    domain_relevance: float
    alternative_mappings: List[Dict[str, Any]]


class ContextAwareTerminologyMapper:
    """Terminology mapper with context awareness."""
    
    def __init__(self, base_mapper: TerminologyMapper = None, config: Dict[str, Any] = None):
        """
        Initialize context-aware mapper.
        
        Args:
            base_mapper: Base terminology mapper instance
            config: Configuration options
        """
        self.base_mapper = base_mapper or TerminologyMapper(config)
        self.config = config or {}
        
        # Initialize context patterns
        self._initialize_context_patterns()
        
        # Initialize domain-specific mappings
        self._initialize_domain_mappings()
        
        # Initialize semantic scoring
        self._initialize_semantic_scoring()
        
        logger.info("Context-aware terminology mapper initialized")
    
    def _initialize_context_patterns(self):
        """Initialize patterns for context detection."""
        # Negation patterns
        self.negation_patterns = [
            r'\b(?:no|not|without|absent|negative|denies?|rules?\s+out)\b',
            r'\b(?:never|none|nowhere|nothing|nobody)\b',
            r'\b(?:cannot|can\'t|won\'t|wouldn\'t|shouldn\'t)\b'
        ]
        
        # Uncertainty patterns
        self.uncertainty_patterns = [
            r'\b(?:possible|possibly|probable|probably|likely|unlikely)\b',
            r'\b(?:suspect|suspected|consider|considering|rule\s+out)\b',
            r'\b(?:may|might|could|would|should)\b',
            r'\b(?:appears?|seems?|suggests?|consistent\s+with)\b'
        ]
        
        # Temporal patterns
        self.temporal_patterns = {
            ContextModifier.PAST_HISTORY: [
                r'\b(?:history\s+of|h/o|hx\s+of|previous|prior|past)\b',
                r'\b(?:formerly|previously|once|used\s+to)\b'
            ],
            ContextModifier.CURRENT: [
                r'\b(?:current|currently|present|active|ongoing)\b',
                r'\b(?:now|today|recently|acute)\b'
            ],
            ContextModifier.CHRONIC: [
                r'\b(?:chronic|long-term|persistent|ongoing)\b',
                r'\b(?:lifelong|permanent|established)\b'
            ]
        }
        
        # Domain patterns
        self.domain_patterns = {
            ClinicalDomain.CARDIOLOGY: [
                r'\b(?:heart|cardiac|cardio|coronary|myocardial|pericardial)\b',
                r'\b(?:arrhythmia|tachycardia|bradycardia|fibrillation)\b',
                r'\b(?:ecg|ekg|echo|catheterization|angiogram)\b'
            ],
            ClinicalDomain.PULMONOLOGY: [
                r'\b(?:lung|pulmonary|respiratory|bronchial|alveolar)\b',
                r'\b(?:asthma|copd|pneumonia|bronchitis|emphysema)\b',
                r'\b(?:chest\s+x-ray|ct\s+chest|spirometry)\b'
            ],
            ClinicalDomain.LABORATORY: [
                r'\b(?:lab|laboratory|blood|serum|plasma|urine)\b',
                r'\b(?:glucose|cholesterol|hemoglobin|creatinine)\b',
                r'\b(?:test|level|result|value|measurement)\b'
            ],
            ClinicalDomain.ENDOCRINOLOGY: [
                r'\b(?:diabetes|diabetic|insulin|glucose|thyroid)\b',
                r'\b(?:hormone|endocrine|metabolic|adrenal)\b',
                r'\b(?:hba1c|tsh|t3|t4|cortisol)\b'
            ]
        }
    
    def _initialize_domain_mappings(self):
        """Initialize domain-specific mapping preferences."""
        self.domain_preferences = {
            ClinicalDomain.LABORATORY: {
                'preferred_systems': ['http://loinc.org'],
                'boost_factor': 1.2,
                'required_properties': ['component', 'property']
            },
            ClinicalDomain.CARDIOLOGY: {
                'preferred_systems': ['http://snomed.info/sct'],
                'boost_factor': 1.1,
                'domain_codes': ['disorder', 'procedure', 'finding']
            },
            ClinicalDomain.ENDOCRINOLOGY: {
                'preferred_systems': ['http://snomed.info/sct', 'http://loinc.org'],
                'boost_factor': 1.15,
                'domain_codes': ['disorder', 'substance', 'observable']
            }
        }
    
    def _initialize_semantic_scoring(self):
        """Initialize semantic similarity scoring."""
        # Semantic similarity weights
        self.semantic_weights = {
            'exact_match': 1.0,
            'synonym_match': 0.9,
            'hyponym_match': 0.8,
            'hypernym_match': 0.7,
            'related_match': 0.6,
            'context_boost': 0.2,
            'domain_boost': 0.15,
            'negation_penalty': -0.3,
            'uncertainty_penalty': -0.1
        }
    
    def map_with_context(self, term: str, context_text: str = "", 
                        domain_hint: ClinicalDomain = None) -> ContextAwareMapping:
        """
        Map a term with clinical context awareness.
        
        Args:
            term: The term to map
            context_text: Surrounding text for context
            domain_hint: Optional domain hint
            
        Returns:
            ContextAwareMapping with enhanced contextual information
        """
        try:
            logger.debug(f"Context-aware mapping for term: {term}")
            
            # Step 1: Detect clinical context
            clinical_context = self._detect_clinical_context(term, context_text, domain_hint)
            
            # Step 2: Get base mappings from all systems
            base_mappings = []
            
            # Try SNOMED first
            snomed_result = self.base_mapper.map_to_snomed(term, context_text)
            if snomed_result.get('found', False):
                base_mappings.append(snomed_result)
            
            # Try LOINC
            loinc_result = self.base_mapper.map_to_loinc(term, context_text)
            if loinc_result.get('found', False):
                base_mappings.append(loinc_result)
            
            # Try RxNorm
            rxnorm_result = self.base_mapper.map_to_rxnorm(term, context_text)
            if rxnorm_result.get('found', False):
                base_mappings.append(rxnorm_result)
            
            # Use the best mapping or create a fallback
            if base_mappings:
                # Sort by confidence and use the best one
                base_mapping = max(base_mappings, key=lambda x: x.get('confidence', 0))
            else:
                # No mapping found, create fallback
                base_mapping = {
                    'code': None,
                    'display': term,
                    'system': None,
                    'found': False,
                    'confidence': 0.0
                }
            
            # Step 3: Apply context-aware enhancements
            if base_mapping and base_mapping.get('found', False):
                enhanced_mapping = self._enhance_mapping_with_context(
                    base_mapping, clinical_context, term, context_text
                )
            else:
                # Try context-aware alternative mapping
                enhanced_mapping = self._context_aware_fallback_mapping(
                    term, clinical_context, context_text
                )
            
            # Step 4: Calculate contextual scores
            context_score = self._calculate_context_score(enhanced_mapping, clinical_context)
            semantic_score = self._calculate_semantic_score(enhanced_mapping, clinical_context)
            domain_relevance = self._calculate_domain_relevance(enhanced_mapping, clinical_context)
            
            # Step 5: Get alternative mappings
            alternatives = self._get_alternative_mappings(term, clinical_context, enhanced_mapping)
            
            # Add other base mappings as alternatives (exclude the primary one if found)
            for mapping in base_mappings:
                if mapping != base_mapping:
                    alternatives.append(mapping)
            
            # Step 6: Create context-aware mapping result
            result = ContextAwareMapping(
                original_text=term,
                found=enhanced_mapping.get('found', False),
                system=enhanced_mapping.get('system'),
                code=enhanced_mapping.get('code'),
                display=enhanced_mapping.get('display'),
                confidence=enhanced_mapping.get('confidence', 0.0),
                match_type=enhanced_mapping.get('match_type', 'no_match'),
                clinical_context=clinical_context,
                context_score=context_score,
                semantic_score=semantic_score,
                domain_relevance=domain_relevance,
                alternative_mappings=alternatives
            )
            
            logger.debug(f"Context-aware mapping completed: {result.found}")
            return result
            
        except Exception as e:
            logger.error(f"Error in context-aware mapping for '{term}': {str(e)}", exc_info=True)
            
            # Return fallback mapping
            return ContextAwareMapping(
                original_text=term,
                found=False,
                system=None,
                code=None,
                display=None,
                confidence=0.0,
                match_type='error',
                clinical_context=ClinicalContext(
                    domain=ClinicalDomain.GENERAL,
                    modifiers=[],
                    surrounding_text=context_text,
                    confidence=0.0,
                    semantic_context={}
                ),
                context_score=0.0,
                semantic_score=0.0,
                domain_relevance=0.0,
                alternative_mappings=[]
            )
    
    def _detect_clinical_context(self, term: str, context_text: str, 
                               domain_hint: ClinicalDomain = None) -> ClinicalContext:
        """
        Detect clinical context from term and surrounding text.
        
        Args:
            term: The term being mapped
            context_text: Surrounding context text
            domain_hint: Optional domain hint
            
        Returns:
            ClinicalContext object
        """
        full_text = f"{context_text} {term}".lower()
        
        # Detect modifiers
        modifiers = []
        
        # Check for negation
        for pattern in self.negation_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                modifiers.append(ContextModifier.NEGATION)
                break
        
        # Check for uncertainty
        for pattern in self.uncertainty_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                modifiers.append(ContextModifier.UNCERTAINTY)
                break
        
        # Check for temporal modifiers
        for modifier, patterns in self.temporal_patterns.items():
            for pattern in patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    modifiers.append(modifier)
                    break
        
        # Detect clinical domain
        detected_domain = domain_hint or self._detect_clinical_domain(full_text)
        
        # Calculate context confidence
        confidence = self._calculate_context_confidence(full_text, detected_domain, modifiers)
        
        # Extract semantic context
        semantic_context = self._extract_semantic_context(full_text, term)
        
        return ClinicalContext(
            domain=detected_domain,
            modifiers=modifiers,
            surrounding_text=context_text,
            confidence=confidence,
            semantic_context=semantic_context
        )
    
    def _detect_clinical_domain(self, text: str) -> ClinicalDomain:
        """
        Detect the most likely clinical domain from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Most likely ClinicalDomain
        """
        domain_scores = {}
        
        for domain, patterns in self.domain_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        
        return ClinicalDomain.GENERAL
    
    def _calculate_context_confidence(self, text: str, domain: ClinicalDomain, 
                                    modifiers: List[ContextModifier]) -> float:
        """
        Calculate confidence in context detection.
        
        Args:
            text: Analyzed text
            domain: Detected domain
            modifiers: Detected modifiers
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        base_confidence = 0.5
        
        # Boost for domain-specific terms
        if domain != ClinicalDomain.GENERAL:
            base_confidence += 0.2
        
        # Boost for clear modifiers
        if modifiers:
            base_confidence += min(0.2, len(modifiers) * 0.1)
        
        # Text length factor
        text_length_factor = min(1.0, len(text.split()) / 20.0)
        base_confidence += text_length_factor * 0.1
        
        return min(1.0, base_confidence)
    
    def _extract_semantic_context(self, text: str, term: str) -> Dict[str, Any]:
        """
        Extract semantic context information.
        
        Args:
            text: Full context text
            term: Target term
            
        Returns:
            Dictionary of semantic context features
        """
        return {
            'word_count': len(text.split()),
            'term_position': text.lower().find(term.lower()),
            'medical_terms_count': len(re.findall(r'\b\w+(?:ology|itis|osis|pathy|graphy|scopy)\b', text)),
            'numeric_values': len(re.findall(r'\b\d+(?:\.\d+)?\s*(?:mg|ml|cm|mm|%|units?)\b', text)),
            'has_dosage': bool(re.search(r'\b\d+\s*(?:mg|ml|units?)\b', text)),
            'has_measurement': bool(re.search(r'\b\d+(?:\.\d+)?\s*(?:cm|mm|inches?|feet)\b', text))
        }
    
    def _enhance_mapping_with_context(self, base_mapping: Dict[str, Any], 
                                    clinical_context: ClinicalContext,
                                    term: str, context_text: str) -> Dict[str, Any]:
        """
        Enhance base mapping with contextual information.
        
        Args:
            base_mapping: Base mapping result
            clinical_context: Detected clinical context
            term: Original term
            context_text: Context text
            
        Returns:
            Enhanced mapping dictionary
        """
        enhanced = dict(base_mapping)
        
        # Apply domain-specific enhancements
        if clinical_context.domain in self.domain_preferences:
            prefs = self.domain_preferences[clinical_context.domain]
            
            # Boost confidence for preferred systems
            if enhanced.get('system') in prefs.get('preferred_systems', []):
                enhanced['confidence'] = min(1.0, enhanced.get('confidence', 0.0) * prefs['boost_factor'])
                enhanced['match_type'] = f"domain_enhanced_{enhanced.get('match_type', 'unknown')}"
        
        # Apply modifier penalties/boosts
        for modifier in clinical_context.modifiers:
            if modifier == ContextModifier.NEGATION:
                enhanced['confidence'] *= 0.7  # Reduce confidence for negated terms
                enhanced['match_type'] = f"negated_{enhanced.get('match_type', 'unknown')}"
            elif modifier == ContextModifier.UNCERTAINTY:
                enhanced['confidence'] *= 0.9  # Slight reduction for uncertain terms
                enhanced['match_type'] = f"uncertain_{enhanced.get('match_type', 'unknown')}"
        
        return enhanced
    
    def _context_aware_fallback_mapping(self, term: str, clinical_context: ClinicalContext,
                                      context_text: str) -> Dict[str, Any]:
        """
        Attempt context-aware fallback mapping when base mapping fails.
        
        Args:
            term: Term to map
            clinical_context: Clinical context
            context_text: Context text
            
        Returns:
            Fallback mapping or empty result
        """
        # Try fuzzy matching with domain-specific preferences
        if clinical_context.domain in self.domain_preferences:
            prefs = self.domain_preferences[clinical_context.domain]
            
            # Use fuzzy matcher with domain preference
            if hasattr(self.base_mapper, 'fuzzy_matcher') and self.base_mapper.fuzzy_matcher:
                fuzzy_results = self.base_mapper.fuzzy_matcher.find_similar_terms(
                    term, limit=3, min_confidence=0.6
                )
                
                # Filter by preferred systems
                for result in fuzzy_results:
                    if result.get('system') in prefs.get('preferred_systems', []):
                        result['confidence'] *= prefs['boost_factor']
                        result['match_type'] = 'context_aware_fuzzy'
                        return result
                
                # Return best fuzzy match if available
                if fuzzy_results:
                    best_match = fuzzy_results[0]
                    best_match['match_type'] = 'fallback_fuzzy'
                    return best_match
        
        # Return no match
        return {
            'found': False,
            'system': None,
            'code': None,
            'display': None,
            'confidence': 0.0,
            'match_type': 'no_match'
        }
    
    def _calculate_context_score(self, mapping: Dict[str, Any], 
                               clinical_context: ClinicalContext) -> float:
        """Calculate context relevance score."""
        if not mapping.get('found', False):
            return 0.0
        
        score = 0.5  # Base score
        
        # Domain relevance boost
        if clinical_context.domain != ClinicalDomain.GENERAL:
            score += 0.2
        
        # Context confidence boost
        score += clinical_context.confidence * 0.2
        
        # Modifier penalties
        if ContextModifier.NEGATION in clinical_context.modifiers:
            score -= 0.3
        if ContextModifier.UNCERTAINTY in clinical_context.modifiers:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_semantic_score(self, mapping: Dict[str, Any], 
                                clinical_context: ClinicalContext) -> float:
        """Calculate semantic similarity score."""
        if not mapping.get('found', False):
            return 0.0
        
        # Base semantic score from match type
        match_type = mapping.get('match_type', 'unknown')
        if 'exact' in match_type:
            base_score = 1.0
        elif 'fuzzy' in match_type or 'partial' in match_type:
            base_score = 0.8
        elif 'synonym' in match_type:
            base_score = 0.9
        else:
            base_score = 0.6
        
        # Apply semantic context adjustments
        semantic_context = clinical_context.semantic_context
        if semantic_context.get('has_dosage') and 'drug' in match_type.lower():
            base_score += 0.1
        if semantic_context.get('has_measurement') and 'measurement' in match_type.lower():
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def _calculate_domain_relevance(self, mapping: Dict[str, Any], 
                                  clinical_context: ClinicalContext) -> float:
        """Calculate domain relevance score."""
        if not mapping.get('found', False):
            return 0.0
        
        system = mapping.get('system', '')
        domain = clinical_context.domain
        
        # Check domain preferences
        if domain in self.domain_preferences:
            prefs = self.domain_preferences[domain]
            if system in prefs.get('preferred_systems', []):
                return 0.9
        
        # Default relevance based on system
        if 'loinc.org' in system and domain == ClinicalDomain.LABORATORY:
            return 0.95
        elif 'snomed.info' in system and domain in [ClinicalDomain.CARDIOLOGY, ClinicalDomain.ENDOCRINOLOGY]:
            return 0.85
        elif 'rxnorm' in system and domain == ClinicalDomain.GENERAL:
            return 0.8
        
        return 0.5  # Default relevance
    
    def _get_alternative_mappings(self, term: str, clinical_context: ClinicalContext,
                                primary_mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get alternative mappings for the term.
        
        Args:
            term: Original term
            clinical_context: Clinical context
            primary_mapping: Primary mapping result
            
        Returns:
            List of alternative mappings
        """
        alternatives = []
        
        try:
            # Use fuzzy matcher to find alternatives
            if hasattr(self.base_mapper, 'fuzzy_matcher') and self.base_mapper.fuzzy_matcher:
                fuzzy_results = self.base_mapper.fuzzy_matcher.find_similar_terms(
                    term, limit=5, min_confidence=0.5
                )
                
                for result in fuzzy_results:
                    # Skip if same as primary mapping
                    if (primary_mapping.get('code') == result.get('code') and 
                        primary_mapping.get('system') == result.get('system')):
                        continue
                    
                    # Calculate context relevance for alternative
                    context_relevance = self._calculate_domain_relevance(result, clinical_context)
                    result['context_relevance'] = context_relevance
                    alternatives.append(result)
        
        except Exception as e:
            logger.warning(f"Error getting alternative mappings: {e}")
        
        # Sort by context relevance and confidence
        alternatives.sort(key=lambda x: (x.get('context_relevance', 0), x.get('confidence', 0)), reverse=True)
        
        return alternatives[:3]  # Return top 3 alternatives
    
    def batch_map_with_context(self, terms_with_context: List[Tuple[str, str]], 
                             domain_hint: ClinicalDomain = None) -> List[ContextAwareMapping]:
        """
        Map multiple terms with their contexts in batch.
        
        Args:
            terms_with_context: List of (term, context) tuples
            domain_hint: Optional domain hint for all terms
            
        Returns:
            List of ContextAwareMapping results
        """
        logger.info(f"Batch context-aware mapping for {len(terms_with_context)} terms")
        
        results = []
        for term, context in terms_with_context:
            try:
                result = self.map_with_context(term, context, domain_hint)
                results.append(result)
            except Exception as e:
                logger.error(f"Error mapping term '{term}': {e}")
                # Add error result
                results.append(ContextAwareMapping(
                    original_text=term,
                    found=False,
                    system=None,
                    code=None,
                    display=None,
                    confidence=0.0,
                    match_type='error',
                    clinical_context=ClinicalContext(
                        domain=ClinicalDomain.GENERAL,
                        modifiers=[],
                        surrounding_text=context,
                        confidence=0.0,
                        semantic_context={}
                    ),
                    context_score=0.0,
                    semantic_score=0.0,
                    domain_relevance=0.0,
                    alternative_mappings=[]
                ))
        
        logger.info(f"Completed batch context-aware mapping: {sum(1 for r in results if r.found)}/{len(results)} successful")
        return results
    
    def get_context_statistics(self, mappings: List[ContextAwareMapping]) -> Dict[str, Any]:
        """
        Get statistics about context-aware mappings.
        
        Args:
            mappings: List of ContextAwareMapping results
            
        Returns:
            Dictionary of statistics
        """
        if not mappings:
            return {}
        
        successful_mappings = [m for m in mappings if m.found]
        
        # Domain distribution
        domain_counts = {}
        for mapping in mappings:
            domain = mapping.clinical_context.domain.value
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Modifier distribution
        modifier_counts = {}
        for mapping in mappings:
            for modifier in mapping.clinical_context.modifiers:
                mod_name = modifier.value
                modifier_counts[mod_name] = modifier_counts.get(mod_name, 0) + 1
        
        # Score statistics
        context_scores = [m.context_score for m in successful_mappings]
        semantic_scores = [m.semantic_score for m in successful_mappings]
        domain_relevance_scores = [m.domain_relevance for m in successful_mappings]
        
        return {
            'total_mappings': len(mappings),
            'successful_mappings': len(successful_mappings),
            'success_rate': len(successful_mappings) / len(mappings) if mappings else 0,
            'domain_distribution': domain_counts,
            'modifier_distribution': modifier_counts,
            'average_context_score': sum(context_scores) / len(context_scores) if context_scores else 0,
            'average_semantic_score': sum(semantic_scores) / len(semantic_scores) if semantic_scores else 0,
            'average_domain_relevance': sum(domain_relevance_scores) / len(domain_relevance_scores) if domain_relevance_scores else 0,
            'has_alternatives': sum(1 for m in mappings if m.alternative_mappings),
        }