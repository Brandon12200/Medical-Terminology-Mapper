"""
Caching system for term extraction to improve performance.
This module provides caching capabilities to avoid redundant processing
of similar text chunks. Adapted from the Clinical Protocol Extractor's
entity_cache.py with terminology-specific adjustments.
"""

import os
import json
import logging
import hashlib
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading

# Configure logging
logger = logging.getLogger(__name__)

class TermCache:
    """
    Cache system for extracted medical terms to improve performance.
    
    This class implements a two-level caching strategy:
    1. In-memory LRU cache for fastest access to recent results
    2. Disk-based cache for persistence between runs
    """
    
    def __init__(self, cache_dir: Optional[str] = None, max_memory_items: int = 1000, 
                 max_disk_items: int = 10000, ttl: int = 86400):
        """
        Initialize the term cache.
        
        Args:
            cache_dir (str, optional): Directory for persistent cache storage.
                If None, uses a default directory in the system temp folder.
            max_memory_items (int): Maximum number of items to keep in memory.
            max_disk_items (int): Maximum number of items to store on disk.
            ttl (int): Time-to-live for cache entries in seconds (default: 24 hours).
        """
        # Set up cache directories
        if cache_dir is None:
            self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                      'cache', 'term_cache')
        else:
            self.cache_dir = cache_dir
            
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache parameters
        self.max_memory_items = max_memory_items
        self.max_disk_items = max_disk_items
        self.ttl = ttl
        
        # Initialize in-memory cache
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        
        # Cache stats
        self.stats = {
            'hits': 0,
            'misses': 0,
            'memory_hits': 0,
            'disk_hits': 0,
            'entries': 0
        }
        
        # Thread lock for cache operations
        self.lock = threading.RLock()
        
        # Load cache stats if they exist
        self._load_stats()
        
        logger.info(f"Term cache initialized with {self.stats['entries']} entries")
        
    def _load_stats(self):
        """Load cache statistics from disk."""
        stats_path = os.path.join(self.cache_dir, 'cache_stats.json')
        if os.path.exists(stats_path):
            try:
                with open(stats_path, 'r') as f:
                    self.stats.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load cache stats: {e}")
    
    def _save_stats(self):
        """Save cache statistics to disk."""
        stats_path = os.path.join(self.cache_dir, 'cache_stats.json')
        try:
            with open(stats_path, 'w') as f:
                json.dump(self.stats, f)
        except Exception as e:
            logger.warning(f"Failed to save cache stats: {e}")
    
    def _get_cache_key(self, text: str, model_id: str, threshold: float) -> str:
        """
        Generate a cache key for the given text and parameters.
        
        Args:
            text (str): The text to extract terms from
            model_id (str): Identifier for the model or extraction method
            threshold (float): Confidence threshold
            
        Returns:
            str: Cache key
        """
        # Create a string with all parameters
        key_string = f"{text}|{model_id}|{threshold}"
        
        # Generate SHA-256 hash as cache key
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """
        Get the file path for a disk cache entry.
        
        Args:
            cache_key (str): Cache key
            
        Returns:
            str: File path for cache entry
        """
        # Use the first two characters of the key for subdirectory
        # This helps distribute files and avoid too many files in one directory
        subdir = cache_key[:2]
        cache_subdir = os.path.join(self.cache_dir, subdir)
        os.makedirs(cache_subdir, exist_ok=True)
        
        return os.path.join(cache_subdir, f"{cache_key}.json")
    
    def get(self, text: str, model_id: str, threshold: float) -> Optional[List[Dict[str, Any]]]:
        """
        Get terms from cache if available.
        
        Args:
            text (str): The text to extract terms from
            model_id (str): Identifier for the model or extraction method
            threshold (float): Confidence threshold
            
        Returns:
            Optional[List[Dict[str, Any]]]: Cached terms or None if not found
        """
        with self.lock:
            cache_key = self._get_cache_key(text, model_id, threshold)
            current_time = time.time()
            
            # Check in-memory cache first (fastest)
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                
                # Check if entry is still valid
                if current_time - entry['timestamp'] <= self.ttl:
                    # Update access time
                    self.access_times[cache_key] = current_time
                    self.stats['hits'] += 1
                    self.stats['memory_hits'] += 1
                    return entry['terms']
                else:
                    # Entry expired, remove from memory cache
                    del self.memory_cache[cache_key]
                    if cache_key in self.access_times:
                        del self.access_times[cache_key]
            
            # Check disk cache
            cache_path = self._get_cache_path(cache_key)
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r') as f:
                        entry = json.load(f)
                    
                    # Check if entry is still valid
                    if current_time - entry['timestamp'] <= self.ttl:
                        # Add to memory cache
                        self.memory_cache[cache_key] = entry
                        self.access_times[cache_key] = current_time
                        
                        # Maintain memory cache size
                        if len(self.memory_cache) > self.max_memory_items:
                            self._evict_memory_cache()
                        
                        self.stats['hits'] += 1
                        self.stats['disk_hits'] += 1
                        return entry['terms']
                    else:
                        # Entry expired, remove file
                        os.remove(cache_path)
                except Exception as e:
                    logger.warning(f"Failed to read cache entry: {e}")
            
            # Cache miss
            self.stats['misses'] += 1
            return None
    
    def put(self, text: str, model_id: str, threshold: float, 
            terms: List[Dict[str, Any]]) -> None:
        """
        Store terms in cache.
        
        Args:
            text (str): The text that terms were extracted from
            model_id (str): Identifier for the model or extraction method
            threshold (float): Confidence threshold used
            terms (List[Dict[str, Any]]): Extracted terms to cache
        """
        with self.lock:
            cache_key = self._get_cache_key(text, model_id, threshold)
            current_time = time.time()
            
            # Prepare cache entry
            entry = {
                'timestamp': current_time,
                'model_id': model_id,
                'threshold': threshold,
                'text_hash': hashlib.md5(text.encode('utf-8')).hexdigest(),
                'terms': terms
            }
            
            # Store in memory cache
            self.memory_cache[cache_key] = entry
            self.access_times[cache_key] = current_time
            
            # Maintain memory cache size
            if len(self.memory_cache) > self.max_memory_items:
                self._evict_memory_cache()
            
            # Store in disk cache
            try:
                cache_path = self._get_cache_path(cache_key)
                with open(cache_path, 'w') as f:
                    json.dump(entry, f)
                
                # Update stats
                self.stats['entries'] += 1
                self._save_stats()
                
                # Clean disk cache if necessary
                self._clean_disk_cache()
            except Exception as e:
                logger.warning(f"Failed to write cache entry: {e}")
    
    def _evict_memory_cache(self):
        """
        Evict least recently used items from memory cache.
        This is called when the memory cache exceeds the maximum size.
        """
        # Sort by access time, oldest first
        sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])
        
        # Remove oldest entries until we're under the limit
        entries_to_remove = len(self.memory_cache) - self.max_memory_items + 10
        for i in range(min(entries_to_remove, len(sorted_keys))):
            key_to_remove = sorted_keys[i][0]
            if key_to_remove in self.memory_cache:
                del self.memory_cache[key_to_remove]
            if key_to_remove in self.access_times:
                del self.access_times[key_to_remove]
    
    def _clean_disk_cache(self):
        """
        Clean up disk cache by removing old entries or when exceeding max items.
        """
        try:
            # Get all cache files
            cache_files = []
            for root, _, files in os.walk(self.cache_dir):
                for file in files:
                    if file.endswith('.json') and file != 'cache_stats.json':
                        cache_path = os.path.join(root, file)
                        cache_files.append((cache_path, os.path.getmtime(cache_path)))
            
            # If under the limit, nothing to do
            if len(cache_files) <= self.max_disk_items:
                return
            
            # Sort by modification time (oldest first)
            cache_files.sort(key=lambda x: x[1])
            
            # Remove oldest files until we're under the limit
            files_to_remove = len(cache_files) - self.max_disk_items + 100
            for i in range(min(files_to_remove, len(cache_files))):
                try:
                    os.remove(cache_files[i][0])
                    self.stats['entries'] -= 1
                except Exception as e:
                    logger.warning(f"Failed to remove cache file {cache_files[i][0]}: {e}")
            
            # Update stats
            self._save_stats()
        except Exception as e:
            logger.warning(f"Failed to clean disk cache: {e}")
    
    def clear(self, older_than_days: Optional[int] = None):
        """
        Clear the cache, optionally only entries older than a certain age.
        
        Args:
            older_than_days (int, optional): If provided, only clear entries
                older than this many days. If None, clear all entries.
        """
        with self.lock:
            if older_than_days is None:
                # Clear all cache
                self.memory_cache = {}
                self.access_times = {}
                
                try:
                    # Clear disk cache (except stats file)
                    for root, _, files in os.walk(self.cache_dir):
                        for file in files:
                            if file != 'cache_stats.json':
                                try:
                                    os.remove(os.path.join(root, file))
                                except Exception as e:
                                    logger.warning(f"Failed to remove cache file: {e}")
                    
                    # Reset stats
                    self.stats['entries'] = 0
                    self._save_stats()
                except Exception as e:
                    logger.error(f"Failed to clear disk cache: {e}")
            else:
                # Clear entries older than specified days
                cutoff_time = time.time() - (older_than_days * 86400)
                
                # Clear memory cache
                keys_to_remove = []
                for key, entry in self.memory_cache.items():
                    if entry['timestamp'] < cutoff_time:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.memory_cache[key]
                    if key in self.access_times:
                        del self.access_times[key]
                
                # Clear disk cache
                try:
                    deleted_count = 0
                    for root, _, files in os.walk(self.cache_dir):
                        for file in files:
                            if file != 'cache_stats.json':
                                file_path = os.path.join(root, file)
                                if os.path.getmtime(file_path) < cutoff_time:
                                    try:
                                        os.remove(file_path)
                                        deleted_count += 1
                                    except Exception as e:
                                        logger.warning(f"Failed to remove old cache file: {e}")
                    
                    # Update stats
                    self.stats['entries'] -= deleted_count
                    self._save_stats()
                except Exception as e:
                    logger.error(f"Failed to clear old disk cache: {e}")
            
            logger.info(f"Cache cleared. {self.stats['entries']} entries remaining.")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_ratio = self.stats['hits'] / max(1, total_requests) * 100
            
            return {
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'memory_hits': self.stats['memory_hits'],
                'disk_hits': self.stats['disk_hits'],
                'hit_ratio': hit_ratio,
                'entries': self.stats['entries'],
                'memory_entries': len(self.memory_cache),
                'cache_dir': self.cache_dir
            }
    
    def optimize(self):
        """
        Optimize the cache by removing expired entries and reorganizing files.
        """
        with self.lock:
            logger.info("Optimizing term cache...")
            start_time = time.time()
            
            # Remove expired entries from memory cache
            current_time = time.time()
            memory_keys_to_remove = []
            for key, entry in self.memory_cache.items():
                if current_time - entry['timestamp'] > self.ttl:
                    memory_keys_to_remove.append(key)
            
            for key in memory_keys_to_remove:
                del self.memory_cache[key]
                if key in self.access_times:
                    del self.access_times[key]
            
            # Remove expired entries from disk cache
            expired_count = 0
            try:
                for root, _, files in os.walk(self.cache_dir):
                    for file in files:
                        if file.endswith('.json') and file != 'cache_stats.json':
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r') as f:
                                    entry = json.load(f)
                                if current_time - entry['timestamp'] > self.ttl:
                                    os.remove(file_path)
                                    expired_count += 1
                            except Exception as e:
                                logger.warning(f"Failed to process cache file {file_path}: {e}")
                                # Remove invalid files
                                try:
                                    os.remove(file_path)
                                    expired_count += 1
                                except:
                                    pass
            except Exception as e:
                logger.error(f"Failed to optimize disk cache: {e}")
            
            # Update stats
            self.stats['entries'] -= expired_count
            self._save_stats()
            
            duration = time.time() - start_time
            logger.info(f"Cache optimization completed in {duration:.2f}s. Removed {expired_count} expired entries.")


# Global singleton instance
_cache_instance = None

def get_term_cache() -> TermCache:
    """
    Get or create the global term cache instance.
    
    Returns:
        TermCache: The global term cache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = TermCache()
    return _cache_instance


# For testing purposes
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create cache instance
    cache = TermCache()
    
    # Test putting and getting items
    sample_text = "Patient has hypertension and diabetes mellitus type 2."
    sample_terms = [
        {
            'text': 'hypertension',
            'type': 'CONDITION',
            'start': 12,
            'end': 24,
            'confidence': 0.95,
            'terminology': {
                'mapped': False,
                'vocabulary': 'SNOMED CT',
                'code': None,
                'description': None
            }
        },
        {
            'text': 'diabetes mellitus type 2',
            'type': 'CONDITION',
            'start': 29,
            'end': 52,
            'confidence': 0.9,
            'terminology': {
                'mapped': False,
                'vocabulary': 'SNOMED CT',
                'code': None,
                'description': None
            }
        }
    ]
    
    # Cache the terms
    cache.put(sample_text, 'test-model', 0.7, sample_terms)
    
    # Retrieve from cache
    cached_terms = cache.get(sample_text, 'test-model', 0.7)
    
    # Verify
    if cached_terms:
        print("Cache hit!")
        print(f"Retrieved {len(cached_terms)} terms from cache")
    else:
        print("Cache miss!")
    
    # Print stats
    print("\nCache Statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")