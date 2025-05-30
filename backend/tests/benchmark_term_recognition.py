"""
Benchmark tests for the term recognition engine.
Measures performance metrics like speed, accuracy, and memory usage.
"""

import os
import sys
import time
import unittest
import logging
import gc
import resource
from typing import Dict, List, Any, Tuple
import json

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from app.models.model_loader import ModelManager
from app.extractors.term_extractor import TermExtractor
from app.models.preprocessing import prepare_for_biobert

# Import test data
from test_data import SAMPLE_TEXTS, EXPECTED_TERM_TYPES, BENCHMARK_TEXT

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BenchmarkTermRecognition(unittest.TestCase):
    """Benchmark tests for term recognition functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up benchmark resources before any tests run."""
        # Initialize model manager
        cls.model_manager = ModelManager()
        cls.model_manager.initialize()
        
        # Create both offline and online extractors for comparison
        cls.offline_extractor = TermExtractor(
            cls.model_manager,
            use_cache=False,
            offline_mode=True,
            confidence_threshold=0.6
        )
        
        # Create BioBERT extractor if possible
        try:
            cls.biobert_extractor = TermExtractor(
                cls.model_manager,
                use_cache=False,
                offline_mode=False,
                confidence_threshold=0.6
            )
        except Exception as e:
            logger.warning(f"BioBERT extractor initialization failed: {e}")
            cls.biobert_extractor = None
        
        # Create results directory if it doesn't exist
        cls.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'benchmark_results')
        os.makedirs(cls.results_dir, exist_ok=True)
        
        # Get current timestamp for results
        from datetime import datetime
        cls.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _measure_memory_usage(self) -> int:
        """Measure current memory usage in KB."""
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    
    def _run_extraction_benchmark(self, 
                                extractor: TermExtractor, 
                                text: str, 
                                iterations: int = 3) -> Dict[str, Any]:
        """
        Run benchmark on term extraction.
        
        Args:
            extractor: The term extractor to benchmark
            text: Text to process
            iterations: Number of iterations to run
            
        Returns:
            Dict with benchmark results
        """
        # Force garbage collection before benchmark
        gc.collect()
        
        # Measure starting memory
        start_memory = self._measure_memory_usage()
        
        # Run extraction multiple times and measure performance
        durations = []
        term_counts = []
        
        for i in range(iterations):
            start_time = time.time()
            terms = extractor.extract_terms(text)
            duration = time.time() - start_time
            
            durations.append(duration)
            term_counts.append(len(terms))
            
            # Log iteration results
            logger.info(f"Iteration {i+1}/{iterations}: {len(terms)} terms extracted in {duration:.3f}s")
        
        # Calculate average performance
        avg_duration = sum(durations) / len(durations)
        avg_term_count = sum(term_counts) / len(term_counts)
        
        # Measure memory usage
        end_memory = self._measure_memory_usage()
        memory_used = end_memory - start_memory
        
        # Prepare results
        chars_per_second = len(text) / avg_duration if avg_duration > 0 else 0
        terms_per_second = avg_term_count / avg_duration if avg_duration > 0 else 0
        
        return {
            'text_length': len(text),
            'avg_duration': avg_duration,
            'avg_term_count': avg_term_count,
            'memory_used_kb': memory_used,
            'chars_per_second': chars_per_second,
            'terms_per_second': terms_per_second,
            'iterations': iterations,
            'durations': durations,
            'term_counts': term_counts
        }
    
    def test_benchmark_short_text(self):
        """Benchmark term extraction on short text."""
        # Get a short sample text
        text = SAMPLE_TEXTS['general_medical_history']
        
        # Run benchmark for offline mode
        logger.info("\n--- Benchmarking short text with pattern matching ---")
        offline_results = self._run_extraction_benchmark(self.offline_extractor, text)
        
        # Run benchmark for BioBERT if available
        biobert_results = None
        if self.biobert_extractor and not self.biobert_extractor.offline_mode:
            logger.info("\n--- Benchmarking short text with BioBERT model ---")
            biobert_results = self._run_extraction_benchmark(self.biobert_extractor, text)
        
        # Save results
        self._save_benchmark_results(
            'short_text',
            offline_results,
            biobert_results
        )
        
        # Verify performance meets requirements
        self.assertLess(offline_results['avg_duration'], 1.0, 
                      "Short text extraction should take less than 1 second")
    
    def test_benchmark_medium_text(self):
        """Benchmark term extraction on medium-sized text."""
        # Combine a few sample texts to make a medium-sized text
        text = (SAMPLE_TEXTS['general_medical_history'] + 
                SAMPLE_TEXTS['medication_list'] + 
                SAMPLE_TEXTS['lab_results'])
        
        # Run benchmark for offline mode
        logger.info("\n--- Benchmarking medium text with pattern matching ---")
        offline_results = self._run_extraction_benchmark(self.offline_extractor, text)
        
        # Run benchmark for BioBERT if available
        biobert_results = None
        if self.biobert_extractor and not self.biobert_extractor.offline_mode:
            logger.info("\n--- Benchmarking medium text with BioBERT model ---")
            biobert_results = self._run_extraction_benchmark(self.biobert_extractor, text)
        
        # Save results
        self._save_benchmark_results(
            'medium_text',
            offline_results,
            biobert_results
        )
        
        # Verify performance meets requirements
        self.assertLess(offline_results['avg_duration'], 3.0, 
                      "Medium text extraction should take less than 3 seconds")
    
    def test_benchmark_long_text(self):
        """Benchmark term extraction on long text."""
        # Use the long benchmark text
        text = BENCHMARK_TEXT
        
        # Run benchmark for offline mode
        logger.info("\n--- Benchmarking long text with pattern matching ---")
        offline_results = self._run_extraction_benchmark(self.offline_extractor, text, iterations=2)
        
        # Run benchmark for BioBERT if available
        biobert_results = None
        if self.biobert_extractor and not self.biobert_extractor.offline_mode:
            logger.info("\n--- Benchmarking long text with BioBERT model ---")
            biobert_results = self._run_extraction_benchmark(self.biobert_extractor, text, iterations=2)
        
        # Save results
        self._save_benchmark_results(
            'long_text',
            offline_results,
            biobert_results
        )
        
        # Verify performance meets requirements
        self.assertLess(offline_results['avg_duration'], 5.0, 
                      "Long text extraction should take less than 5 seconds")
    
    def test_benchmark_chunking(self):
        """Benchmark the text chunking performance."""
        text = BENCHMARK_TEXT
        
        # Force garbage collection
        gc.collect()
        
        # Measure chunking performance
        start_time = time.time()
        prepared = prepare_for_biobert(text)
        duration = time.time() - start_time
        
        # Log results
        chunk_count = len(prepared['chunks'])
        avg_chunk_size = sum(len(chunk['text']) for chunk in prepared['chunks']) / chunk_count
        
        logger.info(f"Chunking benchmark: {chunk_count} chunks created in {duration:.3f}s")
        logger.info(f"Average chunk size: {avg_chunk_size:.1f} characters")
        
        # Verify chunking meets requirements
        self.assertLess(duration, 1.0, "Chunking should take less than 1 second")
        
        # Save results
        results = {
            'text_length': len(text),
            'duration': duration,
            'chunk_count': chunk_count,
            'avg_chunk_size': avg_chunk_size,
            'chars_per_second': len(text) / duration if duration > 0 else 0,
            'chunks_per_second': chunk_count / duration if duration > 0 else 0
        }
        
        self._save_benchmark_results('chunking', results)
    
    def test_benchmark_terminology_mapping(self):
        """Benchmark terminology mapping performance."""
        # Skip if offline extractor doesn't have terminology mapping
        if not hasattr(self.offline_extractor, 'terminology_mapper') or not self.offline_extractor.terminology_mapper:
            logger.warning("Skipping terminology mapping benchmark - mapper not available")
            return
        
        # Use medium text for this benchmark
        text = SAMPLE_TEXTS['clinical_note']
        
        # First extract terms without mapping
        self.offline_extractor.use_terminology = False
        terms = self.offline_extractor.extract_terms(text)
        
        # Now benchmark the mapping process
        start_time = time.time()
        
        # Use the mapper directly
        mapped_terms = self.offline_extractor.terminology_mapper.map_terms(terms)
        
        duration = time.time() - start_time
        
        # Calculate statistics
        mapped_count = sum(1 for term in mapped_terms if term.get('terminology', {}).get('mapped', False))
        mapping_ratio = mapped_count / len(terms) if terms else 0
        
        logger.info(f"Terminology mapping: {mapped_count}/{len(terms)} terms mapped in {duration:.3f}s")
        logger.info(f"Mapping ratio: {mapping_ratio:.2%}")
        
        # Save results
        results = {
            'term_count': len(terms),
            'mapped_count': mapped_count,
            'mapping_ratio': mapping_ratio,
            'duration': duration,
            'terms_per_second': len(terms) / duration if duration > 0 else 0
        }
        
        self._save_benchmark_results('terminology_mapping', results)
        
        # Reset extractor state
        self.offline_extractor.use_terminology = True
    
    def _save_benchmark_results(self, test_name: str, *result_sets):
        """Save benchmark results to a JSON file."""
        try:
            # Combine results into a single object
            combined_results = {
                'test_name': test_name,
                'timestamp': self.timestamp,
                'results': []
            }
            
            # Add each result set
            for i, result_set in enumerate(result_sets):
                if result_set:
                    result_type = f"result_{i+1}" if i > 0 else "result"
                    combined_results['results'].append({
                        'type': result_type,
                        'data': result_set
                    })
            
            # Create a unique filename
            filename = f"benchmark_{test_name}_{self.timestamp}.json"
            file_path = os.path.join(self.results_dir, filename)
            
            # Write results to file
            with open(file_path, 'w') as f:
                json.dump(combined_results, f, indent=2)
            
            logger.info(f"Benchmark results saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving benchmark results: {e}")


if __name__ == '__main__':
    unittest.main()