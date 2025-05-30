"""
Advanced Database Optimization for Medical Terminology Mapper

This module provides comprehensive database optimization including indexing,
query optimization, and performance monitoring for terminology databases.
"""

import sqlite3
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceMetrics:
    """Performance metrics for database queries"""
    query_hash: str
    execution_time: float
    rows_returned: int
    cache_hit: bool
    timestamp: float
    parameters: str


@dataclass
class DatabaseStats:
    """Database statistics and metadata"""
    database_path: str
    size_bytes: int
    table_count: int
    index_count: int
    page_count: int
    page_size: int
    cache_size: int
    total_queries: int
    avg_query_time: float
    cache_hit_ratio: float


class DatabaseOptimizer:
    """Advanced database optimization for terminology lookups"""
    
    def __init__(self, db_paths: Dict[str, str], config: Dict[str, Any] = None):
        """
        Initialize database optimizer.
        
        Args:
            db_paths: Dictionary mapping system names to database paths
            config: Configuration options
        """
        self.db_paths = db_paths
        self.config = config or {}
        self.connections = {}
        self.query_metrics = []
        self.performance_cache = {}
        self._lock = threading.RLock()
        
        # Performance tracking
        self.query_count = defaultdict(int)
        self.query_times = defaultdict(list)
        self.slow_queries = []
        
        # Initialize optimizations
        self._initialize_optimizations()
        
    def _initialize_optimizations(self):
        """Initialize database optimizations for all systems"""
        for system, db_path in self.db_paths.items():
            if Path(db_path).exists():
                self._optimize_database(system, db_path)
    
    def _optimize_database(self, system: str, db_path: str):
        """Apply comprehensive optimizations to a database"""
        logger.info(f"Optimizing database for {system}: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            
            # Apply performance pragmas
            self._apply_performance_pragmas(conn)
            
            # Create performance indexes
            self._create_performance_indexes(conn, system)
            
            # Analyze database for query planning
            conn.execute("ANALYZE")
            
            # Update database statistics
            conn.execute("PRAGMA optimize")
            
            conn.close()
            logger.info(f"Database optimization completed for {system}")
            
        except Exception as e:
            logger.error(f"Error optimizing database {system}: {e}")
    
    def _apply_performance_pragmas(self, conn: sqlite3.Connection):
        """Apply performance-enhancing pragmas"""
        pragmas = [
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=NORMAL", 
            "PRAGMA cache_size=20000",  # Increased cache size
            "PRAGMA temp_store=MEMORY",
            "PRAGMA mmap_size=536870912",  # 512MB memory mapping
            "PRAGMA page_size=4096",
            "PRAGMA auto_vacuum=INCREMENTAL",
            "PRAGMA busy_timeout=30000",
            "PRAGMA checkpoint_fullfsync=0",
            "PRAGMA wal_autocheckpoint=1000"
        ]
        
        for pragma in pragmas:
            try:
                conn.execute(pragma)
                logger.debug(f"Applied pragma: {pragma}")
            except Exception as e:
                logger.warning(f"Failed to apply pragma {pragma}: {e}")
    
    def _create_performance_indexes(self, conn: sqlite3.Connection, system: str):
        """Create system-specific performance indexes"""
        
        # Common indexes for all systems
        common_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_code_lookup ON concepts(code)",
            "CREATE INDEX IF NOT EXISTS idx_display_lookup ON concepts(display)",
            "CREATE INDEX IF NOT EXISTS idx_system_lookup ON concepts(system)",
            "CREATE INDEX IF NOT EXISTS idx_code_system ON concepts(code, system)",
            "CREATE INDEX IF NOT EXISTS idx_display_search ON concepts(display COLLATE NOCASE)"
        ]
        
        # System-specific indexes
        system_indexes = {
            'snomed': [
                "CREATE INDEX IF NOT EXISTS idx_snomed_hierarchy ON relationships(source_id, target_id, type)",
                "CREATE INDEX IF NOT EXISTS idx_snomed_descriptions ON descriptions(concept_id, term)",
                "CREATE INDEX IF NOT EXISTS idx_snomed_term_search ON descriptions(term COLLATE NOCASE)",
                "CREATE INDEX IF NOT EXISTS idx_snomed_semantic_tag ON concepts(semantic_tag)"
            ],
            'loinc': [
                "CREATE INDEX IF NOT EXISTS idx_loinc_component ON concepts(component)",
                "CREATE INDEX IF NOT EXISTS idx_loinc_property ON concepts(property)",
                "CREATE INDEX IF NOT EXISTS idx_loinc_system_concept ON concepts(system_concept)",
                "CREATE INDEX IF NOT EXISTS idx_loinc_scale ON concepts(scale_typ)",
                "CREATE INDEX IF NOT EXISTS idx_loinc_method ON concepts(method_typ)",
                "CREATE INDEX IF NOT EXISTS idx_loinc_class ON concepts(class)"
            ],
            'rxnorm': [
                "CREATE INDEX IF NOT EXISTS idx_rxnorm_ingredient ON concepts(ingredient)",
                "CREATE INDEX IF NOT EXISTS idx_rxnorm_strength ON concepts(strength)",
                "CREATE INDEX IF NOT EXISTS idx_rxnorm_dose_form ON concepts(dose_form)",
                "CREATE INDEX IF NOT EXISTS idx_rxnorm_tty ON concepts(tty)",
                "CREATE INDEX IF NOT EXISTS idx_rxnorm_relationships ON relationships(rxcui1, rxcui2, rela)"
            ]
        }
        
        # Apply common indexes
        for index_sql in common_indexes:
            try:
                conn.execute(index_sql)
                logger.debug(f"Created common index")
            except Exception as e:
                logger.debug(f"Index may already exist or table structure different: {e}")
        
        # Apply system-specific indexes
        if system in system_indexes:
            for index_sql in system_indexes[system]:
                try:
                    conn.execute(index_sql)
                    logger.debug(f"Created {system} specific index")
                except Exception as e:
                    logger.debug(f"System-specific index not applied: {e}")
    
    def get_optimized_connection(self, system: str) -> sqlite3.Connection:
        """Get an optimized database connection"""
        with self._lock:
            if system not in self.connections:
                if system not in self.db_paths:
                    raise ValueError(f"Unknown system: {system}")
                
                conn = sqlite3.connect(
                    self.db_paths[system],
                    check_same_thread=False,
                    timeout=30.0
                )
                
                # Apply runtime optimizations
                self._apply_performance_pragmas(conn)
                
                # Set row factory for better performance
                conn.row_factory = sqlite3.Row
                
                self.connections[system] = conn
                
            return self.connections[system]
    
    def execute_optimized_query(self, system: str, query: str, parameters: Tuple = None) -> List[Dict[str, Any]]:
        """Execute an optimized query with performance tracking"""
        start_time = time.time()
        query_hash = hash(f"{system}:{query}:{parameters}")
        
        # Check query cache first
        cache_key = f"{query_hash}"
        if cache_key in self.performance_cache:
            cached_result, timestamp = self.performance_cache[cache_key]
            # Cache valid for 5 minutes
            if time.time() - timestamp < 300:
                execution_time = time.time() - start_time
                self._record_query_metrics(query_hash, execution_time, len(cached_result), True, parameters)
                return cached_result
        
        # Execute query
        try:
            conn = self.get_optimized_connection(system)
            
            if parameters:
                cursor = conn.execute(query, parameters)
            else:
                cursor = conn.execute(query)
            
            results = [dict(row) for row in cursor.fetchall()]
            
            # Cache results
            self.performance_cache[cache_key] = (results, time.time())
            
            # Maintain cache size
            if len(self.performance_cache) > 2000:
                # Remove oldest 200 entries
                oldest_keys = sorted(self.performance_cache.keys(), 
                                   key=lambda k: self.performance_cache[k][1])[:200]
                for key in oldest_keys:
                    del self.performance_cache[key]
            
            execution_time = time.time() - start_time
            self._record_query_metrics(query_hash, execution_time, len(results), False, parameters)
            
            return results
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Database query error in {system}: {e}")
            self._record_query_metrics(query_hash, execution_time, 0, False, parameters)
            return []
    
    def _record_query_metrics(self, query_hash: str, execution_time: float, 
                             rows_returned: int, cache_hit: bool, parameters: Any):
        """Record query performance metrics"""
        metric = QueryPerformanceMetrics(
            query_hash=str(query_hash),
            execution_time=execution_time,
            rows_returned=rows_returned,
            cache_hit=cache_hit,
            timestamp=time.time(),
            parameters=str(parameters) if parameters else ""
        )
        
        self.query_metrics.append(metric)
        self.query_count[query_hash] += 1
        self.query_times[query_hash].append(execution_time)
        
        # Track slow queries (>100ms)
        if execution_time > 0.1 and not cache_hit:
            self.slow_queries.append(metric)
        
        # Maintain metrics size
        if len(self.query_metrics) > 10000:
            self.query_metrics = self.query_metrics[-5000:]  # Keep recent 5000
        
        if len(self.slow_queries) > 100:
            self.slow_queries = self.slow_queries[-50:]  # Keep recent 50
    
    def get_database_stats(self, system: str) -> DatabaseStats:
        """Get comprehensive database statistics"""
        try:
            conn = self.get_optimized_connection(system)
            
            # Database size
            db_path = self.db_paths[system]
            size_bytes = Path(db_path).stat().st_size if Path(db_path).exists() else 0
            
            # Table and index counts
            tables_result = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()
            table_count = tables_result[0] if tables_result else 0
            
            indexes_result = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
            ).fetchone()
            index_count = indexes_result[0] if indexes_result else 0
            
            # Page information
            page_count_result = conn.execute("PRAGMA page_count").fetchone()
            page_count = page_count_result[0] if page_count_result else 0
            
            page_size_result = conn.execute("PRAGMA page_size").fetchone()
            page_size = page_size_result[0] if page_size_result else 0
            
            cache_size_result = conn.execute("PRAGMA cache_size").fetchone()
            cache_size = cache_size_result[0] if cache_size_result else 0
            
            # Query statistics
            system_queries = [m for m in self.query_metrics if system in str(m.query_hash)]
            total_queries = len(system_queries)
            avg_query_time = sum(m.execution_time for m in system_queries) / total_queries if total_queries > 0 else 0
            cache_hits = sum(1 for m in system_queries if m.cache_hit)
            cache_hit_ratio = cache_hits / total_queries if total_queries > 0 else 0
            
            return DatabaseStats(
                database_path=db_path,
                size_bytes=size_bytes,
                table_count=table_count,
                index_count=index_count,
                page_count=page_count,
                page_size=page_size,
                cache_size=abs(cache_size),  # Cache size can be negative
                total_queries=total_queries,
                avg_query_time=avg_query_time,
                cache_hit_ratio=cache_hit_ratio
            )
            
        except Exception as e:
            logger.error(f"Error getting database stats for {system}: {e}")
            return DatabaseStats(
                database_path=self.db_paths.get(system, ""),
                size_bytes=0, table_count=0, index_count=0,
                page_count=0, page_size=0, cache_size=0,
                total_queries=0, avg_query_time=0, cache_hit_ratio=0
            )
    
    def optimize_slow_queries(self) -> List[str]:
        """Analyze and optimize slow queries"""
        recommendations = []
        
        # Analyze slow queries
        if self.slow_queries:
            # Group by query pattern
            query_patterns = defaultdict(list)
            for metric in self.slow_queries:
                query_patterns[metric.query_hash].append(metric)
            
            for query_hash, metrics in query_patterns.items():
                avg_time = sum(m.execution_time for m in metrics) / len(metrics)
                frequency = len(metrics)
                
                if avg_time > 0.5:  # Very slow queries
                    recommendations.append(
                        f"Query {query_hash}: avg {avg_time:.3f}s, {frequency} executions - Consider adding specific indexes"
                    )
                elif frequency > 10:  # Frequent slow queries
                    recommendations.append(
                        f"Query {query_hash}: {frequency} executions, avg {avg_time:.3f}s - Consider caching or query optimization"
                    )
        
        # Check for missing indexes
        for system in self.db_paths:
            try:
                conn = self.get_optimized_connection(system)
                
                # Check if ANALYZE has been run recently
                analyze_result = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_stat1"
                ).fetchone()
                
                if not analyze_result or analyze_result[0] == 0:
                    recommendations.append(f"Run ANALYZE on {system} database for better query planning")
                
            except Exception as e:
                logger.debug(f"Could not check analyze status for {system}: {e}")
        
        return recommendations
    
    def vacuum_databases(self, systems: List[str] = None):
        """Vacuum databases to reclaim space and optimize"""
        systems = systems or list(self.db_paths.keys())
        
        for system in systems:
            try:
                logger.info(f"Vacuuming database: {system}")
                conn = self.get_optimized_connection(system)
                
                # Close connection for vacuum
                conn.close()
                if system in self.connections:
                    del self.connections[system]
                
                # Perform vacuum
                temp_conn = sqlite3.connect(self.db_paths[system])
                temp_conn.execute("VACUUM")
                temp_conn.close()
                
                logger.info(f"Vacuum completed for {system}")
                
            except Exception as e:
                logger.error(f"Error vacuuming database {system}: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'database_stats': {},
            'query_performance': {},
            'cache_performance': {},
            'optimization_recommendations': []
        }
        
        # Database statistics
        for system in self.db_paths:
            report['database_stats'][system] = self.get_database_stats(system).__dict__
        
        # Query performance
        if self.query_metrics:
            recent_metrics = [m for m in self.query_metrics if time.time() - m.timestamp < 3600]  # Last hour
            
            report['query_performance'] = {
                'total_queries': len(self.query_metrics),
                'recent_queries': len(recent_metrics),
                'avg_execution_time': sum(m.execution_time for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0,
                'slow_queries_count': len(self.slow_queries),
                'cache_hit_ratio': sum(1 for m in recent_metrics if m.cache_hit) / len(recent_metrics) if recent_metrics else 0
            }
        
        # Cache performance
        report['cache_performance'] = {
            'cache_size': len(self.performance_cache),
            'max_cache_size': 2000,
            'cache_utilization': len(self.performance_cache) / 2000 * 100
        }
        
        # Optimization recommendations
        report['optimization_recommendations'] = self.optimize_slow_queries()
        
        return report
    
    def close_all_connections(self):
        """Close all database connections"""
        with self._lock:
            for system, conn in self.connections.items():
                try:
                    conn.close()
                    logger.debug(f"Closed connection for {system}")
                except Exception as e:
                    logger.warning(f"Error closing connection for {system}: {e}")
            
            self.connections.clear()
    
    def benchmark_queries(self, test_queries: List[Tuple[str, str, Tuple]] = None) -> Dict[str, Any]:
        """Benchmark database query performance"""
        if not test_queries:
            # Default benchmark queries
            test_queries = [
                ('snomed', "SELECT * FROM concepts WHERE code = ?", ('123456789',)),
                ('snomed', "SELECT * FROM concepts WHERE display LIKE ?", ('%pain%',)),
                ('loinc', "SELECT * FROM concepts WHERE component LIKE ?", ('%glucose%',)),
                ('rxnorm', "SELECT * FROM concepts WHERE ingredient LIKE ?", ('%aspirin%',))
            ]
        
        benchmark_results = {}
        
        for system, query, params in test_queries:
            if system not in self.db_paths:
                continue
                
            # Run query multiple times to get average
            times = []
            for _ in range(5):
                start_time = time.time()
                try:
                    results = self.execute_optimized_query(system, query, params)
                    execution_time = time.time() - start_time
                    times.append(execution_time)
                except Exception as e:
                    logger.error(f"Benchmark query failed: {e}")
                    times.append(float('inf'))
            
            # Calculate statistics
            valid_times = [t for t in times if t != float('inf')]
            if valid_times:
                benchmark_results[f"{system}_{hash(query)}"] = {
                    'system': system,
                    'query': query[:50] + "..." if len(query) > 50 else query,
                    'avg_time': sum(valid_times) / len(valid_times),
                    'min_time': min(valid_times),
                    'max_time': max(valid_times),
                    'runs': len(valid_times)
                }
        
        return benchmark_results


def create_database_optimizer(terminology_db_path: str) -> DatabaseOptimizer:
    """Create a database optimizer for the terminology databases"""
    db_paths = {
        'snomed': f"{terminology_db_path}/snomed_core.sqlite",
        'loinc': f"{terminology_db_path}/loinc_core.sqlite", 
        'rxnorm': f"{terminology_db_path}/rxnorm_core.sqlite"
    }
    
    # Filter to only existing databases
    existing_db_paths = {
        system: path for system, path in db_paths.items() 
        if Path(path).exists()
    }
    
    if not existing_db_paths:
        logger.warning("No terminology databases found for optimization")
        return None
    
    return DatabaseOptimizer(existing_db_paths)


if __name__ == "__main__":
    # Demo database optimization
    import tempfile
    
    # Create a demo database
    temp_dir = tempfile.mkdtemp()
    demo_db = f"{temp_dir}/demo.sqlite"
    
    # Create demo database with sample data
    conn = sqlite3.connect(demo_db)
    conn.execute("""
        CREATE TABLE concepts (
            id INTEGER PRIMARY KEY,
            code TEXT,
            display TEXT,
            system TEXT
        )
    """)
    
    # Insert sample data
    for i in range(1000):
        conn.execute(
            "INSERT INTO concepts (code, display, system) VALUES (?, ?, ?)",
            (f"CODE_{i}", f"Display Term {i}", "DEMO")
        )
    
    conn.commit()
    conn.close()
    
    # Test optimization
    optimizer = DatabaseOptimizer({'demo': demo_db})
    
    # Run some test queries
    for i in range(10):
        results = optimizer.execute_optimized_query(
            'demo', 
            "SELECT * FROM concepts WHERE display LIKE ?", 
            (f"%{i}%",)
        )
        print(f"Query {i}: {len(results)} results")
    
    # Get performance report
    report = optimizer.get_performance_report()
    print(f"\nPerformance Report:")
    print(json.dumps(report, indent=2, default=str))
    
    # Cleanup
    optimizer.close_all_connections()
    import shutil
    shutil.rmtree(temp_dir)