"""
BioBERT Service for Medical Entity Recognition

This service provides high-level functionality for extracting medical entities
from text using BioBERT, with integration to terminology mapping and 
post-processing capabilities.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import time
from collections import defaultdict
import logging

from app.ml.biobert.model_manager import (
    get_biobert_manager,
    EntityPrediction,
    BatchResult
)
from app.ml.medical_entity_extractor import (
    MedicalEntityExtractor,
    EntityType,
    MedicalEntity as ExtractorEntity
)
from app.extractors.regex_patterns import get_patterns_by_type
from app.models.preprocessing import clean_text, chunk_document
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class MedicalEntity:
    """Enhanced medical entity with additional metadata"""
    text: str
    normalized_text: str
    entity_type: str
    start_position: int
    end_position: int
    confidence: float
    source: str  # 'biobert', 'regex', 'ensemble'
    context: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    terminology_mappings: Optional[Dict[str, List[Dict[str, Any]]]] = None


@dataclass
class DocumentAnalysis:
    """Complete document analysis results"""
    entities: List[MedicalEntity]
    entity_summary: Dict[str, int]
    processing_time: float
    chunks_processed: int
    extraction_methods: List[str]
    confidence_stats: Dict[str, float]


class BioBERTService:
    """
    High-level service for medical entity extraction using BioBERT
    
    Features:
    - Entity extraction with BioBERT
    - Regex pattern matching for specific medical terms
    - Ensemble approach combining multiple methods
    - Post-processing and normalization
    - Integration with terminology mapping
    - Confidence scoring and filtering
    """
    
    def __init__(self, 
                 use_regex_patterns: bool = True,
                 use_ensemble: bool = True,
                 confidence_threshold: float = 0.7,
                 terminology_mapper = None,
                 use_advanced_extractor: bool = True):
        """
        Initialize BioBERT service
        
        Args:
            use_regex_patterns: Whether to use regex pattern matching
            use_ensemble: Whether to use ensemble approach
            confidence_threshold: Minimum confidence for entity acceptance
            terminology_mapper: Optional terminology mapper instance
            use_advanced_extractor: Whether to use the advanced MedicalEntityExtractor
        """
        self.model_manager = get_biobert_manager()
        self.use_regex_patterns = use_regex_patterns
        self.use_ensemble = use_ensemble
        self.confidence_threshold = confidence_threshold
        self.terminology_mapper = terminology_mapper
        self.use_advanced_extractor = use_advanced_extractor
        
        # Initialize advanced extractor if enabled
        if use_advanced_extractor:
            self.medical_extractor = MedicalEntityExtractor(
                use_crf=True,
                calibration_temperature=1.5
            )
        else:
            self.medical_extractor = None
        
        # Medical term normalizers
        self.normalizers = {
            "MEDICATION": self._normalize_medication,
            "LAB_TEST": self._normalize_lab_test,
            "CONDITION": self._normalize_condition
        }
        
        # Initialize regex patterns if enabled
        self.regex_patterns = {}
        if use_regex_patterns and not use_advanced_extractor:
            self._initialize_regex_patterns()
        
        logger.info(f"BioBERT Service initialized (ensemble={use_ensemble}, regex={use_regex_patterns}, advanced={use_advanced_extractor})")
    
    def _initialize_regex_patterns(self):
        """Initialize medical regex patterns"""
        try:
            # Get patterns for each entity type
            pattern_types = {
                "MEDICATION": ["medications", "dosages"],
                "LAB_TEST": ["lab_tests", "lab_values"],
                "CONDITION": ["conditions", "symptoms"],
                "PROCEDURE": ["procedures"]
            }
            
            for entity_type, pattern_names in pattern_types.items():
                self.regex_patterns[entity_type] = []
                for pattern_name in pattern_names:
                    patterns = get_patterns_by_type(pattern_name)
                    self.regex_patterns[entity_type].extend([
                        (re.compile(p["pattern"], re.IGNORECASE), p.get("name", ""))
                        for p in patterns
                    ])
            
            logger.info(f"Initialized {sum(len(p) for p in self.regex_patterns.values())} regex patterns")
        except Exception as e:
            logger.warning(f"Failed to initialize regex patterns: {e}")
            self.regex_patterns = {}
    
    def extract_entities(self, 
                        text: str,
                        extract_context: bool = True,
                        map_to_terminologies: bool = True,
                        chunk_size: int = 2000) -> List[MedicalEntity]:
        """
        Extract medical entities from text
        
        Args:
            text: Input text
            extract_context: Whether to extract surrounding context
            map_to_terminologies: Whether to map to standard terminologies
            chunk_size: Size of text chunks for processing
            
        Returns:
            List of medical entities
        """
        start_time = time.time()
        
        # Clean and prepare text
        cleaned_text = clean_text(text)
        
        # Use advanced extractor if enabled
        if self.use_advanced_extractor and self.medical_extractor:
            entities = self._extract_with_advanced_extractor(cleaned_text)
        else:
            # Extract entities using selected methods
            if self.use_ensemble:
                entities = self._extract_ensemble(cleaned_text, chunk_size)
            else:
                entities = self._extract_biobert_only(cleaned_text, chunk_size)
        
        # Post-process entities
        entities = self._post_process_entities(entities, cleaned_text, extract_context)
        
        # Map to terminologies if requested
        if map_to_terminologies and self.terminology_mapper:
            entities = self._map_to_terminologies(entities)
        
        processing_time = time.time() - start_time
        logger.info(f"Extracted {len(entities)} entities in {processing_time:.2f}s")
        
        return entities
    
    def analyze_document(self,
                        text: str,
                        extract_context: bool = True,
                        map_to_terminologies: bool = True,
                        chunk_size: int = 2000) -> DocumentAnalysis:
        """
        Perform comprehensive document analysis
        
        Args:
            text: Input document text
            extract_context: Whether to extract surrounding context
            map_to_terminologies: Whether to map to standard terminologies
            chunk_size: Size of text chunks for processing
            
        Returns:
            Complete document analysis
        """
        start_time = time.time()
        
        # Extract entities
        entities = self.extract_entities(
            text, 
            extract_context, 
            map_to_terminologies,
            chunk_size
        )
        
        # Calculate statistics
        entity_summary = defaultdict(int)
        confidence_sum = defaultdict(float)
        confidence_count = defaultdict(int)
        extraction_methods = set()
        
        for entity in entities:
            entity_summary[entity.entity_type] += 1
            confidence_sum[entity.entity_type] += entity.confidence
            confidence_count[entity.entity_type] += 1
            extraction_methods.add(entity.source)
        
        # Calculate average confidence by type
        confidence_stats = {
            entity_type: confidence_sum[entity_type] / confidence_count[entity_type]
            for entity_type in confidence_sum
        }
        
        # Calculate chunks processed
        chunks = chunk_document(clean_text(text), chunk_size)
        
        processing_time = time.time() - start_time
        
        return DocumentAnalysis(
            entities=entities,
            entity_summary=dict(entity_summary),
            processing_time=processing_time,
            chunks_processed=len(chunks),
            extraction_methods=list(extraction_methods),
            confidence_stats=confidence_stats
        )
    
    def extract_entities_batch(self,
                              texts: List[str],
                              batch_size: int = 8) -> List[List[MedicalEntity]]:
        """
        Extract entities from multiple texts efficiently
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            
        Returns:
            List of entity lists for each input text
        """
        # Use model manager's batch processing
        batch_result = self.model_manager.extract_entities_batch(
            texts,
            self.confidence_threshold,
            batch_size
        )
        
        # Convert predictions to MedicalEntity objects
        all_entities = []
        for text, predictions in zip(texts, batch_result.predictions):
            entities = [
                self._prediction_to_entity(pred, text, "biobert")
                for pred in predictions
            ]
            # Post-process each text's entities
            entities = self._post_process_entities(entities, text, extract_context=False)
            all_entities.append(entities)
        
        return all_entities
    
    def _extract_with_advanced_extractor(self, text: str) -> List[MedicalEntity]:
        """Extract entities using advanced MedicalEntityExtractor"""
        # Use sliding window for long texts
        extractor_entities = self.medical_extractor.extract_with_sliding_window(text)
        
        # Convert ExtractorEntity to MedicalEntity
        entities = []
        for ext_entity in extractor_entities:
            # Map entity type
            entity_type_map = {
                EntityType.CONDITION: "CONDITION",
                EntityType.DRUG: "MEDICATION",
                EntityType.PROCEDURE: "PROCEDURE",
                EntityType.TEST: "LAB_TEST",
                EntityType.ANATOMY: "ANATOMY",
                EntityType.DOSAGE: "DOSAGE",
                EntityType.FREQUENCY: "FREQUENCY",
                EntityType.OBSERVATION: "OBSERVATION"
            }
            
            entity = MedicalEntity(
                text=ext_entity.text,
                normalized_text=ext_entity.text.lower().strip(),
                entity_type=entity_type_map.get(ext_entity.type, str(ext_entity.type.value)),
                start_position=ext_entity.start,
                end_position=ext_entity.end,
                confidence=ext_entity.confidence,
                source="advanced_extractor",
                context=ext_entity.context,
                attributes={
                    "negated": ext_entity.negated,
                    "uncertain": ext_entity.uncertain,
                    "linked_id": ext_entity.linked_id,
                    "hierarchy": ext_entity.hierarchy,
                    "raw_confidence": ext_entity.raw_confidence
                }
            )
            entities.append(entity)
        
        return entities
    
    def _extract_ensemble(self, text: str, chunk_size: int) -> List[MedicalEntity]:
        """Extract entities using ensemble of methods"""
        all_entities = []
        
        # Extract with BioBERT
        biobert_entities = self._extract_biobert_only(text, chunk_size)
        all_entities.extend(biobert_entities)
        
        # Extract with regex patterns
        if self.use_regex_patterns:
            regex_entities = self._extract_regex_patterns(text)
            all_entities.extend(regex_entities)
        
        # Merge overlapping entities
        merged_entities = self._merge_overlapping_entities(all_entities)
        
        return merged_entities
    
    def _extract_biobert_only(self, text: str, chunk_size: int) -> List[MedicalEntity]:
        """Extract entities using only BioBERT"""
        entities = []
        
        # Process in chunks if text is long
        chunks = chunk_document(text, chunk_size)
        
        for chunk_text, chunk_start in chunks:
            # Extract entities from chunk
            predictions = self.model_manager.extract_entities(
                chunk_text,
                self.confidence_threshold
            )
            
            # Convert to MedicalEntity objects with adjusted positions
            for pred in predictions:
                entity = self._prediction_to_entity(
                    pred,
                    text,
                    "biobert",
                    position_offset=chunk_start
                )
                entities.append(entity)
        
        return entities
    
    def _extract_regex_patterns(self, text: str) -> List[MedicalEntity]:
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, patterns in self.regex_patterns.items():
            for pattern, pattern_name in patterns:
                for match in pattern.finditer(text):
                    entity = MedicalEntity(
                        text=match.group(0),
                        normalized_text=match.group(0).lower().strip(),
                        entity_type=entity_type,
                        start_position=match.start(),
                        end_position=match.end(),
                        confidence=0.9,  # High confidence for regex matches
                        source="regex",
                        attributes={"pattern": pattern_name} if pattern_name else None
                    )
                    entities.append(entity)
        
        return entities
    
    def _prediction_to_entity(self,
                             prediction: EntityPrediction,
                             full_text: str,
                             source: str,
                             position_offset: int = 0) -> MedicalEntity:
        """Convert BioBERT prediction to MedicalEntity"""
        return MedicalEntity(
            text=prediction.text,
            normalized_text=prediction.text.lower().strip(),
            entity_type=prediction.entity_type,
            start_position=prediction.start + position_offset,
            end_position=prediction.end + position_offset,
            confidence=prediction.confidence,
            source=source
        )
    
    def _merge_overlapping_entities(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """Merge overlapping entities, keeping highest confidence"""
        if not entities:
            return []
        
        # Sort by start position
        sorted_entities = sorted(entities, key=lambda e: (e.start_position, -e.confidence))
        
        merged = []
        current = sorted_entities[0]
        
        for entity in sorted_entities[1:]:
            # Check for overlap
            if entity.start_position < current.end_position:
                # Overlapping - keep higher confidence or ensemble
                if entity.confidence > current.confidence:
                    current = entity
                elif entity.source != current.source:
                    # Different sources - create ensemble entity
                    current = MedicalEntity(
                        text=current.text if len(current.text) >= len(entity.text) else entity.text,
                        normalized_text=current.normalized_text,
                        entity_type=current.entity_type,
                        start_position=min(current.start_position, entity.start_position),
                        end_position=max(current.end_position, entity.end_position),
                        confidence=max(current.confidence, entity.confidence),
                        source="ensemble",
                        attributes={"sources": [current.source, entity.source]}
                    )
            else:
                # No overlap - save current and move to next
                merged.append(current)
                current = entity
        
        # Don't forget the last entity
        merged.append(current)
        
        return merged
    
    def _post_process_entities(self,
                              entities: List[MedicalEntity],
                              text: str,
                              extract_context: bool) -> List[MedicalEntity]:
        """Post-process entities with normalization and context extraction"""
        processed = []
        
        for entity in entities:
            # Normalize entity text based on type
            if entity.entity_type in self.normalizers:
                entity.normalized_text = self.normalizers[entity.entity_type](entity.text)
            
            # Extract context if requested
            if extract_context:
                entity.context = self._extract_context(
                    text,
                    entity.start_position,
                    entity.end_position,
                    window=50
                )
            
            # Filter out low confidence entities
            if entity.confidence >= self.confidence_threshold:
                processed.append(entity)
        
        return processed
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Extract surrounding context for an entity"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        
        context = text[context_start:context_end]
        
        # Mark the entity in context
        entity_start = start - context_start
        entity_end = end - context_start
        
        marked_context = (
            context[:entity_start] + 
            "[" + context[entity_start:entity_end] + "]" +
            context[entity_end:]
        )
        
        return marked_context.strip()
    
    def _normalize_medication(self, text: str) -> str:
        """Normalize medication names"""
        # Remove common suffixes
        normalized = re.sub(r'\s*(tablet|capsule|injection|solution|cream|ointment)s?\b', '', text, flags=re.IGNORECASE)
        # Remove dosage information for name normalization
        normalized = re.sub(r'\s*\d+\s*(mg|mcg|ml|g|%)\b', '', normalized, flags=re.IGNORECASE)
        return normalized.lower().strip()
    
    def _normalize_lab_test(self, text: str) -> str:
        """Normalize lab test names"""
        # Remove "level", "test", etc.
        normalized = re.sub(r'\s*(level|test|measurement|value)\b', '', text, flags=re.IGNORECASE)
        return normalized.lower().strip()
    
    def _normalize_condition(self, text: str) -> str:
        """Normalize condition names"""
        # Remove "disease", "syndrome", etc. but keep if it's part of the name
        if not any(term in text.lower() for term in ["parkinson", "alzheimer", "cushing"]):
            normalized = re.sub(r'\s*(disease|syndrome|disorder)\b', '', text, flags=re.IGNORECASE)
        else:
            normalized = text
        return normalized.lower().strip()
    
    def _map_to_terminologies(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """Map entities to standard terminologies"""
        if not self.terminology_mapper:
            return entities
        
        for entity in entities:
            try:
                # Determine terminology system based on entity type
                if entity.entity_type == "MEDICATION":
                    systems = ["rxnorm"]
                elif entity.entity_type == "LAB_TEST":
                    systems = ["loinc"]
                elif entity.entity_type in ["CONDITION", "PROCEDURE"]:
                    systems = ["snomed"]
                else:
                    systems = ["snomed", "loinc", "rxnorm"]
                
                # Get mappings for each system
                mappings = {}
                for system in systems:
                    results = self.terminology_mapper.map_term(
                        entity.normalized_text,
                        system=system,
                        context=entity.context
                    )
                    if results:
                        mappings[system] = results[:3]  # Top 3 matches
                
                if mappings:
                    entity.terminology_mappings = mappings
                    
            except Exception as e:
                logger.warning(f"Failed to map entity '{entity.text}': {e}")
        
        return entities
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service configuration and status"""
        model_info = self.model_manager.get_model_info()
        
        return {
            "service": "BioBERT Medical Entity Recognition",
            "configuration": {
                "use_regex_patterns": self.use_regex_patterns,
                "use_ensemble": self.use_ensemble,
                "confidence_threshold": self.confidence_threshold,
                "terminology_mapping_enabled": self.terminology_mapper is not None
            },
            "model": model_info,
            "regex_patterns": {
                entity_type: len(patterns)
                for entity_type, patterns in self.regex_patterns.items()
            } if self.use_regex_patterns else {}
        }


# Convenience function for creating service instance
def create_biobert_service(**kwargs) -> BioBERTService:
    """Create BioBERT service with optional configuration"""
    return BioBERTService(**kwargs)