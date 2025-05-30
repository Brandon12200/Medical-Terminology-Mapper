"""
Enhanced Negation and Modifier Handler for Medical Terminology Mapper

This module provides advanced negation detection and clinical modifier handling
for medical text processing. Week 6 Implementation - Enhanced Negation and Modifier Handling.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class NegationScope(Enum):
    """Scope of negation detection"""
    SENTENCE = "sentence"
    PHRASE = "phrase"
    IMMEDIATE = "immediate"
    GLOBAL = "global"


class ModifierType(Enum):
    """Types of clinical modifiers"""
    NEGATION = "negation"
    UNCERTAINTY = "uncertainty"
    SEVERITY = "severity"
    TEMPORALITY = "temporality"
    FAMILY_HISTORY = "family_history"
    EXPERIENCER = "experiencer"
    CONDITIONALITY = "conditionality"


@dataclass
class ModifierMatch:
    """Represents a detected modifier"""
    modifier_type: ModifierType
    text: str
    start_pos: int
    end_pos: int
    confidence: float
    scope_start: int
    scope_end: int
    pattern_matched: str


@dataclass
class NegationResult:
    """Result of negation analysis"""
    is_negated: bool
    confidence: float
    negation_cue: Optional[str]
    negation_scope: Tuple[int, int]
    modifiers: List[ModifierMatch]


class EnhancedNegationHandler:
    """
    Advanced negation and modifier detection for clinical text.
    
    This handler uses sophisticated pattern matching and scope detection
    to identify negation, uncertainty, and other clinical modifiers.
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the negation handler with patterns and rules."""
        self.config = config or {}
        self._initialize_patterns()
        self._initialize_scope_rules()
        
    def _initialize_patterns(self):
        """Initialize patterns for negation and modifier detection."""
        
        # Enhanced negation patterns with context
        self.negation_patterns = {
            'explicit_negation': [
                r'\b(?:no|not|without|absent|negative|denies?|rules?\s+out)\b',
                r'\b(?:never|none|nowhere|nothing|nobody)\b',
                r'\b(?:cannot|can\'t|won\'t|wouldn\'t|shouldn\'t|couldn\'t)\b',
                r'\b(?:free\s+of|lack\s+of|absence\s+of|devoid\s+of)\b',
                r'\b(?:ruled?\s+out|r/o|rule\s+out|exclude[sd]?)\b'
            ],
            'implicit_negation': [
                r'\b(?:no\s+(?:evidence|signs?|symptoms?|indication)\s+of)\b',
                r'\b(?:no\s+(?:history|h/o)\s+of)\b',
                r'\b(?:unremarkable|normal|within\s+normal\s+limits|wnl)\b',
                r'\b(?:clear|cleared|resolution|resolved)\b'
            ],
            'conditional_negation': [
                r'\b(?:if\s+no|unless|except\s+for|other\s+than)\b',
                r'\b(?:rather\s+than|instead\s+of|as\s+opposed\s+to)\b'
            ]
        }
        
        # Uncertainty patterns
        self.uncertainty_patterns = {
            'epistemic': [
                r'\b(?:possible|possibly|probable|probably|likely|unlikely)\b',
                r'\b(?:suspect|suspected|consider|considering)\b',
                r'\b(?:may|might|could|would|should)\b',
                r'\b(?:appears?|seems?|suggests?|consistent\s+with)\b',
                r'\b(?:impression|differential|rule\s+out|r/o)\b'
            ],
            'hedging': [
                r'\b(?:somewhat|rather|fairly|quite|relatively)\b',
                r'\b(?:apparently|presumably|allegedly)\b',
                r'\b(?:tend\s+to|inclined\s+to)\b'
            ]
        }
        
        # Severity modifiers
        self.severity_patterns = {
            'mild': [
                r'\b(?:mild|slight|minor|minimal|trace)\b',
                r'\b(?:low-grade|low\s+grade)\b'
            ],
            'moderate': [
                r'\b(?:moderate|medium|intermediate)\b'
            ],
            'severe': [
                r'\b(?:severe|serious|major|significant|marked)\b',
                r'\b(?:acute|critical|extreme|intense)\b',
                r'\b(?:high-grade|high\s+grade)\b'
            ]
        }
        
        # Temporal modifiers
        self.temporal_patterns = {
            'past': [
                r'\b(?:history\s+of|h/o|hx\s+of|previous|prior|past)\b',
                r'\b(?:formerly|previously|once|used\s+to)\b',
                r'\b(?:years?\s+ago|months?\s+ago|days?\s+ago)\b'
            ],
            'current': [
                r'\b(?:current|currently|present|active|ongoing)\b',
                r'\b(?:now|today|recently|acute)\b'
            ],
            'chronic': [
                r'\b(?:chronic|long-term|persistent|ongoing)\b',
                r'\b(?:lifelong|permanent|established)\b'
            ],
            'intermittent': [
                r'\b(?:intermittent|occasional|episodic|sporadic)\b',
                r'\b(?:on\s+and\s+off|comes?\s+and\s+goes?)\b'
            ]
        }
        
        # Family history patterns
        self.family_history_patterns = [
            r'\b(?:family\s+history|fh|family\s+hx)\b',
            r'\b(?:mother|father|parent|sibling|brother|sister)\b',
            r'\b(?:maternal|paternal|grandmother|grandfather)\b',
            r'\b(?:runs?\s+in\s+the\s+family|familial)\b'
        ]
        
        # Experiencer patterns (who experiences the condition)
        self.experiencer_patterns = {
            'patient': [
                r'\b(?:patient|pt|he|she|they)\b',
                r'\b(?:this\s+(?:patient|person|individual))\b'
            ],
            'family': [
                r'\b(?:mother|father|parent|sibling|relative)\b',
                r'\b(?:family\s+member|grandmother|grandfather)\b'
            ],
            'other': [
                r'\b(?:someone|anyone|people|others)\b'
            ]
        }
        
        # Scope terminators - patterns that end negation scope
        self.scope_terminators = [
            r'\b(?:but|however|although|though|except|while)\b',
            r'\b(?:and|also|additionally|furthermore|moreover)\b',
            r'[.!?;]',  # Punctuation
            r'\n'  # New line
        ]
        
    def _initialize_scope_rules(self):
        """Initialize rules for determining modifier scope."""
        self.scope_rules = {
            'negation_scope': {
                'max_distance': 10,  # Maximum words after negation cue
                'punctuation_boundary': True,
                'conjunction_boundary': True
            },
            'uncertainty_scope': {
                'max_distance': 8,
                'punctuation_boundary': True,
                'conjunction_boundary': False
            },
            'severity_scope': {
                'max_distance': 3,  # Severity modifiers are usually close
                'punctuation_boundary': False,
                'conjunction_boundary': False
            }
        }
    
    def analyze_negation_and_modifiers(self, text: str, target_term: str,
                                     target_start: int, target_end: int) -> NegationResult:
        """
        Analyze text for negation and modifiers affecting the target term.
        
        Args:
            text: Full text to analyze
            target_term: The term to check for negation/modifiers
            target_start: Start position of target term
            target_end: End position of target term
            
        Returns:
            NegationResult with detected negation and modifiers
        """
        logger.debug(f"Analyzing negation for term: {target_term}")
        
        # Detect all modifiers first
        all_modifiers = self._detect_all_modifiers(text)
        
        # Filter modifiers that affect the target term
        relevant_modifiers = self._filter_modifiers_by_scope(
            all_modifiers, target_start, target_end, text
        )
        
        # Determine negation status
        negation_modifiers = [m for m in relevant_modifiers 
                            if m.modifier_type == ModifierType.NEGATION]
        
        if negation_modifiers:
            # Use the closest negation modifier
            closest_neg = min(negation_modifiers, 
                            key=lambda m: abs(m.start_pos - target_start))
            
            return NegationResult(
                is_negated=True,
                confidence=closest_neg.confidence,
                negation_cue=closest_neg.text,
                negation_scope=(closest_neg.scope_start, closest_neg.scope_end),
                modifiers=relevant_modifiers
            )
        else:
            return NegationResult(
                is_negated=False,
                confidence=1.0,
                negation_cue=None,
                negation_scope=(target_start, target_end),
                modifiers=relevant_modifiers
            )
    
    def _detect_all_modifiers(self, text: str) -> List[ModifierMatch]:
        """Detect all modifiers in the text."""
        modifiers = []
        
        # Detect negation
        modifiers.extend(self._detect_modifier_type(
            text, self.negation_patterns, ModifierType.NEGATION
        ))
        
        # Detect uncertainty
        modifiers.extend(self._detect_modifier_type(
            text, self.uncertainty_patterns, ModifierType.UNCERTAINTY
        ))
        
        # Detect severity
        modifiers.extend(self._detect_modifier_type(
            text, self.severity_patterns, ModifierType.SEVERITY
        ))
        
        # Detect temporal modifiers
        modifiers.extend(self._detect_modifier_type(
            text, self.temporal_patterns, ModifierType.TEMPORALITY
        ))
        
        # Detect family history
        modifiers.extend(self._detect_simple_modifiers(
            text, self.family_history_patterns, ModifierType.FAMILY_HISTORY
        ))
        
        return modifiers
    
    def _detect_modifier_type(self, text: str, pattern_dict: Dict[str, List[str]],
                            modifier_type: ModifierType) -> List[ModifierMatch]:
        """Detect modifiers of a specific type."""
        modifiers = []
        
        for subtype, patterns in pattern_dict.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    # Calculate scope for this modifier
                    scope_start, scope_end = self._calculate_modifier_scope(
                        text, match.start(), match.end(), modifier_type
                    )
                    
                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_modifier_confidence(
                        pattern, match.group(), modifier_type
                    )
                    
                    modifiers.append(ModifierMatch(
                        modifier_type=modifier_type,
                        text=match.group(),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=confidence,
                        scope_start=scope_start,
                        scope_end=scope_end,
                        pattern_matched=pattern
                    ))
        
        return modifiers
    
    def _detect_simple_modifiers(self, text: str, patterns: List[str],
                               modifier_type: ModifierType) -> List[ModifierMatch]:
        """Detect modifiers with simple pattern lists."""
        modifiers = []
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                scope_start, scope_end = self._calculate_modifier_scope(
                    text, match.start(), match.end(), modifier_type
                )
                
                confidence = self._calculate_modifier_confidence(
                    pattern, match.group(), modifier_type
                )
                
                modifiers.append(ModifierMatch(
                    modifier_type=modifier_type,
                    text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=confidence,
                    scope_start=scope_start,
                    scope_end=scope_end,
                    pattern_matched=pattern
                ))
        
        return modifiers
    
    def _calculate_modifier_scope(self, text: str, start_pos: int, end_pos: int,
                                modifier_type: ModifierType) -> Tuple[int, int]:
        """Calculate the scope of influence for a modifier."""
        
        # Get scope rules for this modifier type
        if modifier_type == ModifierType.NEGATION:
            rules = self.scope_rules['negation_scope']
        elif modifier_type == ModifierType.UNCERTAINTY:
            rules = self.scope_rules['uncertainty_scope']
        elif modifier_type == ModifierType.SEVERITY:
            rules = self.scope_rules['severity_scope']
        else:
            # Default scope rules
            rules = {'max_distance': 5, 'punctuation_boundary': True, 'conjunction_boundary': True}
        
        # Find scope end
        words_after = text[end_pos:].split()
        scope_end = end_pos
        word_count = 0
        
        for word in words_after:
            if word_count >= rules['max_distance']:
                break
                
            # Check for scope terminators
            if rules.get('punctuation_boundary', True):
                if re.search(r'[.!?;]', word):
                    break
            
            if rules.get('conjunction_boundary', True):
                if re.search(r'\b(?:but|however|although|though|except|while)\b', 
                           word, re.IGNORECASE):
                    break
            
            scope_end += len(word) + 1  # +1 for space
            word_count += 1
        
        # Scope typically extends from the modifier to the calculated end
        return start_pos, min(scope_end, len(text))
    
    def _calculate_modifier_confidence(self, pattern: str, matched_text: str,
                                     modifier_type: ModifierType) -> float:
        """Calculate confidence score for a modifier match."""
        base_confidence = 0.8
        
        # Boost confidence for explicit patterns
        if modifier_type == ModifierType.NEGATION:
            if any(explicit in pattern for explicit in ['no', 'not', 'without', 'absent']):
                base_confidence = 0.95
            elif 'rule' in pattern or 'exclude' in pattern:
                base_confidence = 0.9
        
        elif modifier_type == ModifierType.UNCERTAINTY:
            if any(uncertain in pattern for uncertain in ['possible', 'probable', 'likely']):
                base_confidence = 0.9
            elif 'may' in pattern or 'might' in pattern:
                base_confidence = 0.85
        
        # Adjust for matched text length (longer matches often more reliable)
        if len(matched_text.split()) > 1:
            base_confidence += 0.05
        
        return min(1.0, base_confidence)
    
    def _filter_modifiers_by_scope(self, modifiers: List[ModifierMatch],
                                 target_start: int, target_end: int,
                                 text: str) -> List[ModifierMatch]:
        """Filter modifiers that affect the target term based on scope."""
        relevant_modifiers = []
        
        for modifier in modifiers:
            # Check if target term is within modifier scope
            if (modifier.scope_start <= target_start <= modifier.scope_end or
                modifier.scope_start <= target_end <= modifier.scope_end or
                (target_start <= modifier.scope_start and target_end >= modifier.scope_end)):
                
                # Additional contextual checks
                if self._is_modifier_contextually_relevant(modifier, target_start, target_end, text):
                    relevant_modifiers.append(modifier)
        
        return relevant_modifiers
    
    def _is_modifier_contextually_relevant(self, modifier: ModifierMatch,
                                         target_start: int, target_end: int,
                                         text: str) -> bool:
        """Check if a modifier is contextually relevant to the target term."""
        
        # Get text between modifier and target
        if modifier.end_pos < target_start:
            between_text = text[modifier.end_pos:target_start]
        elif target_end < modifier.start_pos:
            between_text = text[target_end:modifier.start_pos]
        else:
            # Overlapping or adjacent
            return True
        
        # Check for scope breakers
        scope_breakers = [
            r'\b(?:but|however|although|though|except|while)\b',
            r'[.!?]',
            r'\n\s*\n'  # Paragraph break
        ]
        
        for breaker in scope_breakers:
            if re.search(breaker, between_text, re.IGNORECASE):
                return False
        
        return True
    
    def get_negation_summary(self, negation_result: NegationResult) -> Dict[str, any]:
        """Get a summary of negation analysis results."""
        return {
            'is_negated': negation_result.is_negated,
            'confidence': negation_result.confidence,
            'negation_cue': negation_result.negation_cue,
            'modifiers_detected': len(negation_result.modifiers),
            'modifier_types': list(set(m.modifier_type.value for m in negation_result.modifiers)),
            'has_uncertainty': any(m.modifier_type == ModifierType.UNCERTAINTY 
                                 for m in negation_result.modifiers),
            'has_temporal': any(m.modifier_type == ModifierType.TEMPORALITY 
                              for m in negation_result.modifiers),
            'has_severity': any(m.modifier_type == ModifierType.SEVERITY 
                              for m in negation_result.modifiers),
            'is_family_history': any(m.modifier_type == ModifierType.FAMILY_HISTORY 
                                   for m in negation_result.modifiers)
        }


def test_negation_handler():
    """Test the negation handler with sample clinical text."""
    handler = EnhancedNegationHandler()
    
    test_cases = [
        ("Patient has no history of diabetes", "diabetes", 25, 33),
        ("No evidence of myocardial infarction", "myocardial infarction", 15, 35),
        ("Patient denies chest pain", "chest pain", 15, 25),
        ("Possible pneumonia", "pneumonia", 9, 18),
        ("Severe hypertension", "hypertension", 7, 19),
        ("Family history of cancer", "cancer", 18, 24),
        ("Chronic kidney disease", "kidney disease", 8, 21)
    ]
    
    for text, term, start, end in test_cases:
        result = handler.analyze_negation_and_modifiers(text, term, start, end)
        summary = handler.get_negation_summary(result)
        
        print(f"\nText: '{text}'")
        print(f"Term: '{term}'")
        print(f"Negated: {summary['is_negated']}")
        print(f"Modifiers: {summary['modifier_types']}")


if __name__ == "__main__":
    test_negation_handler()