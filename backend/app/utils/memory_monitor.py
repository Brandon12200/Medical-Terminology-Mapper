"""
Memory Usage Monitoring and Optimization for Medical Terminology Mapper

This module provides comprehensive memory monitoring, optimization, and
management capabilities for the terminology mapping system.
"""

import psutil
import gc
import sys
import time
import threading
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import tracemalloc
import weakref

logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """Memory usage snapshot at a point in time"""
    timestamp: float
    process_memory_mb: float
    system_memory_mb: float
    system_memory_percent: float
    cache_memory_mb: float
    gc_collections: Dict[int, int]
    top_allocations: List[Dict[str, Any]]
    thread_count: int


@dataclass
class MemoryAlert:
    """Memory usage alert"""
    timestamp: float
    alert_type: str
    message: str
    memory_usage_mb: float
    threshold_mb: float
    severity: str


class MemoryMonitor:
    """Comprehensive memory monitoring and optimization"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize memory monitor.
        
        Args:
            config: Configuration options including thresholds and intervals
        """
        self.config = config or {}
        
        # Monitoring configuration
        self.memory_threshold_mb = self.config.get('memory_threshold_mb', 1024)  # 1GB default
        self.critical_threshold_mb = self.config.get('critical_threshold_mb', 2048)  # 2GB critical
        self.monitoring_interval = self.config.get('monitoring_interval', 30)  # 30 seconds
        self.history_size = self.config.get('history_size', 100)  # Keep 100 snapshots
        
        # Memory tracking
        self.memory_history = deque(maxlen=self.history_size)
        self.alerts = deque(maxlen=50)  # Keep recent 50 alerts
        self.cache_objects = weakref.WeakSet()
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        self._lock = threading.RLock()
        
        # Initialize tracemalloc for detailed tracking
        if not tracemalloc.is_tracing():
            tracemalloc.start(10)  # Keep 10 frames
        
        # Statistics
        self.stats = {
            'peak_memory_mb': 0,
            'total_gc_collections': 0,
            'cache_evictions': 0,
            'alerts_triggered': 0
        }
        
        logger.info("Memory monitor initialized")
    
    def start_monitoring(self):
        """Start continuous memory monitoring"""
        if self.is_monitoring:
            logger.warning("Memory monitoring already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("Memory monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                snapshot = self.take_memory_snapshot()
                self._check_memory_thresholds(snapshot)
                
                # Update peak memory
                if snapshot.process_memory_mb > self.stats['peak_memory_mb']:
                    self.stats['peak_memory_mb'] = snapshot.process_memory_mb
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}")
                time.sleep(5)  # Brief pause before retrying
    
    def take_memory_snapshot(self) -> MemorySnapshot:
        """Take a comprehensive memory snapshot"""
        timestamp = time.time()
        
        # Process memory information
        process = psutil.Process()
        process_memory = process.memory_info()
        process_memory_mb = process_memory.rss / (1024 * 1024)
        
        # System memory information
        system_memory = psutil.virtual_memory()
        system_memory_mb = system_memory.total / (1024 * 1024)
        system_memory_percent = system_memory.percent
        
        # Cache memory estimation
        cache_memory_mb = self._estimate_cache_memory()
        
        # Garbage collector statistics
        gc_stats = {}
        for generation in range(3):
            gc_stats[generation] = gc.get_count()[generation]
        
        # Top memory allocations
        top_allocations = self._get_top_allocations()
        
        # Thread count
        thread_count = threading.active_count()
        
        snapshot = MemorySnapshot(
            timestamp=timestamp,
            process_memory_mb=process_memory_mb,
            system_memory_mb=system_memory_mb,
            system_memory_percent=system_memory_percent,
            cache_memory_mb=cache_memory_mb,
            gc_collections=gc_stats,
            top_allocations=top_allocations,
            thread_count=thread_count
        )
        
        with self._lock:
            self.memory_history.append(snapshot)
        
        return snapshot
    
    def _estimate_cache_memory(self) -> float:
        """Estimate memory used by cache objects"""
        total_size = 0
        
        try:
            # Estimate size of tracked cache objects
            for cache_obj in list(self.cache_objects):
                if hasattr(cache_obj, '__sizeof__'):
                    total_size += sys.getsizeof(cache_obj)
                elif hasattr(cache_obj, '__dict__'):
                    total_size += sys.getsizeof(cache_obj.__dict__)
        except Exception as e:
            logger.debug(f"Error estimating cache memory: {e}")
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def _get_top_allocations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top memory allocations using tracemalloc"""
        top_allocations = []
        
        try:
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')
                
                for stat in top_stats[:limit]:
                    allocation = {
                        'filename': stat.traceback.format()[-1] if stat.traceback.format() else 'unknown',
                        'size_mb': stat.size / (1024 * 1024),
                        'count': stat.count
                    }
                    top_allocations.append(allocation)
        
        except Exception as e:
            logger.debug(f"Error getting top allocations: {e}")
        
        return top_allocations
    
    def _check_memory_thresholds(self, snapshot: MemorySnapshot):
        """Check memory usage against thresholds and generate alerts"""
        memory_mb = snapshot.process_memory_mb
        
        # Critical threshold
        if memory_mb > self.critical_threshold_mb:
            alert = MemoryAlert(
                timestamp=snapshot.timestamp,
                alert_type="CRITICAL_MEMORY",
                message=f"Critical memory usage: {memory_mb:.1f}MB (threshold: {self.critical_threshold_mb}MB)",
                memory_usage_mb=memory_mb,
                threshold_mb=self.critical_threshold_mb,
                severity="CRITICAL"
            )
            self._trigger_alert(alert)
            self._emergency_memory_cleanup()
        
        # Warning threshold
        elif memory_mb > self.memory_threshold_mb:
            alert = MemoryAlert(
                timestamp=snapshot.timestamp,
                alert_type="HIGH_MEMORY",
                message=f"High memory usage: {memory_mb:.1f}MB (threshold: {self.memory_threshold_mb}MB)",
                memory_usage_mb=memory_mb,
                threshold_mb=self.memory_threshold_mb,
                severity="WARNING"
            )
            self._trigger_alert(alert)
            self._perform_memory_optimization()
    
    def _trigger_alert(self, alert: MemoryAlert):
        """Trigger a memory alert"""
        with self._lock:
            self.alerts.append(alert)
            self.stats['alerts_triggered'] += 1
        
        if alert.severity == "CRITICAL":
            logger.critical(alert.message)
        else:
            logger.warning(alert.message)
    
    def _perform_memory_optimization(self):
        """Perform standard memory optimization"""
        logger.info("Performing memory optimization")
        
        # Force garbage collection
        collected = 0
        for generation in range(3):
            collected += gc.collect(generation)
        
        self.stats['total_gc_collections'] += collected
        logger.debug(f"Garbage collection freed {collected} objects")
        
        # Optimize caches
        self._optimize_caches()
    
    def _emergency_memory_cleanup(self):
        """Perform emergency memory cleanup"""
        logger.critical("Performing emergency memory cleanup")
        
        # Aggressive garbage collection
        for _ in range(3):
            gc.collect()
        
        # Clear all caches
        self._clear_all_caches()
        
        # Force memory optimization
        self._perform_memory_optimization()
    
    def _optimize_caches(self):
        """Optimize cache memory usage"""
        evicted_count = 0
        
        # Optimize tracked cache objects
        for cache_obj in list(self.cache_objects):
            try:
                if hasattr(cache_obj, 'clear_expired_entries'):
                    cache_obj.clear_expired_entries()
                    evicted_count += 1
                elif hasattr(cache_obj, 'optimize'):
                    cache_obj.optimize()
                    evicted_count += 1
            except Exception as e:
                logger.debug(f"Error optimizing cache object: {e}")
        
        self.stats['cache_evictions'] += evicted_count
        logger.debug(f"Optimized {evicted_count} cache objects")
    
    def _clear_all_caches(self):
        """Clear all tracked caches (emergency only)"""
        cleared_count = 0
        
        for cache_obj in list(self.cache_objects):
            try:
                if hasattr(cache_obj, 'clear'):
                    cache_obj.clear()
                    cleared_count += 1
            except Exception as e:
                logger.debug(f"Error clearing cache object: {e}")
        
        logger.warning(f"Emergency cache clear: {cleared_count} caches cleared")
    
    def register_cache_object(self, cache_obj: Any):
        """Register a cache object for monitoring and optimization"""
        try:
            self.cache_objects.add(cache_obj)
            logger.debug(f"Registered cache object: {type(cache_obj).__name__}")
        except TypeError:
            # Some objects (like dict) cannot be weakly referenced
            # For these, we'll track them differently or skip registration
            logger.debug(f"Cannot weakly reference {type(cache_obj).__name__}, skipping registration")
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        current_snapshot = self.take_memory_snapshot()
        
        # Calculate trends
        memory_trend = self._calculate_memory_trend()
        recent_alerts = list(self.alerts)[-10:]  # Last 10 alerts
        
        statistics = {
            'current_memory': {
                'process_mb': current_snapshot.process_memory_mb,
                'system_percent': current_snapshot.system_memory_percent,
                'cache_mb': current_snapshot.cache_memory_mb,
                'thread_count': current_snapshot.thread_count
            },
            'thresholds': {
                'warning_mb': self.memory_threshold_mb,
                'critical_mb': self.critical_threshold_mb
            },
            'trends': memory_trend,
            'statistics': self.stats.copy(),
            'recent_alerts': [asdict(alert) for alert in recent_alerts],
            'top_allocations': current_snapshot.top_allocations,
            'gc_stats': current_snapshot.gc_collections
        }
        
        return statistics
    
    def _calculate_memory_trend(self) -> Dict[str, float]:
        """Calculate memory usage trends"""
        if len(self.memory_history) < 2:
            return {'trend': 0, 'avg_memory_mb': 0, 'peak_memory_mb': 0}
        
        snapshots = list(self.memory_history)
        
        # Calculate average memory usage
        avg_memory = sum(s.process_memory_mb for s in snapshots) / len(snapshots)
        
        # Calculate peak memory
        peak_memory = max(s.process_memory_mb for s in snapshots)
        
        # Calculate trend (simple linear trend)
        if len(snapshots) >= 5:
            recent_avg = sum(s.process_memory_mb for s in snapshots[-5:]) / 5
            older_avg = sum(s.process_memory_mb for s in snapshots[-10:-5]) / 5 if len(snapshots) >= 10 else recent_avg
            trend = recent_avg - older_avg
        else:
            trend = 0
        
        return {
            'trend': trend,
            'avg_memory_mb': avg_memory,
            'peak_memory_mb': peak_memory
        }
    
    def optimize_memory_usage(self):
        """Manually trigger memory optimization"""
        logger.info("Manual memory optimization triggered")
        self._perform_memory_optimization()
    
    def get_memory_recommendations(self) -> List[str]:
        """Get memory optimization recommendations"""
        recommendations = []
        current_snapshot = self.take_memory_snapshot()
        
        # High memory usage
        if current_snapshot.process_memory_mb > self.memory_threshold_mb:
            recommendations.append(
                f"Memory usage ({current_snapshot.process_memory_mb:.1f}MB) exceeds threshold "
                f"({self.memory_threshold_mb}MB). Consider increasing cache cleanup frequency."
            )
        
        # High cache memory
        if current_snapshot.cache_memory_mb > 100:  # 100MB cache
            recommendations.append(
                f"Cache memory usage is high ({current_snapshot.cache_memory_mb:.1f}MB). "
                "Consider reducing cache sizes or TTL values."
            )
        
        # Many threads
        if current_snapshot.thread_count > 20:
            recommendations.append(
                f"High thread count ({current_snapshot.thread_count}). "
                "Consider reducing parallel processing workers."
            )
        
        # Frequent GC
        gc_frequency = sum(current_snapshot.gc_collections.values())
        if gc_frequency > 1000:
            recommendations.append(
                "High garbage collection frequency suggests memory fragmentation. "
                "Consider object pooling or reducing object creation."
            )
        
        # Memory growth trend
        trend = self._calculate_memory_trend()
        if trend['trend'] > 10:  # Growing by more than 10MB
            recommendations.append(
                f"Memory usage is trending upward (+{trend['trend']:.1f}MB). "
                "Check for memory leaks or increase cleanup frequency."
            )
        
        return recommendations
    
    def export_memory_report(self, filepath: str):
        """Export detailed memory report to file"""
        import json
        
        report = {
            'timestamp': time.time(),
            'statistics': self.get_memory_statistics(),
            'recommendations': self.get_memory_recommendations(),
            'memory_history': [asdict(snapshot) for snapshot in list(self.memory_history)],
            'configuration': {
                'memory_threshold_mb': self.memory_threshold_mb,
                'critical_threshold_mb': self.critical_threshold_mb,
                'monitoring_interval': self.monitoring_interval
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Memory report exported to {filepath}")


class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def optimize_dictionary(d: Dict, max_size: int = 1000) -> Dict:
        """Optimize dictionary by limiting size and removing old entries"""
        if len(d) <= max_size:
            return d
        
        # Keep most recent entries (assumes ordered dict or recent Python)
        items = list(d.items())
        optimized = dict(items[-max_size:])
        
        logger.debug(f"Dictionary optimized: {len(d)} -> {len(optimized)} entries")
        return optimized
    
    @staticmethod
    def optimize_list(lst: List, max_size: int = 1000) -> List:
        """Optimize list by limiting size"""
        if len(lst) <= max_size:
            return lst
        
        optimized = lst[-max_size:]
        logger.debug(f"List optimized: {len(lst)} -> {len(optimized)} entries")
        return optimized
    
    @staticmethod
    def get_object_size(obj: Any) -> int:
        """Get approximate size of an object in bytes"""
        try:
            return sys.getsizeof(obj)
        except:
            return 0
    
    @staticmethod
    def force_garbage_collection() -> int:
        """Force garbage collection and return number of objects collected"""
        total_collected = 0
        for generation in range(3):
            collected = gc.collect(generation)
            total_collected += collected
        
        logger.debug(f"Forced GC collected {total_collected} objects")
        return total_collected


# Global memory monitor instance
_memory_monitor = None

def get_memory_monitor(config: Dict[str, Any] = None) -> MemoryMonitor:
    """Get or create global memory monitor instance"""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor(config)
    return _memory_monitor


def memory_profile(func: Callable) -> Callable:
    """Decorator to profile memory usage of a function"""
    def wrapper(*args, **kwargs):
        monitor = get_memory_monitor()
        
        # Take snapshot before
        before_snapshot = monitor.take_memory_snapshot()
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            raise
        finally:
            # Take snapshot after
            after_snapshot = monitor.take_memory_snapshot()
            
            # Log memory usage
            memory_diff = after_snapshot.process_memory_mb - before_snapshot.process_memory_mb
            logger.debug(
                f"Memory profile {func.__name__}: "
                f"{memory_diff:+.2f}MB change, "
                f"Success: {success}"
            )
        
        return result
    
    return wrapper


if __name__ == "__main__":
    # Demo memory monitoring
    monitor = MemoryMonitor({
        'memory_threshold_mb': 100,  # Low threshold for demo
        'monitoring_interval': 5
    })
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Simulate memory usage
    big_list = []
    for i in range(1000):
        big_list.append([0] * 1000)  # Allocate memory
        if i % 100 == 0:
            stats = monitor.get_memory_statistics()
            print(f"Iteration {i}: {stats['current_memory']['process_mb']:.1f}MB")
    
    # Get final statistics
    final_stats = monitor.get_memory_statistics()
    print(f"\nFinal Statistics:")
    print(f"Current Memory: {final_stats['current_memory']['process_mb']:.1f}MB")
    print(f"Peak Memory: {final_stats['statistics']['peak_memory_mb']:.1f}MB")
    print(f"Alerts Triggered: {final_stats['statistics']['alerts_triggered']}")
    
    # Get recommendations
    recommendations = monitor.get_memory_recommendations()
    if recommendations:
        print(f"\nRecommendations:")
        for rec in recommendations:
            print(f"- {rec}")
    
    # Stop monitoring
    monitor.stop_monitoring()