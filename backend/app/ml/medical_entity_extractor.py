"""
Medical Entity Extractor with multi-model support and advanced NER capabilities.
"""
import re
import torch
import torch.nn as nn
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np
from transformers import (
    AutoTokenizer, 
    AutoModelForTokenClassification,
    pipeline
)
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Comprehensive medical entity types."""
    CONDITION = "CONDITION"
    DRUG = "DRUG"
    PROCEDURE = "PROCEDURE"
    TEST = "TEST"
    ANATOMY = "ANATOMY"
    DOSAGE = "DOSAGE"
    FREQUENCY = "FREQUENCY"
    OBSERVATION = "OBSERVATION"
    
    @classmethod
    def from_string(cls, value: str) -> Optional['EntityType']:
        """Convert string to EntityType."""
        value = value.upper()
        # Handle aliases
        aliases = {
            "MEDICATION": cls.DRUG,
            "LAB_TEST": cls.TEST,
            "LAB": cls.TEST,
            "MEDICINE": cls.DRUG,
            "DISEASE": cls.CONDITION,
            "DISORDER": cls.CONDITION,
            "SYMPTOM": cls.CONDITION,
            "BODY_PART": cls.ANATOMY,
            "ORGAN": cls.ANATOMY,
        }
        
        if value in aliases:
            return aliases[value]
        
        try:
            return cls(value)
        except ValueError:
            return None


@dataclass
class MedicalEntity:
    """Represents a medical entity with all metadata."""
    text: str
    type: EntityType
    start: int
    end: int
    confidence: float
    raw_confidence: float  # Before calibration
    context: Optional[str] = None
    negated: bool = False
    uncertain: bool = False
    linked_id: Optional[str] = None  # For entity linking
    hierarchy: Optional[List[str]] = None  # For hierarchical recognition
    source_model: Optional[str] = None


class ConfidenceCalibrator:
    """Calibrates confidence scores using temperature scaling."""
    
    def __init__(self, temperature: float = 1.5):
        self.temperature = temperature
        
    def calibrate(self, logits: torch.Tensor) -> torch.Tensor:
        """Apply temperature scaling to logits."""
        return logits / self.temperature
        
    def calibrate_scores(self, scores: List[float]) -> List[float]:
        """Calibrate a list of confidence scores."""
        # Convert to logits, apply temperature, convert back
        scores_tensor = torch.tensor(scores)
        logits = torch.log(scores_tensor / (1 - scores_tensor + 1e-8))
        calibrated_logits = self.calibrate(logits)
        calibrated_scores = torch.sigmoid(calibrated_logits)
        return calibrated_scores.tolist()


class CRFLayer(nn.Module):
    """Conditional Random Field layer for sequence labeling."""
    
    def __init__(self, num_tags: int):
        super().__init__()
        self.num_tags = num_tags
        self.transitions = nn.Parameter(torch.randn(num_tags, num_tags))
        self.start_transitions = nn.Parameter(torch.randn(num_tags))
        self.end_transitions = nn.Parameter(torch.randn(num_tags))
        
    def forward(self, emissions: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """Forward pass of CRF layer."""
        return self._viterbi_decode(emissions, mask)
        
    def _viterbi_decode(self, emissions: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """Viterbi algorithm for finding most likely sequence."""
        batch_size, seq_len, num_tags = emissions.shape
        
        # Initialize
        scores = self.start_transitions + emissions[:, 0]
        paths = []
        
        # Forward pass
        for i in range(1, seq_len):
            scores_with_trans = scores.unsqueeze(2) + self.transitions
            scores, indices = scores_with_trans.max(dim=1)
            scores = scores + emissions[:, i]
            paths.append(indices)
            
        # Termination
        scores = scores + self.end_transitions
        best_scores, best_tags = scores.max(dim=1)
        
        # Backtrack
        best_paths = [best_tags]
        for indices in reversed(paths):
            best_tags = indices.gather(1, best_tags.unsqueeze(1)).squeeze(1)
            best_paths.append(best_tags)
            
        best_paths.reverse()
        return torch.stack(best_paths, dim=1)


class NegationDetector:
    """Detects negation in medical text."""
    
    def __init__(self):
        self.negation_patterns = [
            r'\bno\s+(?:evidence|signs?|symptoms?|history)\s+of\b',
            r'\bdenies?\b',
            r'\bnegative\s+for\b',
            r'\brule\s+out\b',
            r'\bwithout\b',
            r'\babsent\b',
            r'\bnot\s+(?:seen|observed|found|present)\b',
            r'\bno\s+\w+\s+(?:seen|observed|found|present)\b',
        ]
        self.negation_window = 5  # words
        
    def is_negated(self, entity: MedicalEntity, text: str) -> bool:
        """Check if entity is negated based on context."""
        # Get surrounding context
        start_context = max(0, entity.start - 50)
        end_context = min(len(text), entity.end + 50)
        context = text[start_context:end_context].lower()
        
        # Check for negation patterns
        for pattern in self.negation_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                # Check if negation is near the entity
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    neg_pos = match.start() + start_context
                    if abs(neg_pos - entity.start) < 50:  # Within 50 chars
                        return True
        return False


class UncertaintyDetector:
    """Detects uncertainty in medical text."""
    
    def __init__(self):
        self.uncertainty_patterns = [
            r'\b(?:possible|possibly|probable|probably)\b',
            r'\b(?:suspected|suspect)\b',
            r'\b(?:suggestive|suggests?)\s+of\b',
            r'\b(?:consistent|compatible)\s+with\b',
            r'\b(?:likely|unlikely)\b',
            r'\b(?:may|might|could)\s+(?:be|have|represent)\b',
            r'\b(?:question|questionable)\b',
            r'\b(?:differential|ddx)\b',
            r'\b(?:cannot\s+rule\s+out|r/o)\b',
        ]
        
    def is_uncertain(self, entity: MedicalEntity, text: str) -> bool:
        """Check if entity mention is uncertain."""
        # Get surrounding context
        start_context = max(0, entity.start - 50)
        end_context = min(len(text), entity.end + 50)
        context = text[start_context:end_context].lower()
        
        # Check for uncertainty patterns
        for pattern in self.uncertainty_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return True
        return False


class EntityLinker:
    """Links entities to knowledge base IDs."""
    
    def __init__(self):
        self.knowledge_base = {}  # Simplified KB
        self._load_common_mappings()
        
    def _load_common_mappings(self):
        """Load common entity mappings."""
        # Common conditions
        self.knowledge_base.update({
            "diabetes": "SNOMED:73211009",
            "diabetes mellitus": "SNOMED:73211009",
            "hypertension": "SNOMED:38341003",
            "high blood pressure": "SNOMED:38341003",
            "asthma": "SNOMED:195967001",
            "copd": "SNOMED:13645005",
            "chronic obstructive pulmonary disease": "SNOMED:13645005",
        })
        
        # Common medications
        self.knowledge_base.update({
            "aspirin": "RXNORM:1191",
            "metformin": "RXNORM:6809",
            "lisinopril": "RXNORM:29046",
            "atorvastatin": "RXNORM:83367",
            "omeprazole": "RXNORM:7646",
        })
        
        # Common anatomy
        self.knowledge_base.update({
            "heart": "SNOMED:80891009",
            "lung": "SNOMED:39607008",
            "lungs": "SNOMED:39607008",
            "liver": "SNOMED:10200004",
            "kidney": "SNOMED:64033007",
            "brain": "SNOMED:12738006",
        })
        
    def link_entity(self, entity: MedicalEntity) -> Optional[str]:
        """Link entity to knowledge base ID."""
        text_lower = entity.text.lower()
        return self.knowledge_base.get(text_lower)


class HierarchicalRecognizer:
    """Recognizes hierarchical relationships between entities."""
    
    def __init__(self):
        self.hierarchies = {
            "diabetes": ["endocrine disorder", "metabolic disorder", "chronic disease"],
            "type 2 diabetes": ["diabetes", "endocrine disorder", "metabolic disorder"],
            "insulin": ["hormone", "medication", "endocrine agent"],
            "metformin": ["antidiabetic drug", "medication", "biguanide"],
            "chest": ["thorax", "body region", "anatomy"],
            "heart": ["cardiac organ", "thoracic organ", "organ"],
        }
        
    def get_hierarchy(self, entity: MedicalEntity) -> Optional[List[str]]:
        """Get hierarchical path for entity."""
        text_lower = entity.text.lower()
        return self.hierarchies.get(text_lower)


class MedicalEntityExtractor:
    """Advanced medical entity extractor with multi-model support."""
    
    def __init__(self, 
                 models: Optional[List[str]] = None,
                 use_crf: bool = True,
                 calibration_temperature: float = 1.5):
        """
        Initialize the medical entity extractor.
        
        Args:
            models: List of model names to use (defaults to BioBERT)
            use_crf: Whether to use CRF layer
            calibration_temperature: Temperature for confidence calibration
        """
        self.models = models or ["dmis-lab/biobert-base-cased-v1.2"]
        self.use_crf = use_crf
        self.calibrator = ConfidenceCalibrator(calibration_temperature)
        self.negation_detector = NegationDetector()
        self.uncertainty_detector = UncertaintyDetector()
        self.entity_linker = EntityLinker()
        self.hierarchical_recognizer = HierarchicalRecognizer()
        
        # Initialize models
        self.pipelines = {}
        self._initialize_models()
        
        # Initialize spaCy for additional processing
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_sci_sm")
            except:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except:
                    logger.warning("No spacy models found, spacy features disabled")
                    self.nlp = None
        else:
            self.nlp = None
            
        # Entity type mapping
        self.label_mapping = self._create_label_mapping()
        
        # Regex patterns for specific entity types
        self.regex_patterns = self._create_regex_patterns()
        
    def _initialize_models(self):
        """Initialize all models."""
        for model_name in self.models:
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForTokenClassification.from_pretrained(model_name)
                
                # Add CRF layer if requested
                if self.use_crf:
                    num_labels = model.config.num_labels
                    self.crf = CRFLayer(num_labels)
                    
                # Create pipeline
                self.pipelines[model_name] = pipeline(
                    "ner",
                    model=model,
                    tokenizer=tokenizer,
                    aggregation_strategy="simple"
                )
                logger.info(f"Loaded model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                
    def _create_label_mapping(self) -> Dict[str, EntityType]:
        """Create mapping from model labels to entity types."""
        return {
            # BioBERT labels
            "DISEASE": EntityType.CONDITION,
            "DRUG": EntityType.DRUG,
            "DRUG_N": EntityType.DRUG,
            "PROCEDURE": EntityType.PROCEDURE,
            "TEST": EntityType.TEST,
            "ANATOMY": EntityType.ANATOMY,
            
            # Common variations
            "MEDICATION": EntityType.DRUG,
            "CONDITION": EntityType.CONDITION,
            "LAB_TEST": EntityType.TEST,
            "LAB": EntityType.TEST,
            "BODY_PART": EntityType.ANATOMY,
            "SYMPTOM": EntityType.CONDITION,
            "SIGN": EntityType.CONDITION,
        }
        
    def _create_regex_patterns(self) -> Dict[EntityType, List[re.Pattern]]:
        """Create regex patterns for specific entity types."""
        return {
            EntityType.DOSAGE: [
                re.compile(r'\b\d+\s*(?:mg|g|mcg|ug|ml|cc|units?|iu)\b', re.I),
                re.compile(r'\b\d+\s*(?:-|to)\s*\d+\s*(?:mg|g|mcg|ug|ml|cc|units?|iu)\b', re.I),
            ],
            EntityType.FREQUENCY: [
                re.compile(r'\b(?:once|twice|three\s+times|four\s+times)\s+(?:a\s+)?(?:day|daily|week|weekly|month|monthly)\b', re.I),
                re.compile(r'\b(?:q|every)\s*\d+\s*(?:h|hr|hrs|hours?|d|days?|w|wk|weeks?|mo|months?)\b', re.I),
                re.compile(r'\b(?:bid|tid|qid|qd|qod|prn|ac|pc|hs)\b', re.I),
                re.compile(r'\b\d+\s*times?\s+(?:per|a)\s+(?:day|week|month)\b', re.I),
            ],
            EntityType.ANATOMY: [
                re.compile(r'\b(?:head|neck|chest|abdomen|pelvis|extremit(?:y|ies)|spine|back)\b', re.I),
                re.compile(r'\b(?:heart|lung|liver|kidney|brain|stomach|intestine|colon)\b', re.I),
                re.compile(r'\b(?:arm|leg|foot|feet|hand|finger|toe|shoulder|knee|hip|ankle|wrist|elbow)\b', re.I),
            ],
        }
        
    def extract_entities(self, 
                        text: str, 
                        context: Optional[Dict[str, Any]] = None) -> List[MedicalEntity]:
        """
        Extract medical entities from text.
        
        Args:
            text: Input text
            context: Optional context information
            
        Returns:
            List of extracted medical entities
        """
        all_entities = []
        
        # Extract from each model
        for model_name, pipeline in self.pipelines.items():
            model_entities = self._extract_from_model(text, pipeline, model_name)
            all_entities.extend(model_entities)
            
        # Extract using regex patterns
        regex_entities = self._extract_regex_entities(text)
        all_entities.extend(regex_entities)
        
        # Merge and deduplicate entities
        merged_entities = self._merge_entities(all_entities)
        
        # Apply post-processing
        processed_entities = []
        for entity in merged_entities:
            # Detect negation
            entity.negated = self.negation_detector.is_negated(entity, text)
            
            # Detect uncertainty
            entity.uncertain = self.uncertainty_detector.is_uncertain(entity, text)
            
            # Link to knowledge base
            entity.linked_id = self.entity_linker.link_entity(entity)
            
            # Get hierarchy
            entity.hierarchy = self.hierarchical_recognizer.get_hierarchy(entity)
            
            # Calibrate confidence
            entity.confidence = self.calibrator.calibrate_scores([entity.raw_confidence])[0]
            
            # Add context
            entity.context = self._extract_context(text, entity.start, entity.end)
            
            processed_entities.append(entity)
            
        return processed_entities
        
    def _extract_from_model(self, 
                           text: str, 
                           pipeline: Any, 
                           model_name: str) -> List[MedicalEntity]:
        """Extract entities using a specific model."""
        entities = []
        
        try:
            # Run NER pipeline
            results = pipeline(text)
            
            for result in results:
                # Map label to entity type
                label = result['entity_group'].upper()
                entity_type = self.label_mapping.get(label)
                
                if entity_type:
                    entity = MedicalEntity(
                        text=result['word'],
                        type=entity_type,
                        start=result['start'],
                        end=result['end'],
                        confidence=result['score'],
                        raw_confidence=result['score'],
                        source_model=model_name
                    )
                    entities.append(entity)
                    
        except Exception as e:
            logger.error(f"Error extracting from {model_name}: {e}")
            
        return entities
        
    def _extract_regex_entities(self, text: str) -> List[MedicalEntity]:
        """Extract entities using regex patterns."""
        entities = []
        
        for entity_type, patterns in self.regex_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    entity = MedicalEntity(
                        text=match.group(),
                        type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.8,  # Default confidence for regex
                        raw_confidence=0.8,
                        source_model="regex"
                    )
                    entities.append(entity)
                    
        return entities
        
    def _merge_entities(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """Merge overlapping entities and resolve conflicts."""
        if not entities:
            return []
            
        # Sort by start position
        sorted_entities = sorted(entities, key=lambda e: (e.start, -e.end))
        
        merged = []
        current = sorted_entities[0]
        
        for entity in sorted_entities[1:]:
            # Check for overlap
            if entity.start < current.end:
                # Overlapping - keep the one with higher confidence
                if entity.confidence > current.confidence:
                    current = entity
            else:
                # No overlap
                merged.append(current)
                current = entity
                
        merged.append(current)
        return merged
        
    def _extract_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Extract context around entity."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]
        
    def extract_with_sliding_window(self, 
                                   text: str, 
                                   window_size: int = 512,
                                   overlap: int = 50) -> List[MedicalEntity]:
        """Extract entities using sliding window for long texts."""
        entities = []
        
        # Process in windows
        for i in range(0, len(text), window_size - overlap):
            window_text = text[i:i + window_size]
            window_entities = self.extract_entities(window_text)
            
            # Adjust positions
            for entity in window_entities:
                entity.start += i
                entity.end += i
                
            entities.extend(window_entities)
            
        # Merge overlapping entities from different windows
        return self._merge_entities(entities)