"""
BioBERT Model Manager for Medical Entity Recognition

This module provides centralized management of BioBERT models for medical term extraction,
including model loading, caching, batch processing, and inference optimization.
"""

import os
import torch
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from threading import Lock
import time
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    pipeline,
    BatchEncoding
)
import numpy as np

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class EntityPrediction:
    """Represents a predicted medical entity"""
    text: str
    entity_type: str
    start: int
    end: int
    confidence: float
    token_indices: List[int]


@dataclass
class BatchResult:
    """Results from batch processing"""
    predictions: List[List[EntityPrediction]]
    processing_time: float
    batch_size: int


class BioBERTModelManager:
    """
    Manages BioBERT model lifecycle and provides optimized inference
    
    Features:
    - Lazy model loading with singleton pattern
    - GPU/CPU device management
    - Batch processing optimization
    - Model warm-up for consistent latency
    - Thread-safe operations
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Implement singleton pattern for model manager"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize model manager (only runs once due to singleton)"""
        if self._initialized:
            return
            
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.device = None
        self.model_name = "dmis-lab/biobert-base-cased-v1.2"
        self.max_length = 512
        self.batch_size = 8
        self.entity_types = [
            "CONDITION",
            "MEDICATION", 
            "PROCEDURE",
            "LAB_TEST",
            "OBSERVATION"
        ]
        self._model_lock = Lock()
        self._is_loaded = False
        self._initialized = True
        
        # Entity type mapping for post-processing
        self.entity_mapping = {
            "DISEASE": "CONDITION",
            "DRUG": "MEDICATION",
            "CHEMICAL": "MEDICATION",
            "TREATMENT": "PROCEDURE",
            "TEST": "LAB_TEST",
            "SYMPTOM": "OBSERVATION"
        }
        
        logger.info("BioBERT Model Manager initialized")
    
    def initialize_model(self, force_reload: bool = False) -> bool:
        """
        Initialize BioBERT model and tokenizer
        
        Args:
            force_reload: Force model reload even if already loaded
            
        Returns:
            bool: True if initialization successful
        """
        with self._model_lock:
            if self._is_loaded and not force_reload:
                logger.info("Model already loaded")
                return True
            
            try:
                logger.info(f"Loading BioBERT model: {self.model_name}")
                start_time = time.time()
                
                # Determine device
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                logger.info(f"Using device: {self.device}")
                
                # Load tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    do_lower_case=False  # BioBERT is cased
                )
                
                # Load model with proper configuration for NER
                self.model = AutoModelForTokenClassification.from_pretrained(
                    self.model_name,
                    num_labels=len(self.entity_types) * 2 + 1,  # B-, I- for each type + O
                    ignore_mismatched_sizes=True
                )
                
                # Move model to device
                self.model.to(self.device)
                self.model.eval()
                
                # Create NER pipeline
                self.pipeline = pipeline(
                    "ner",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=0 if self.device.type == "cuda" else -1,
                    aggregation_strategy="max"
                )
                
                load_time = time.time() - start_time
                logger.info(f"Model loaded successfully in {load_time:.2f} seconds")
                
                # Warm up model
                self._warm_up_model()
                
                self._is_loaded = True
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize model: {e}")
                self._is_loaded = False
                return False
    
    def _warm_up_model(self):
        """Warm up model with sample predictions for consistent latency"""
        try:
            logger.info("Warming up model...")
            sample_texts = [
                "Patient has diabetes mellitus type 2",
                "Prescribed metformin 500mg twice daily",
                "Blood glucose level 126 mg/dL"
            ]
            
            for text in sample_texts:
                _ = self.extract_entities(text)
            
            logger.info("Model warm-up completed")
        except Exception as e:
            logger.warning(f"Model warm-up failed: {e}")
    
    def extract_entities(self, text: str, confidence_threshold: float = 0.7) -> List[EntityPrediction]:
        """
        Extract medical entities from text
        
        Args:
            text: Input text
            confidence_threshold: Minimum confidence for predictions
            
        Returns:
            List of entity predictions
        """
        if not self._is_loaded:
            if not self.initialize_model():
                logger.error("Model not initialized")
                return []
        
        try:
            # Use pipeline for NER
            raw_predictions = self.pipeline(text)
            
            # Convert to EntityPrediction objects
            entities = []
            for pred in raw_predictions:
                # Map entity type if needed
                entity_type = self.entity_mapping.get(
                    pred['entity_group'].upper(),
                    pred['entity_group'].upper()
                )
                
                # Only include recognized entity types
                if entity_type in self.entity_types and pred['score'] >= confidence_threshold:
                    entity = EntityPrediction(
                        text=pred['word'].replace('##', ''),  # Remove BERT subword markers
                        entity_type=entity_type,
                        start=pred['start'],
                        end=pred['end'],
                        confidence=pred['score'],
                        token_indices=[]  # Pipeline doesn't provide token indices
                    )
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    def extract_entities_batch(
        self,
        texts: List[str],
        confidence_threshold: float = 0.7,
        batch_size: Optional[int] = None
    ) -> BatchResult:
        """
        Extract entities from multiple texts efficiently
        
        Args:
            texts: List of input texts
            confidence_threshold: Minimum confidence for predictions
            batch_size: Batch size for processing (uses default if None)
            
        Returns:
            BatchResult with predictions and metadata
        """
        if not self._is_loaded:
            if not self.initialize_model():
                logger.error("Model not initialized")
                return BatchResult(predictions=[], processing_time=0, batch_size=0)
        
        start_time = time.time()
        batch_size = batch_size or self.batch_size
        all_predictions = []
        
        try:
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_predictions = []
                
                # Tokenize batch
                inputs = self.tokenizer(
                    batch_texts,
                    truncation=True,
                    padding=True,
                    max_length=self.max_length,
                    return_tensors="pt"
                ).to(self.device)
                
                # Get predictions
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    predictions = torch.argmax(outputs.logits, dim=-1)
                    probabilities = torch.softmax(outputs.logits, dim=-1)
                
                # Process each text in batch
                for batch_idx, text in enumerate(batch_texts):
                    entities = self._decode_predictions(
                        text,
                        predictions[batch_idx],
                        probabilities[batch_idx],
                        inputs.encodings[batch_idx],
                        confidence_threshold
                    )
                    batch_predictions.append(entities)
                
                all_predictions.extend(batch_predictions)
            
            processing_time = time.time() - start_time
            return BatchResult(
                predictions=all_predictions,
                processing_time=processing_time,
                batch_size=len(texts)
            )
            
        except Exception as e:
            logger.error(f"Batch extraction failed: {e}")
            processing_time = time.time() - start_time
            return BatchResult(
                predictions=[[] for _ in texts],
                processing_time=processing_time,
                batch_size=len(texts)
            )
    
    def _decode_predictions(
        self,
        text: str,
        predictions: torch.Tensor,
        probabilities: torch.Tensor,
        encoding: BatchEncoding,
        confidence_threshold: float
    ) -> List[EntityPrediction]:
        """
        Decode model predictions into entities
        
        Args:
            text: Original text
            predictions: Predicted label indices
            probabilities: Prediction probabilities
            encoding: Tokenizer encoding
            confidence_threshold: Minimum confidence
            
        Returns:
            List of entity predictions
        """
        entities = []
        current_entity = None
        
        # Get label mappings
        id2label = self.model.config.id2label if hasattr(self.model.config, 'id2label') else {}
        
        for idx, (pred_id, probs) in enumerate(zip(predictions, probabilities)):
            pred_id = pred_id.item()
            confidence = probs[pred_id].item()
            
            # Skip special tokens
            if encoding.tokens[idx] in ['[CLS]', '[SEP]', '[PAD]']:
                continue
            
            label = id2label.get(pred_id, f"LABEL_{pred_id}")
            
            # Handle BIO tagging
            if label.startswith('B-'):
                # Save previous entity if exists
                if current_entity and current_entity.confidence >= confidence_threshold:
                    entities.append(current_entity)
                
                # Start new entity
                entity_type = label[2:]
                char_start, char_end = encoding.token_to_chars(idx)
                
                current_entity = EntityPrediction(
                    text=text[char_start:char_end],
                    entity_type=self.entity_mapping.get(entity_type, entity_type),
                    start=char_start,
                    end=char_end,
                    confidence=confidence,
                    token_indices=[idx]
                )
                
            elif label.startswith('I-') and current_entity:
                # Continue current entity
                entity_type = label[2:]
                if current_entity.entity_type == self.entity_mapping.get(entity_type, entity_type):
                    char_start, char_end = encoding.token_to_chars(idx)
                    current_entity.text = text[current_entity.start:char_end]
                    current_entity.end = char_end
                    current_entity.confidence = min(current_entity.confidence, confidence)
                    current_entity.token_indices.append(idx)
            else:
                # O label or mismatched I- label
                if current_entity and current_entity.confidence >= confidence_threshold:
                    entities.append(current_entity)
                current_entity = None
        
        # Don't forget last entity
        if current_entity and current_entity.confidence >= confidence_threshold:
            entities.append(current_entity)
        
        return entities
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_name": self.model_name,
            "is_loaded": self._is_loaded,
            "device": str(self.device) if self.device else "not initialized",
            "entity_types": self.entity_types,
            "max_length": self.max_length,
            "batch_size": self.batch_size
        }
    
    def cleanup(self):
        """Clean up model resources"""
        with self._model_lock:
            if self.model:
                del self.model
            if self.tokenizer:
                del self.tokenizer
            if self.pipeline:
                del self.pipeline
            
            self.model = None
            self.tokenizer = None
            self.pipeline = None
            self._is_loaded = False
            
            # Clear CUDA cache if using GPU
            if self.device and self.device.type == "cuda":
                torch.cuda.empty_cache()
            
            logger.info("Model resources cleaned up")


# Convenience function for getting the singleton instance
def get_biobert_manager() -> BioBERTModelManager:
    """Get the singleton BioBERT model manager instance"""
    return BioBERTModelManager()