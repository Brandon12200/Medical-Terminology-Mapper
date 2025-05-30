"""
Text preprocessing module for Medical Terminology Mapper.
Optimizes text for BioBERT model processing and term extraction.
Adapted from the Clinical Protocol Extractor with terminology-specific optimizations.
"""

import re
import nltk
import logging
import unicodedata
import time
from typing import List, Dict, Any
from functools import lru_cache

# Configure logging
logger = logging.getLogger(__name__)

# Download NLTK data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading NLTK punkt tokenizer")
    nltk.download('punkt', quiet=True)

# Common medical terminology patterns to preserve during preprocessing
MEDICAL_PATTERNS = [
    # Common medical dosages and units
    r'\d+(?:\.\d+)?\s*(?:mg|mcg|g|kg|ml|l|mmol|µg|IU|mg/dl|mmHg|cm|mm)',
    # Lab values with ranges
    r'\d+(?:\.\d+)?\s*(?:-|to|–)\s*\d+(?:\.\d+)?\s*',
    # Medication frequencies
    r'(?:once|twice|three times|four times)\s+(?:daily|weekly|monthly|a day)',
    # Medical abbreviations
    r'\b(?:b\.i\.d\.|t\.i\.d\.|q\.i\.d\.|q\.d\.|p\.r\.n\.|a\.c\.|p\.c\.|q\.[0-9]+h)\b'
]

# Precompile regular expressions for performance
RE_CONTROL_CHARS = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
RE_MULTI_SPACES = re.compile(r' +')
RE_MULTI_NEWLINES = re.compile(r'\n+')
RE_LINE_TRIM = re.compile(r'^\s+|\s+$', re.MULTILINE)
RE_PERIOD_UPPERCASE = re.compile(r'\.([A-Z])')
RE_SPACE_PUNCT = re.compile(r' ([.,;:!?)])')
RE_PUNCT_LETTER = re.compile(r'([.,;:!?)])([A-Za-z])')
RE_MEDICAL_PATTERNS = [re.compile(pattern) for pattern in MEDICAL_PATTERNS]

@lru_cache(maxsize=128)
def clean_text(text: str) -> str:
    """
    Clean and normalize text for processing with caching for repeated calls.
    Optimized for medical terminology preservation.
    
    Args:
        text (str): Raw input text
        
    Returns:
        str: Cleaned and normalized text
    """
    try:
        if not text:
            return ""
        
        # Save medical patterns to restore after cleaning
        saved_patterns = {}
        for i, pattern in enumerate(RE_MEDICAL_PATTERNS):
            for match in pattern.finditer(text):
                # Save matched text with unique placeholder
                placeholder = f"__MED_TERM_{i}_{match.start()}__"
                saved_patterns[placeholder] = match.group(0)
                # Replace with placeholder
                text = text[:match.start()] + placeholder + text[match.end():]
            
        # Remove null bytes and other control characters
        text = RE_CONTROL_CHARS.sub('', text)
        
        # Normalize Unicode characters (NFKC form)
        text = unicodedata.normalize('NFKC', text)
        
        # Replace multiple spaces with single space
        text = RE_MULTI_SPACES.sub(' ', text)
        
        # Normalize newlines
        text = RE_MULTI_NEWLINES.sub('\n', text)
        
        # Remove excessive whitespace at beginning and end of lines
        text = RE_LINE_TRIM.sub('', text)
        
        # Standardize quotation marks
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Normalize dashes
        text = text.replace('–', '-').replace('—', '-')
        
        # Add space after periods if not present and followed by uppercase letter
        text = RE_PERIOD_UPPERCASE.sub(r'. \1', text)
        
        # Fix space before punctuation
        text = RE_SPACE_PUNCT.sub(r'\1', text)
        
        # Ensure space after punctuation if followed by a letter
        text = RE_PUNCT_LETTER.sub(r'\1 \2', text)
        
        # Restore saved medical patterns
        for placeholder, original in saved_patterns.items():
            text = text.replace(placeholder, original)
        
        return text
    except Exception as e:
        logger.error(f"Error cleaning text: {str(e)}")
        # Return original text if an error occurs
        return text

def chunk_document(text: str, max_length: int = 500, overlap: int = 50, optimize_for_biobert: bool = True) -> List[Dict[str, Any]]:
    """
    Split document into overlapping chunks for processing by the BioBERT model.
    Optimized for medical text and terminology preservation.
    
    Args:
        text (str): Input text
        max_length (int): Maximum chunk length (adjusted for BioBERT's context window)
        overlap (int): Overlap between chunks
        optimize_for_biobert (bool): Whether to optimize chunking for BioBERT model
        
    Returns:
        List[Dict[str, Any]]: List of chunks with text and position offsets
    """
    start_time = time.time()
    
    try:
        # For very short documents, return as single chunk
        if len(text) <= max_length:
            return [{'text': text, 'offset': 0}]
            
        # If optimizing for BioBERT, adjust chunk sizes to better fit model
        if optimize_for_biobert:
            # BioBERT works best with chunks around 400-450 tokens
            # which is roughly equivalent to 300-350 words
            max_length = min(max_length, 450)
            # Ensure adequate overlap to catch terms that might span chunk boundaries
            overlap = max(overlap, min(100, max_length // 5))
            
        chunks = []
        start = 0
        text_length = len(text)
        
        # Find potential boundary positions for better chunking
        boundary_positions = set()
        
        # Add paragraph boundaries (double newlines)
        for match in re.finditer(r'\n\s*\n', text):
            boundary_positions.add(match.start())
        
        # Add sentence boundaries using NLTK
        try:
            sentence_detector = nltk.data.load('tokenizers/punkt/english.pickle')
            # Optimize by scanning sections of text
            for pos in range(0, text_length, max_length // 2):
                section_end = min(pos + max_length, text_length)
                section_text = text[pos:section_end]
                for sentence in sentence_detector.tokenize(section_text):
                    sent_pos = pos + section_text.find(sentence) + len(sentence)
                    if sent_pos < text_length:
                        boundary_positions.add(sent_pos)
        except Exception as e:
            logger.warning(f"Error in sentence boundary detection: {e}. Falling back to basic chunking.")
        
        # Add medical term boundaries where possible
        for pattern in RE_MEDICAL_PATTERNS:
            for match in pattern.finditer(text):
                # Add positions after medical terms
                boundary_positions.add(match.end())
        
        # Sort boundary positions
        sorted_boundaries = sorted(boundary_positions)
        
        while start < text_length:
            # Calculate end position for this chunk
            end = min(start + max_length, text_length)
            
            # Try to find a natural boundary for cleaner splitting
            if end < text_length:
                # Find closest boundary position that is near the end point
                closest_boundary = None
                min_distance = max_length // 4  # Maximum distance to look back
                
                for boundary in sorted_boundaries:
                    if boundary > start and boundary < end:
                        # Prefer boundaries closer to end but not too far back
                        if end - boundary < min_distance:
                            closest_boundary = boundary
                            min_distance = end - boundary
                
                if closest_boundary:
                    end = closest_boundary
                else:
                    # Fallback to sentence-ending punctuation if no other boundary found
                    for i in range(end, max(end - max_length // 10, start), -1):
                        if i >= text_length:
                            continue
                        if text[i] in '.!?' and (i + 1 >= text_length or text[i + 1].isspace()):
                            end = i + 1
                            break
            
            # Create chunk
            chunks.append({
                'text': text[start:end],
                'offset': start
            })
            
            # Move start position for next chunk, with overlap
            start = max(start + 1, end - overlap)
        
        # Performance tracking
        duration = time.time() - start_time
        avg_chunk_size = sum(len(chunk['text']) for chunk in chunks) / len(chunks)
        logger.debug(f"Split document into {len(chunks)} chunks in {duration:.3f}s (avg size: {avg_chunk_size:.1f} chars)")
        
        return chunks
    except Exception as e:
        logger.error(f"Error in document chunking: {str(e)}")
        # Fallback to simple chunking without considering boundaries
        chunks = []
        for i in range(0, len(text), max_length - overlap):
            end = min(i + max_length, len(text))
            chunks.append({
                'text': text[i:end],
                'offset': i
            })
        return chunks

def prepare_for_biobert(text: str, max_chunk_length: int = 450) -> Dict[str, Any]:
    """
    Prepare text specifically for BioBERT processing.
    Optimizes text cleaning and chunking for medical terminology extraction.
    
    Args:
        text (str): Raw input text
        max_chunk_length (int): Maximum length for each text chunk
        
    Returns:
        Dict[str, Any]: Prepared text with chunks ready for BioBERT processing
    """
    try:
        start_time = time.time()
        
        # Clean and normalize text
        cleaned_text = clean_text(text)
        
        # Chunk document optimized for BioBERT
        chunks = chunk_document(
            cleaned_text, 
            max_length=max_chunk_length,
            overlap=100,  # Larger overlap for better term recognition
            optimize_for_biobert=True
        )
        
        # Store original text length for reference
        original_length = len(text)
        cleaned_length = len(cleaned_text)
        
        # Performance tracking
        duration = time.time() - start_time
        avg_chunk_size = sum(len(chunk['text']) for chunk in chunks) / len(chunks) if chunks else 0
        
        logger.info(f"Prepared text for BioBERT in {duration:.3f}s: {len(chunks)} chunks, avg size {avg_chunk_size:.1f} chars")
        
        return {
            'text': cleaned_text,
            'chunks': chunks,
            'stats': {
                'original_length': original_length,
                'cleaned_length': cleaned_length,
                'chunk_count': len(chunks),
                'avg_chunk_size': avg_chunk_size,
                'processing_time': duration
            }
        }
        
    except Exception as e:
        logger.error(f"Error preparing text for BioBERT: {str(e)}")
        # Return minimal result on error
        return {
            'text': text,
            'chunks': chunk_document(text, optimize_for_biobert=False),
            'error': str(e)
        }

def optimize_tokens_for_biobert(tokens: List[str]) -> List[str]:
    """
    Optimize tokenization specifically for BioBERT's vocabulary.
    Improves handling of medical terms that might be split across multiple tokens.
    
    Args:
        tokens (List[str]): Initial tokenized text
        
    Returns:
        List[str]: Optimized tokens for BioBERT
    """
    optimized = []
    i = 0
    
    while i < len(tokens):
        current = tokens[i]
        
        # Check for common medical prefixes/suffixes that should be kept together
        if i < len(tokens) - 1:
            next_token = tokens[i+1]
            
            # Handle common medical prefixes (hyper-, anti-, etc.)
            if current.lower() in ['hyper', 'hypo', 'anti', 'neo', 'pre', 'post', 'sub', 'peri'] and next_token.startswith('-'):
                # Combine prefix with next token
                optimized.append(current + next_token)
                i += 2
                continue
                
            # Handle dosage patterns
            if current.isdigit() and next_token.lower() in ['mg', 'g', 'mcg', 'ml', 'l', 'mmol', 'kg']:
                # Combine number with unit
                optimized.append(current + next_token)
                i += 2
                continue
        
        # If no special case, keep token as is
        optimized.append(current)
        i += 1
    
    return optimized

def consolidate_term_predictions(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Consolidate overlapping term predictions from multiple chunks.
    Resolves conflicts when the same term appears in overlapping chunks.
    
    Args:
        predictions (List[Dict[str, Any]]): List of term predictions from all chunks
        
    Returns:
        List[Dict[str, Any]]: Consolidated term predictions
    """
    if not predictions:
        return []
    
    # Sort predictions by confidence (descending) then by length (descending)
    sorted_preds = sorted(
        predictions, 
        key=lambda p: (p.get('confidence', 0), p.get('end', 0) - p.get('start', 0)), 
        reverse=True
    )
    
    # Keep track of non-overlapping terms
    consolidated = []
    covered_ranges = []
    
    for pred in sorted_preds:
        start = pred.get('start', 0)
        end = pred.get('end', 0)
        
        # Skip invalid predictions
        if end <= start:
            continue
        
        # Check if this prediction overlaps with any existing covered range
        overlapping = False
        for range_start, range_end in covered_ranges:
            # Check for overlap
            if not (end <= range_start or start >= range_end):
                overlapping = True
                break
        
        if not overlapping:
            # Add to results and mark range as covered
            consolidated.append(pred)
            covered_ranges.append((start, end))
    
    # Sort final terms by position
    return sorted(consolidated, key=lambda p: p.get('start', 0))