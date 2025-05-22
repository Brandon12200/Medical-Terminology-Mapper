"""
Batch processing module for terminology mapping.

This module provides parallel and sequential batch processing functionality
for mapping large sets of medical terms to standardized terminologies.
"""

import logging
import time
import json
import csv
import os
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Tuple, Union, Callable

# Import mapper for direct use
from app.standards.terminology.mapper import TerminologyStandardMapper

# Configure logging
logger = logging.getLogger(__name__)

class BatchProcessor:
    """
    Batch processor for terminology mapping.
    
    This class handles processing large batches of terms efficiently,
    with support for both sequential and parallel processing.
    """
    
    def __init__(self, mapper: Optional[TerminologyStandardMapper] = None,
                threads: int = 0, threshold: float = 0.7):
        """
        Initialize the batch processor.
        
        Args:
            mapper: Optional TerminologyStandardMapper instance
            threads: Number of worker threads (0 = auto, -1 = sequential)
            threshold: Default confidence threshold for mapping
        """
        self.mapper = mapper or TerminologyStandardMapper()
        self.threshold = threshold
        
        # Determine number of workers
        if threads < 0:
            self.parallel = False
            self.workers = 1
        else:
            self.parallel = True
            if threads == 0:
                # Auto-detect: Use number of CPUs minus 1, minimum 1
                self.workers = max(1, multiprocessing.cpu_count() - 1)
            else:
                self.workers = threads
        
        logger.info(f"Batch processor initialized with {'parallel' if self.parallel else 'sequential'} "
                  f"processing using {self.workers} worker{'s' if self.workers > 1 else ''}")
    
    def process_terms(self, terms: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process a list of term dictionaries.
        
        Args:
            terms: List of term dictionaries, each containing at least 'text' field
            
        Returns:
            Tuple of (processed terms, summary statistics)
        """
        if not terms:
            return [], {'total_terms': 0, 'mapped_terms': 0, 'mapping_rate': 0.0, 'duration_ms': 0}
        
        start_time = time.time()
        
        if self.parallel and len(terms) > 10:
            results = self._process_parallel(terms)
        else:
            results = self._process_sequential(terms)
        
        duration = time.time() - start_time
        
        # Calculate summary statistics
        mapped_count = sum(1 for term in results if term.get('terminology', {}).get('mapped', False))
        mapping_rate = (mapped_count / len(results) * 100) if results else 0
        
        summary = {
            'total_terms': len(results),
            'mapped_terms': mapped_count,
            'mapping_rate': round(mapping_rate, 2),
            'duration_ms': round(duration * 1000, 2),
            'avg_time_per_term_ms': round((duration * 1000) / len(results), 2) if results else 0,
            'parallel': self.parallel,
            'workers': self.workers
        }
        
        logger.info(f"Processed {len(results)} terms with {mapped_count} mapped ({mapping_rate:.1f}%) "
                   f"in {duration:.2f}s")
        
        return results, summary
    
    def _process_sequential(self, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process terms sequentially.
        
        Args:
            terms: List of term dictionaries
            
        Returns:
            List of processed terms
        """
        processed_terms = []
        
        for i, term_dict in enumerate(terms):
            term_text = term_dict.get('text', '')
            term_type = term_dict.get('type', '')
            
            if not term_text:
                continue
            
            # Extract context if available
            context = self._extract_context(term_dict, terms)
            
            # Map the term
            try:
                result = self.mapper.map_term(term_text, term_type, context, self.threshold)
                
                # Update the original term dictionary
                term_dict['terminology'] = {
                    'mapped': result.get('mapped', False),
                    'vocabulary': result.get('vocabulary'),
                    'code': result.get('code'),
                    'description': result.get('display'),
                    'confidence': result.get('confidence', 0.0),
                    'match_type': result.get('match_type', None)
                }
                
                processed_terms.append(term_dict)
                
                # Log progress periodically
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(terms)} terms")
                
            except Exception as e:
                logger.error(f"Error processing term '{term_text}': {e}")
                # Add term with error info
                term_dict['terminology'] = {
                    'mapped': False,
                    'error': str(e)
                }
                processed_terms.append(term_dict)
        
        return processed_terms
    
    def _process_parallel(self, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process terms in parallel using multiple workers.
        
        Args:
            terms: List of term dictionaries
            
        Returns:
            List of processed terms
        """
        # Split terms into chunks for parallel processing
        chunk_size = max(10, len(terms) // self.workers)  # Minimum 10 terms per chunk
        term_chunks = [terms[i:i + chunk_size] for i in range(0, len(terms), chunk_size)]
        
        logger.info(f"Processing {len(terms)} terms in {len(term_chunks)} chunks using {self.workers} workers")
        
        # Define worker function for parallel processing
        def process_chunk(chunk):
            chunk_mapper = TerminologyStandardMapper()  # Create new mapper instance for each process
            results = []
            
            for term_dict in chunk:
                term_text = term_dict.get('text', '')
                term_type = term_dict.get('type', '')
                
                if not term_text:
                    continue
                
                try:
                    # Simple context extraction (limited in parallel mode)
                    context = None
                    
                    # Map the term
                    result = chunk_mapper.map_term(term_text, term_type, context, self.threshold)
                    
                    # Update term dictionary
                    term_dict['terminology'] = {
                        'mapped': result.get('mapped', False),
                        'vocabulary': result.get('vocabulary'),
                        'code': result.get('code'),
                        'description': result.get('display'),
                        'confidence': result.get('confidence', 0.0),
                        'match_type': result.get('match_type', None)
                    }
                    
                    results.append(term_dict)
                    
                except Exception as e:
                    logger.error(f"Error processing term '{term_text}' in worker: {e}")
                    term_dict['terminology'] = {
                        'mapped': False,
                        'error': str(e)
                    }
                    results.append(term_dict)
            
            chunk_mapper.close()  # Close the mapper to release resources
            return results
        
        # Process chunks in parallel
        all_results = []
        
        try:
            # Use Process pool for heavy processing with separate database connections
            with ProcessPoolExecutor(max_workers=self.workers) as executor:
                chunk_results = list(executor.map(process_chunk, term_chunks))
                
                # Flatten results
                for chunk_result in chunk_results:
                    all_results.extend(chunk_result)
                
        except Exception as e:
            logger.error(f"Error in parallel processing: {e}")
            logger.info("Falling back to sequential processing")
            return self._process_sequential(terms)
        
        return all_results
    
    def _extract_context(self, current_term: Dict[str, Any], 
                        all_terms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract context information from surrounding terms.
        
        Args:
            current_term: The current term being processed
            all_terms: All terms in the current batch
            
        Returns:
            Context information as a dictionary
        """
        context = {
            'surrounding_terms': [],
            'document_types': {}
        }
        
        try:
            # Get the current term's index
            current_index = -1
            for i, term in enumerate(all_terms):
                if term is current_term:
                    current_index = i
                    break
            
            if current_index >= 0:
                # Get surrounding terms (up to 2 before and 2 after)
                start_idx = max(0, current_index - 2)
                end_idx = min(len(all_terms), current_index + 3)
                
                surrounding = []
                for i in range(start_idx, end_idx):
                    if i != current_index:  # Skip the current term
                        surrounding.append({
                            'text': all_terms[i].get('text', ''),
                            'type': all_terms[i].get('type', ''),
                            'relative_position': i - current_index
                        })
                
                context['surrounding_terms'] = surrounding
            
            # Count term types in the document for context
            type_counts = {}
            for term in all_terms:
                term_type = term.get('type', '')
                if term_type:
                    type_counts[term_type] = type_counts.get(term_type, 0) + 1
            
            context['document_types'] = type_counts
            
        except Exception as e:
            logger.warning(f"Error extracting context: {e}")
        
        return context
    
    def process_file(self, input_file: str, output_file: Optional[str] = None,
                    input_format: str = 'csv', output_format: str = 'csv') -> Dict[str, Any]:
        """
        Process terms from a file and optionally write results to another file.
        
        Args:
            input_file: Path to input file
            output_file: Optional path to output file
            input_format: Format of input file ('csv', 'json', 'txt')
            output_format: Format of output file ('csv', 'json')
            
        Returns:
            Summary statistics dictionary
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Load terms from file
        terms = self._load_terms_from_file(input_file, input_format)
        
        if not terms:
            logger.warning(f"No terms found in {input_file}")
            return {'total_terms': 0, 'mapped_terms': 0, 'mapping_rate': 0.0, 'duration_ms': 0}
        
        # Process the terms
        results, summary = self.process_terms(terms)
        
        # Write results to output file if specified
        if output_file:
            self._write_results_to_file(results, summary, output_file, output_format)
            logger.info(f"Results written to {output_file}")
        
        return summary
    
    def _load_terms_from_file(self, file_path: str, file_format: str) -> List[Dict[str, Any]]:
        """
        Load terms from a file.
        
        Args:
            file_path: Path to the file
            file_format: Format of the file ('csv', 'json', 'txt')
            
        Returns:
            List of term dictionaries
        """
        terms = []
        
        try:
            if file_format.lower() == 'csv':
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Ensure 'text' field exists (may be named 'term')
                        if 'text' not in row and 'term' in row:
                            row['text'] = row.pop('term')
                        terms.append(row)
                        
            elif file_format.lower() == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle different JSON structures
                    if isinstance(data, list):
                        # List of terms
                        for item in data:
                            if isinstance(item, dict):
                                # Ensure 'text' field exists
                                if 'text' not in item and 'term' in item:
                                    item['text'] = item.pop('term')
                                terms.append(item)
                            elif isinstance(item, str):
                                # Simple list of term strings
                                terms.append({'text': item})
                    elif isinstance(data, dict):
                        # Dictionary with terms
                        if 'terms' in data and isinstance(data['terms'], list):
                            for item in data['terms']:
                                if isinstance(item, dict):
                                    if 'text' not in item and 'term' in item:
                                        item['text'] = item.pop('term')
                                    terms.append(item)
                                elif isinstance(item, str):
                                    terms.append({'text': item})
                        else:
                            # Single term dictionary
                            if 'text' not in data and 'term' in data:
                                data['text'] = data.pop('term')
                            terms.append(data)
                        
            elif file_format.lower() == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            terms.append({'text': line})
            
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
                
        except Exception as e:
            logger.error(f"Error loading terms from {file_path}: {e}")
            raise
        
        return terms
    
    def _write_results_to_file(self, results: List[Dict[str, Any]], summary: Dict[str, Any],
                             file_path: str, file_format: str) -> None:
        """
        Write results to a file.
        
        Args:
            results: List of processed terms
            summary: Summary statistics
            file_path: Path to output file
            file_format: Format of output file ('csv', 'json')
        """
        try:
            if file_format.lower() == 'csv':
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    # Write summary as comments
                    f.write('# Mapping Summary\n')
                    for key, value in summary.items():
                        f.write(f'# {key}: {value}\n')
                    f.write('#\n')
                    
                    # Write results as CSV
                    if results:
                        # Prepare flattened data for CSV
                        flattened_results = []
                        for result in results:
                            flat_result = result.copy()
                            
                            # Flatten terminology information
                            if 'terminology' in flat_result and isinstance(flat_result['terminology'], dict):
                                for k, v in flat_result['terminology'].items():
                                    flat_result[f'terminology_{k}'] = v
                                del flat_result['terminology']
                            
                            flattened_results.append(flat_result)
                        
                        # Get all field names
                        fieldnames = set()
                        for result in flattened_results:
                            fieldnames.update(result.keys())
                        
                        writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                        writer.writeheader()
                        writer.writerows(flattened_results)
                    else:
                        f.write('# No results found\n')
                        
            elif file_format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    output = {
                        'summary': summary,
                        'results': results
                    }
                    json.dump(output, f, indent=2)
                    
            else:
                raise ValueError(f"Unsupported output format: {file_format}")
                
        except Exception as e:
            logger.error(f"Error writing results to {file_path}: {e}")
            raise
    
    def close(self):
        """Close resources."""
        if self.mapper:
            self.mapper.close()