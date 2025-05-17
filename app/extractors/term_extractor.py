"""
Term extractor for Medical Terminology Mapper.
This module extracts medical terminology from text using a biomedical language model.
Adapted from the Clinical Protocol Extractor's entity_extractor.py with terminology-specific adjustments.
"""

import torch
import logging
import time
import os
import hashlib
import re
from typing import List, Dict, Any, Optional

# Import from app modules
from app.models.preprocessing import (
    clean_text, chunk_document, prepare_for_biobert, 
    optimize_tokens_for_biobert, consolidate_term_predictions
)
from app.extractors.term_cache import get_term_cache
from app.extractors.regex_patterns import get_patterns_by_type, get_all_patterns
from app.extractors.terminology_mapper import TerminologyMapper

# Set up logging
logger = logging.getLogger(__name__)

class TermExtractor:
    """
    Extracts medical terminology from text using a biomedical language model.
    This class handles named entity recognition (NER) for medical terms and maps them to standard vocabularies.
    """
    
    def __init__(self, model_manager, use_cache=True, offline_mode=False, confidence_threshold=0.7, use_terminology=True):
        """
        Initialize the term extractor with a model manager.
        
        Args:
            model_manager: ModelManager instance that provides the NER model
            use_cache (bool): Whether to use term caching for improved performance
            offline_mode (bool): Whether to operate in offline mode using pattern matching
            confidence_threshold (float): Default confidence threshold for term extraction
            use_terminology (bool): Whether to map terms to standard terminologies
        """
        self.model_manager = model_manager
        self.use_cache = use_cache
        self.offline_mode = offline_mode
        self.confidence_threshold = confidence_threshold
        self.use_terminology = use_terminology
        
        # Get model ID for cache keys
        self.model_id = "offline" if offline_mode else self._get_model_id()
        
        # Initialize term cache if enabled
        self.cache = get_term_cache() if use_cache else None
        
        # Initialize model if not already done and not in offline mode
        if not offline_mode and not model_manager.is_initialized:
            logger.info("Initializing model manager for term extraction")
            model_manager.initialize()
            
        # Initialize terminology mapper if enabled
        self.terminology_mapper = None
        if use_terminology:
            try:
                logger.info("Initializing terminology mapper")
                self.terminology_mapper = TerminologyMapper()
            except Exception as e:
                logger.warning(f"Failed to initialize terminology mapper: {e}")
                self.use_terminology = False
    
    def _get_model_id(self) -> str:
        """
        Get a unique identifier for the current model configuration.
        
        Returns:
            str: Model identifier
        """
        if not hasattr(self.model_manager, 'model_config'):
            return "default-model"
        
        config = self.model_manager.model_config
        model_name = config.get('name', 'unknown')
        model_version = config.get('version', 'v1')
        return f"{model_name}-{model_version}"
    
    def extract_terms(self, text: str, threshold=None, map_to_terminology=None) -> List[Dict[str, Any]]:
        """
        Extract medical terms from text with confidence above the threshold.
        
        Args:
            text (str): Input text
            threshold (float, optional): Confidence threshold (0.0 to 1.0).
                                        Defaults to self.confidence_threshold
            map_to_terminology (bool, optional): Whether to map terms to standard terminologies.
                                               Defaults to self.use_terminology
            
        Returns:
            list: Extracted terms with positions and confidence scores
        """
        # Use default threshold if none provided
        if threshold is None:
            threshold = self.confidence_threshold
            
        # Use default terminology mapping setting if none provided
        if map_to_terminology is None:
            map_to_terminology = self.use_terminology
        
        # Check for empty or invalid input
        if not text or not isinstance(text, str):
            logger.warning("Invalid input text for term extraction")
            return []
        
        try:
            start_time = time.time()
            extraction_start_time = start_time
            
            # Try to get cached results first if caching is enabled
            if self.use_cache and self.cache:
                cached_terms = self.cache.get(text, self.model_id, threshold)
                if cached_terms:
                    duration = time.time() - start_time
                    logger.info(f"Retrieved {len(cached_terms)} terms from cache in {duration:.3f}s")
                    
                    # Map to terminology if requested and not already mapped
                    if map_to_terminology and self.terminology_mapper and not cached_terms[0].get('terminology', {}).get('mapped', False):
                        mapping_start_time = time.time()
                        cached_terms = self.terminology_mapper.map_terms(cached_terms, threshold)
                        mapping_duration = time.time() - mapping_start_time
                        logger.info(f"Mapped {len(cached_terms)} terms to standard terminologies in {mapping_duration:.3f}s")
                    
                    return cached_terms
            
            logger.debug(f"Extracting terms from text (length: {len(text)})")
            
            # Use pattern matching in offline mode
            if self.offline_mode:
                # Clean and preprocess text for offline extraction
                cleaned_text = clean_text(text)
                terms = self._extract_terms_offline(cleaned_text, threshold)
            # Use neural model for extraction
            else:
                # Use optimized BioBERT preprocessing pipeline
                logger.debug("Preparing text for BioBERT processing")
                prepared = prepare_for_biobert(text)
                
                # Process using BioBERT-optimized chunking
                if len(prepared['chunks']) > 1:
                    logger.debug(f"Processing {len(prepared['chunks'])} BioBERT-optimized chunks")
                    all_terms = []
                    
                    # Process each chunk
                    for chunk in prepared['chunks']:
                        chunk_text = chunk['text']
                        chunk_offset = chunk['offset']
                        
                        # Extract terms from chunk
                        chunk_terms = self._extract_from_chunk(chunk_text, threshold)
                        
                        # Adjust term positions based on chunk offset
                        for term in chunk_terms:
                            term['start'] += chunk_offset
                            term['end'] += chunk_offset
                            all_terms.append(term)
                    
                    # Consolidate predictions using the specialized consolidation function
                    terms = consolidate_term_predictions(all_terms)
                else:
                    # Process short text directly
                    terms = self._extract_from_chunk(prepared['text'], threshold)
            
            extraction_duration = time.time() - extraction_start_time
            logger.info(f"Extracted {len(terms)} terms from text in {extraction_duration:.3f}s")
            
            # Map to standard terminologies if enabled
            if map_to_terminology and self.terminology_mapper and terms:
                mapping_start_time = time.time()
                terms = self.terminology_mapper.map_terms(terms, threshold)
                mapping_duration = time.time() - mapping_start_time
                logger.info(f"Mapped terms to standard terminologies in {mapping_duration:.3f}s")
            
            # Update term cache after mapping to standard terminologies
            if self.use_cache and self.cache and terms:
                self.cache.put(text, self.model_id, threshold, terms)
            
            total_duration = time.time() - start_time
            logger.info(f"Total processing time: {total_duration:.3f}s for {len(terms)} terms")
            return terms
            
        except Exception as e:
            logger.error(f"Error in term extraction: {str(e)}", exc_info=True)
            
            # Fall back to offline mode if model extraction fails
            if not self.offline_mode:
                logger.warning("Falling back to offline extraction mode after error")
                try:
                    # Clean text consistently
                    cleaned_text = clean_text(text)
                    logger.info("Using offline pattern matching as fallback")
                    terms = self._extract_terms_offline(cleaned_text, threshold)
                    
                    # Map to standard terminologies if enabled
                    if map_to_terminology and self.terminology_mapper and terms:
                        terms = self.terminology_mapper.map_terms(terms, threshold)
                    
                    return terms
                except Exception as fallback_error:
                    logger.error(f"Offline fallback also failed: {str(fallback_error)}")
            
            return []
    
    def _extract_terms_offline(self, text: str, threshold: float) -> List[Dict[str, Any]]:
        """
        Extract medical terms using pattern matching (offline mode).
        
        Args:
            text (str): Preprocessed text
            threshold (float): Confidence threshold
            
        Returns:
            List[Dict[str, Any]]: Extracted terms
        """
        logger.info("Using offline pattern matching for term extraction")
        terms = []
        
        # Get all pattern types
        pattern_types = ['CONDITION', 'MEDICATION', 'PROCEDURE', 'LAB_TEST', 'OBSERVATION']
        
        # Process each term type
        for term_type in pattern_types:
            patterns = get_patterns_by_type(term_type)
            terms.extend(self._extract_terms_by_patterns(text, patterns, term_type, 0, threshold))
        
        # Extract dosage information as a special case
        dosage_patterns = get_patterns_by_type('DOSAGE')
        dosage_terms = self._extract_terms_by_patterns(text, dosage_patterns, 'MEDICATION', 0, threshold)
        for term in dosage_terms:
            term['subtype'] = 'DOSAGE'
        terms.extend(dosage_terms)
        
        # Deduplicate overlapping terms
        return self._resolve_overlapping_terms(terms)
        
    def _extract_terms_by_patterns(self, text: str, patterns: List[str], term_type: str, 
                                  offset: int, threshold: float) -> List[Dict[str, Any]]:
        """
        Extract terms using a list of regex patterns.
        
        Args:
            text (str): Text to process
            patterns (List[str]): List of regex patterns
            term_type (str): Type of term to extract
            offset (int): Character offset for position tracking
            threshold (float): Confidence threshold
            
        Returns:
            List[Dict[str, Any]]: Extracted terms
        """
        terms = []
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                match_text = match.group(0).strip()
                
                # Filter out very short or common words that might be false positives
                if len(match_text) < 3 or match_text.lower() in ['the', 'and', 'was', 'for', 'with', 'this', 'that']:
                    continue
                
                # Base confidence score - can be adjusted based on pattern reliability
                confidence = 0.85
                
                # Adjust confidence based on term length and capitalization
                if len(match_text) > 10:
                    confidence += 0.05  # Longer terms are more likely to be correct
                if match_text[0].isupper() and not match_text.isupper():
                    confidence += 0.05  # Proper capitalization suggests medical term
                    
                # Ensure confidence doesn't exceed 1.0
                confidence = min(confidence, 0.95)
                
                # Create term entry
                terms.append({
                    'text': match_text,
                    'type': term_type,
                    'start': offset + match.start(),
                    'end': offset + match.end(),
                    'confidence': confidence,
                    'terminology': {
                        'mapped': False,
                        'vocabulary': self._get_vocabulary_for_type(term_type),
                        'code': None,
                        'description': None
                    }
                })
        
        return terms
    
    
    def _extract_from_chunk(self, text, threshold):
        """
        Extract terms from a single text chunk using the BioBERT neural model.
        Optimized for medical terminology extraction with BioBERT.
        
        Args:
            text (str): Text chunk
            threshold (float): Confidence threshold
            
        Returns:
            list: Extracted terms
        """
        try:
            # Ensure model is initialized
            if not self.model_manager.is_initialized:
                self.model_manager.initialize()
            
            # Apply BioBERT-specific preprocessing to optimize for medical terminology
            # This step cleans up the text while preserving medical terms
            if len(text) > 0:
                # Trim very long text to avoid token overflow
                if len(text) > 1500:  # BioBERT has a maximum context window of 512 tokens
                    logger.debug(f"Trimming long text from {len(text)} chars for BioBERT processing")
                    text = text[:1500]
                
                # Clean the text while preserving medical terminology patterns
                text = clean_text(text)
            
            # Tokenize input with BioBERT tokenizer
            # Using the tokenizer's ability to handle word pieces for medical terms
            inputs = self.model_manager.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,  # BioBERT's maximum sequence length
                return_offsets_mapping=True,
                padding="max_length",
                stride=50,  # Use stride for better handling of token boundaries
                return_overflowing_tokens=True  # Handle sequences longer than max_length
            )
            
            # Get token offsets for mapping back to original text
            offset_mapping = inputs.pop("offset_mapping")
            
            # Handle case where text was split into multiple sequences
            if offset_mapping.shape[0] > 1:
                logger.debug(f"Text was split into {offset_mapping.shape[0]} sequences for processing")
                all_terms = []
                
                # Process each sequence separately
                for seq_idx in range(offset_mapping.shape[0]):
                    # Extract the current sequence's offset mapping
                    seq_offset_mapping = offset_mapping[seq_idx].numpy()
                    
                    # Extract inputs for this sequence
                    seq_inputs = {
                        k: v[seq_idx:seq_idx+1] for k, v in inputs.items() 
                        if k != "overflow_to_sample_mapping"
                    }
                    
                    # Move inputs to device
                    seq_inputs = {k: v.to(self.model_manager.device) for k, v in seq_inputs.items()}
                    
                    # Perform inference on this sequence
                    with torch.no_grad():
                        outputs = self.model_manager.model(**seq_inputs)
                    
                    # Get predictions
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=2)
                    predictions = predictions.cpu().numpy()[0]
                    
                    # Process predictions for this sequence
                    sequence_terms = self._process_predictions(
                        text, 
                        predictions, 
                        seq_offset_mapping, 
                        threshold
                    )
                    
                    all_terms.extend(sequence_terms)
                
                # Consolidate and deduplicate terms from all sequences
                return consolidate_term_predictions(all_terms)
            else:
                # Single sequence processing (common case)
                offset_mapping = offset_mapping.numpy()[0]
                
                # Move inputs to device
                inputs = {k: v.to(self.model_manager.device) for k, v in inputs.items()}
                
                # Perform inference
                with torch.no_grad():
                    outputs = self.model_manager.model(**inputs)
                
                # Get predictions with softmax to convert logits to probabilities
                predictions = torch.nn.functional.softmax(outputs.logits, dim=2)
                predictions = predictions.cpu().numpy()[0]
                
                # Process predictions to get medical terms
                terms = self._process_predictions(
                    text, 
                    predictions, 
                    offset_mapping, 
                    threshold
                )
                
                return terms
        except Exception as e:
            logger.error(f"Error extracting from chunk with BioBERT: {str(e)}", exc_info=True)
            return []
    
    def _process_predictions(self, text, predictions, offsets, threshold):
        """
        Convert model predictions to term objects.
        
        Args:
            text (str): Original text
            predictions (numpy.ndarray): Model predictions
            offsets (numpy.ndarray): Token offsets
            threshold (float): Confidence threshold
            
        Returns:
            list: Extracted terms
        """
        terms = []
        prev_term = None
        term_start = None
        term_text = ""
        term_confidences = []
        
        entity_labels = self.model_manager.get_entity_labels()
        
        for idx, (offset, pred) in enumerate(zip(offsets, predictions)):
            # Skip special tokens and padding
            if offset[0] == offset[1]:
                continue
                
            # Get predicted label and confidence
            label_id = pred.argmax()
            confidence = float(pred[label_id])
            label = entity_labels[label_id]
            
            # Skip 'O' (Outside) label or low confidence predictions
            if label == 'O' or confidence < threshold:
                if prev_term:
                    # Add completed term
                    avg_confidence = sum(term_confidences) / len(term_confidences)
                    terms.append({
                        'text': term_text,
                        'type': prev_term,
                        'start': term_start,
                        'end': offset[0],
                        'confidence': avg_confidence,
                        'terminology': {
                            'mapped': False,
                            'vocabulary': self._get_vocabulary_for_type(prev_term),
                            'code': None,
                            'description': None
                        }
                    })
                    prev_term = None
                    term_text = ""
                    term_confidences = []
                continue
            
            # Handle B- (Beginning) labels
            if label.startswith('B-'):
                if prev_term:
                    # Add completed term
                    avg_confidence = sum(term_confidences) / len(term_confidences)
                    terms.append({
                        'text': term_text,
                        'type': prev_term,
                        'start': term_start,
                        'end': offset[0],
                        'confidence': avg_confidence,
                        'terminology': {
                            'mapped': False,
                            'vocabulary': self._get_vocabulary_for_type(prev_term),
                            'code': None,
                            'description': None
                        }
                    })
                
                # Start new term
                term_start = offset[0]
                term_text = text[offset[0]:offset[1]]
                prev_term = label[2:]  # Remove 'B-' prefix
                term_confidences = [confidence]
                
            # Handle I- (Inside) labels
            elif label.startswith('I-') and prev_term == label[2:]:
                # Continue current term
                term_text += text[offset[0]:offset[1]]
                term_confidences.append(confidence)
            else:
                # Handle unexpected transition
                if prev_term:
                    avg_confidence = sum(term_confidences) / len(term_confidences)
                    terms.append({
                        'text': term_text,
                        'type': prev_term,
                        'start': term_start,
                        'end': offset[0],
                        'confidence': avg_confidence,
                        'terminology': {
                            'mapped': False,
                            'vocabulary': self._get_vocabulary_for_type(prev_term),
                            'code': None,
                            'description': None
                        }
                    })
                
                # Start new term
                term_start = offset[0]
                term_text = text[offset[0]:offset[1]]
                prev_term = label[2:] if (label.startswith('B-') or label.startswith('I-')) else label
                term_confidences = [confidence]
        
        # Add final term if exists
        if prev_term and term_start is not None:
            avg_confidence = sum(term_confidences) / len(term_confidences)
            terms.append({
                'text': term_text,
                'type': prev_term,
                'start': term_start,
                'end': len(text),
                'confidence': avg_confidence,
                'terminology': {
                    'mapped': False,
                    'vocabulary': self._get_vocabulary_for_type(prev_term),
                    'code': None,
                    'description': None
                }
            })
        
        return terms
    
    def _get_vocabulary_for_type(self, term_type):
        """
        Determine the appropriate terminology vocabulary for a given term type.
        
        Args:
            term_type (str): The type of term
            
        Returns:
            str: Vocabulary name
        """
        vocab_mapping = {
            'CONDITION': 'SNOMED CT',
            'MEDICATION': 'RxNorm',
            'PROCEDURE': 'SNOMED CT',
            'LAB_TEST': 'LOINC',
            'OBSERVATION': 'SNOMED CT'
        }
        return vocab_mapping.get(term_type, 'SNOMED CT')
    
    def _resolve_overlapping_terms(self, terms):
        """
        Resolve overlapping term predictions by selecting the highest confidence predictions.
        
        Args:
            terms (list): List of extracted terms
            
        Returns:
            list: Non-overlapping term list
        """
        if not terms:
            return []
            
        # Sort terms by confidence (descending) then by length (descending)
        sorted_terms = sorted(
            terms, 
            key=lambda e: (e['confidence'], e['end'] - e['start']), 
            reverse=True
        )
        
        # Keep track of non-overlapping terms
        result = []
        covered_ranges = []
        
        for term in sorted_terms:
            start = term['start']
            end = term['end']
            
            # Check if this term overlaps with any existing covered range
            overlapping = False
            for range_start, range_end in covered_ranges:
                # Check for overlap
                if not (end <= range_start or start >= range_end):
                    overlapping = True
                    break
            
            if not overlapping:
                # Add to results and mark range as covered
                result.append(term)
                covered_ranges.append((start, end))
        
        # Sort final terms by position
        return sorted(result, key=lambda e: e['start'])
    
    def get_stats(self):
        """
        Get statistics about the term extractor.
        
        Returns:
            dict: Statistics about extraction, caching, and terminology mapping
        """
        stats = {
            'model_id': self.model_id,
            'offline_mode': self.offline_mode,
            'use_cache': self.use_cache,
            'confidence_threshold': self.confidence_threshold,
            'use_terminology': self.use_terminology
        }
        
        # Add cache stats if available
        if self.use_cache and self.cache:
            cache_stats = self.cache.get_stats()
            stats['cache'] = cache_stats
        
        # Add terminology mapper stats if available
        if self.use_terminology and self.terminology_mapper:
            terminology_stats = self.terminology_mapper.get_stats()
            stats['terminology'] = terminology_stats
        
        return stats