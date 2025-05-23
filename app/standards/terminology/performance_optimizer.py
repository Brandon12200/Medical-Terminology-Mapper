"""
Performance Optimization Module for Medical Terminology Mapper

This module provides performance optimizations including advanced caching,
parallel processing, and database query optimization.
Week 6 Implementation - Performance Optimization.
"""

import time
import logging
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass
from functools import wraps, lru_cache
import sqlite3
import json
import hashlib
from pathlib import Path

from app.extractors.term_cache import get_term_cache, TermCache
from app.standards.terminology.custom_mapping_rules import CustomMappingRulesEngine

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for optimization monitoring."""
    execution_time: float
    cache_hits: int
    cache_misses: int
    parallel_tasks: int
    database_queries: int
    memory_usage: float
    throughput: float  # items per second


class QueryOptimizer:
    """Database query optimization for terminology lookups."""
    
    def __init__(self, db_paths: Dict[str, str]):
        """
        Initialize query optimizer.
        
        Args:
            db_paths: Dictionary mapping system names to database paths
        """
        self.db_paths = db_paths
        self.connection_pool = {}
        self.query_cache = {}
        self.prepared_statements = {}
        self._lock = threading.RLock()
        
    def get_connection(self, system: str) -> sqlite3.Connection:
        """Get optimized database connection for a system."""
        with self._lock:
            if system not in self.connection_pool:
                if system not in self.db_paths:
                    raise ValueError(f"Unknown system: {system}")
                
                conn = sqlite3.connect(
                    self.db_paths[system],
                    check_same_thread=False,
                    timeout=30.0
                )
                
                # Optimize connection
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.execute("PRAGMA mmap_size=268435456")  # 256MB
                
                self.connection_pool[system] = conn
                
            return self.connection_pool[system]
    
    def execute_optimized_query(self, system: str, query: str, 
                              params: Tuple = None) -> List[Dict[str, Any]]:
        """Execute an optimized database query with caching."""
        # Create cache key
        cache_key = hashlib.md5(f"{system}:{query}:{params}".encode()).hexdigest()
        
        # Check query cache
        if cache_key in self.query_cache:
            cached_result, timestamp = self.query_cache[cache_key]
            # Cache valid for 5 minutes
            if time.time() - timestamp < 300:
                return cached_result
        
        # Execute query
        conn = self.get_connection(system)
        conn.row_factory = sqlite3.Row
        
        try:
            if params:
                cursor = conn.execute(query, params)
            else:
                cursor = conn.execute(query)
            
            results = [dict(row) for row in cursor.fetchall()]
            
            # Cache results
            self.query_cache[cache_key] = (results, time.time())
            
            # Limit cache size
            if len(self.query_cache) > 1000:
                # Remove oldest entries
                oldest_keys = sorted(self.query_cache.keys(), 
                                   key=lambda k: self.query_cache[k][1])[:100]
                for key in oldest_keys:
                    del self.query_cache[key]
            
            return results
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []
    
    def prepare_batch_queries(self, system: str, base_query: str, 
                            param_sets: List[Tuple]) -> List[Dict[str, Any]]:
        """Execute batch queries efficiently."""
        if not param_sets:
            return []
        
        # For large batches, use batch processing
        if len(param_sets) > 100:
            # Split into chunks
            chunk_size = 100
            chunks = [param_sets[i:i + chunk_size] 
                     for i in range(0, len(param_sets), chunk_size)]
            
            all_results = []
            for chunk in chunks:
                # Create batch query with IN clause
                placeholders = ','.join(['?' for _ in chunk])
                batch_query = base_query.replace('?', f'({placeholders})')
                flat_params = tuple(param for params in chunk for param in params)
                
                results = self.execute_optimized_query(system, batch_query, flat_params)
                all_results.extend(results)
            
            return all_results
        else:
            # Execute individual queries (cached)
            all_results = []
            for params in param_sets:
                results = self.execute_optimized_query(system, base_query, params)
                all_results.extend(results)
            return all_results
    
    def close_connections(self):
        """Close all database connections."""
        with self._lock:
            for conn in self.connection_pool.values():
                conn.close()
            self.connection_pool.clear()


class ParallelProcessor:
    """Parallel processing for terminology mapping operations."""
    
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        """
        Initialize parallel processor.
        
        Args:
            max_workers: Maximum number of worker threads/processes
            use_processes: Whether to use processes instead of threads
        """
        self.max_workers = max_workers or min(32, (multiprocessing.cpu_count() or 1) + 4)
        self.use_processes = use_processes
        self.metrics = PerformanceMetrics(0, 0, 0, 0, 0, 0, 0)
        
    def map_terms_parallel(self, terms: List[str], mapping_function: Callable,
                          chunk_size: Optional[int] = None, 
                          context_data: Optional[Dict] = None) -> List[Any]:
        """
        Map terms in parallel using the provided mapping function.
        
        Args:
            terms: List of terms to map
            mapping_function: Function to map each term
            chunk_size: Size of chunks for processing
            context_data: Optional context data for mapping
            
        Returns:
            List of mapping results
        """
        if not terms:
            return []
        
        start_time = time.time()
        
        # Determine optimal chunk size
        if chunk_size is None:
            chunk_size = max(1, len(terms) // self.max_workers)
        
        # Create chunks
        chunks = [terms[i:i + chunk_size] for i in range(0, len(terms), chunk_size)]
        
        results = []
        
        if self.use_processes:
            # Use process pool for CPU-intensive work
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_chunk = {
                    executor.submit(self._process_chunk, chunk, mapping_function, context_data): chunk
                    for chunk in chunks
                }
                
                for future in as_completed(future_to_chunk):
                    try:
                        chunk_results = future.result()
                        results.extend(chunk_results)
                    except Exception as e:
                        logger.error(f"Error processing chunk: {e}")
                        # Add empty results for failed chunk
                        chunk = future_to_chunk[future]
                        results.extend([None] * len(chunk))
        else:
            # Use thread pool for I/O-bound work
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_chunk = {
                    executor.submit(self._process_chunk, chunk, mapping_function, context_data): chunk
                    for chunk in chunks
                }
                
                for future in as_completed(future_to_chunk):
                    try:
                        chunk_results = future.result()
                        results.extend(chunk_results)
                    except Exception as e:
                        logger.error(f"Error processing chunk: {e}")
                        # Add empty results for failed chunk
                        chunk = future_to_chunk[future]
                        results.extend([None] * len(chunk))
        
        # Update metrics
        execution_time = time.time() - start_time
        self.metrics.execution_time = execution_time
        self.metrics.parallel_tasks = len(chunks)
        self.metrics.throughput = len(terms) / execution_time if execution_time > 0 else 0
        
        logger.info(f"Parallel processing completed: {len(terms)} terms in {execution_time:.2f}s "
                   f"({self.metrics.throughput:.1f} terms/sec)")
        
        return results
    
    def _process_chunk(self, chunk: List[str], mapping_function: Callable,
                      context_data: Optional[Dict] = None) -> List[Any]:
        """Process a chunk of terms."""
        results = []
        for term in chunk:
            try:
                if context_data:
                    result = mapping_function(term, **context_data)
                else:
                    result = mapping_function(term)
                results.append(result)
            except Exception as e:
                logger.error(f"Error mapping term '{term}': {e}")
                results.append(None)
        return results


class AdvancedCache:
    """Advanced caching system with multiple cache levels and strategies."""
    
    def __init__(self, term_cache: Optional[TermCache] = None):
        """Initialize advanced cache."""
        self.term_cache = term_cache or get_term_cache()
        self.mapping_cache = {}
        self.rule_cache = {}
        self.stats_cache = {}
        self._lock = threading.RLock()
        
        # Cache configuration
        self.max_mapping_cache_size = 5000
        self.max_rule_cache_size = 1000
        
    def get_cached_mapping(self, term: str, system: str, 
                          cache_key_params: Dict = None) -> Optional[Dict[str, Any]]:
        """Get cached mapping result."""
        with self._lock:
            # Create cache key
            cache_params = cache_key_params or {}
            cache_key = f"{term}:{system}:{hash(str(sorted(cache_params.items())))}"
            
            if cache_key in self.mapping_cache:
                cached_data, timestamp = self.mapping_cache[cache_key]
                # Cache valid for 1 hour
                if time.time() - timestamp < 3600:
                    return cached_data
                else:
                    del self.mapping_cache[cache_key]
            
            return None
    
    def cache_mapping(self, term: str, system: str, result: Dict[str, Any],
                     cache_key_params: Dict = None):
        """Cache mapping result."""
        with self._lock:
            cache_params = cache_key_params or {}
            cache_key = f"{term}:{system}:{hash(str(sorted(cache_params.items())))}"
            
            self.mapping_cache[cache_key] = (result, time.time())
            
            # Manage cache size
            if len(self.mapping_cache) > self.max_mapping_cache_size:
                # Remove oldest entries
                oldest_keys = sorted(self.mapping_cache.keys(),
                                   key=lambda k: self.mapping_cache[k][1])[:100]
                for key in oldest_keys:
                    del self.mapping_cache[key]
    
    def get_cached_rules(self, term: str, context: Dict = None) -> Optional[List]:
        """Get cached custom rules for a term."""
        with self._lock:
            context_key = hash(str(sorted((context or {}).items())))
            cache_key = f"rules:{term}:{context_key}"
            
            if cache_key in self.rule_cache:
                cached_rules, timestamp = self.rule_cache[cache_key]
                # Rule cache valid for 30 minutes
                if time.time() - timestamp < 1800:
                    return cached_rules
                else:
                    del self.rule_cache[cache_key]
            
            return None
    
    def cache_rules(self, term: str, rules: List, context: Dict = None):
        """Cache custom rules for a term."""
        with self._lock:
            context_key = hash(str(sorted((context or {}).items())))
            cache_key = f"rules:{term}:{context_key}"
            
            self.rule_cache[cache_key] = (rules, time.time())
            
            # Manage cache size
            if len(self.rule_cache) > self.max_rule_cache_size:
                oldest_keys = sorted(self.rule_cache.keys(),
                                   key=lambda k: self.rule_cache[k][1])[:50]
                for key in oldest_keys:
                    del self.rule_cache[key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        term_stats = self.term_cache.get_stats()
        
        return {
            'term_cache': term_stats,
            'mapping_cache_size': len(self.mapping_cache),
            'rule_cache_size': len(self.rule_cache),
            'total_memory_entries': (len(self.mapping_cache) + 
                                   len(self.rule_cache) + 
                                   term_stats.get('memory_entries', 0))
        }
    
    def clear_expired_entries(self):
        """Clear expired cache entries."""
        current_time = time.time()
        
        with self._lock:
            # Clear expired mapping cache entries
            expired_mapping_keys = [
                key for key, (_, timestamp) in self.mapping_cache.items()
                if current_time - timestamp > 3600
            ]
            for key in expired_mapping_keys:
                del self.mapping_cache[key]
            
            # Clear expired rule cache entries
            expired_rule_keys = [
                key for key, (_, timestamp) in self.rule_cache.items()
                if current_time - timestamp > 1800
            ]
            for key in expired_rule_keys:
                del self.rule_cache[key]
        
        logger.info(f"Cleared {len(expired_mapping_keys)} expired mapping entries "
                   f"and {len(expired_rule_keys)} expired rule entries")


def performance_monitor(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = 0  # Could integrate with psutil for actual memory monitoring
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            logger.error(f"Performance monitoring: {func.__name__} failed: {e}")
            result = None
            success = False
        
        execution_time = time.time() - start_time
        
        # Log performance metrics
        logger.debug(f"Performance: {func.__name__} - "
                    f"Time: {execution_time:.3f}s, Success: {success}")
        
        # Could store metrics in a performance database here
        
        if not success:
            raise
        
        return result
    
    return wrapper


class PerformanceOptimizer:
    """Main performance optimization coordinator."""
    
    def __init__(self, config: Dict = None):
        """Initialize performance optimizer with configuration."""
        self.config = config or {}
        
        # Initialize components
        db_paths = self.config.get('db_paths', {
            'snomed': 'data/terminology/snomed_core.sqlite',
            'loinc': 'data/terminology/loinc_core.sqlite',
            'rxnorm': 'data/terminology/rxnorm_core.sqlite'
        })
        
        self.query_optimizer = QueryOptimizer(db_paths)
        self.parallel_processor = ParallelProcessor(
            max_workers=self.config.get('max_workers'),
            use_processes=self.config.get('use_processes', False)
        )
        self.advanced_cache = AdvancedCache()
        
        # Performance monitoring
        self.performance_metrics = {}
        self._metrics_lock = threading.Lock()
        
        logger.info("Performance optimizer initialized")
    
    @performance_monitor
    def optimize_terminology_mapping(self, terms: List[str], 
                                   mapping_function: Callable,
                                   use_parallel: bool = True,
                                   use_cache: bool = True) -> List[Any]:
        """
        Optimize terminology mapping with all available optimizations.
        
        Args:
            terms: List of terms to map
            mapping_function: Function to perform mapping
            use_parallel: Whether to use parallel processing
            use_cache: Whether to use caching
            
        Returns:
            List of mapping results
        """
        start_time = time.time()
        
        if use_cache:
            # Check cache for pre-computed results
            cached_results = []
            uncached_terms = []
            
            for term in terms:
                cached = self.advanced_cache.get_cached_mapping(term, "combined")
                if cached:
                    cached_results.append(cached)
                else:
                    uncached_terms.append(term)
                    cached_results.append(None)  # Placeholder
        else:
            uncached_terms = terms
            cached_results = [None] * len(terms)
        
        # Process uncached terms
        if uncached_terms:
            if use_parallel and len(uncached_terms) > 10:
                # Use parallel processing for large batches
                uncached_results = self.parallel_processor.map_terms_parallel(
                    uncached_terms, mapping_function
                )
            else:
                # Sequential processing for small batches
                uncached_results = []
                for term in uncached_terms:
                    try:
                        result = mapping_function(term)
                        uncached_results.append(result)
                        
                        # Cache the result
                        if use_cache:
                            self.advanced_cache.cache_mapping(term, "combined", result)
                    except Exception as e:
                        logger.error(f"Error mapping term '{term}': {e}")
                        uncached_results.append(None)
            
            # Merge cached and uncached results
            uncached_iter = iter(uncached_results)
            final_results = []
            for cached_result in cached_results:
                if cached_result is None:
                    final_results.append(next(uncached_iter, None))
                else:
                    final_results.append(cached_result)
        else:
            final_results = cached_results
        
        execution_time = time.time() - start_time
        
        # Update performance metrics
        with self._metrics_lock:
            self.performance_metrics['last_optimization'] = {
                'total_terms': len(terms),
                'cached_terms': len(terms) - len(uncached_terms),
                'execution_time': execution_time,
                'cache_hit_rate': (len(terms) - len(uncached_terms)) / len(terms) if terms else 0,
                'throughput': len(terms) / execution_time if execution_time > 0 else 0,
                'used_parallel': use_parallel and len(uncached_terms) > 10
            }
        
        return final_results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        cache_stats = self.advanced_cache.get_cache_stats()
        
        with self._metrics_lock:
            last_opt = self.performance_metrics.get('last_optimization', {})
        
        return {
            'cache_statistics': cache_stats,
            'last_optimization': last_opt,
            'parallel_processor_config': {
                'max_workers': self.parallel_processor.max_workers,
                'use_processes': self.parallel_processor.use_processes
            },
            'query_optimizer': {
                'active_connections': len(self.query_optimizer.connection_pool),
                'query_cache_size': len(self.query_optimizer.query_cache)
            }
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.query_optimizer.close_connections()
        self.advanced_cache.clear_expired_entries()
        logger.info("Performance optimizer cleanup completed")


# Example usage and testing
def example_mapping_function(term: str) -> Dict[str, Any]:
    """Example mapping function for testing."""
    import random
    time.sleep(random.uniform(0.01, 0.1))  # Simulate work
    
    return {
        'term': term,
        'code': f"CODE_{hash(term) % 10000}",
        'system': 'TEST',
        'confidence': random.uniform(0.7, 1.0)
    }


if __name__ == "__main__":
    # Test performance optimization
    logging.basicConfig(level=logging.INFO)
    
    optimizer = PerformanceOptimizer()
    
    # Test with sample terms
    test_terms = [
        "hypertension", "diabetes", "pneumonia", "asthma", "arthritis",
        "depression", "anxiety", "migraine", "obesity", "anemia"
    ] * 10  # 100 terms total
    
    print("Testing performance optimization...")
    
    # Test with optimization
    start_time = time.time()
    results = optimizer.optimize_terminology_mapping(
        test_terms, example_mapping_function, use_parallel=True, use_cache=True
    )
    optimized_time = time.time() - start_time
    
    # Test without optimization (sequential)
    start_time = time.time()
    sequential_results = [example_mapping_function(term) for term in test_terms]
    sequential_time = time.time() - start_time
    
    print(f"\nResults:")
    print(f"Optimized processing: {optimized_time:.2f}s")
    print(f"Sequential processing: {sequential_time:.2f}s")
    print(f"Speedup: {sequential_time / optimized_time:.2f}x")
    
    # Show performance report
    report = optimizer.get_performance_report()
    print(f"\nPerformance Report:")
    print(json.dumps(report, indent=2, default=str))