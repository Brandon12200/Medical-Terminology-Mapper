"""
Performance Profiling and Benchmarking for Medical Terminology Mapper

This module provides comprehensive performance profiling, benchmarking,
and analysis tools for the terminology mapping system.
"""

import time
import cProfile
import pstats
import io
import threading
import logging
import json
import functools
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark"""
    test_name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    median_time: float
    std_dev: float
    throughput: float
    memory_used_mb: float
    success_rate: float
    errors: List[str]


@dataclass
class ProfileData:
    """Profiling data for a function or operation"""
    function_name: str
    call_count: int
    total_time: float
    avg_time: float
    cumulative_time: float
    file_location: str
    line_number: int


class PerformanceProfiler:
    """Comprehensive performance profiling and benchmarking system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize performance profiler.
        
        Args:
            config: Configuration options for profiling
        """
        self.config = config or {}
        
        # Profiling state
        self.is_profiling = False
        self.profiler = None
        self.profile_stats = None
        
        # Benchmark results storage
        self.benchmark_results = {}
        self.function_metrics = defaultdict(list)
        
        # Performance monitoring
        self.execution_times = defaultdict(deque)
        self.max_history = self.config.get('max_history', 1000)
        
        # Threading
        self._lock = threading.RLock()
        
        logger.info("Performance profiler initialized")
    
    def start_profiling(self):
        """Start cProfile profiling"""
        if self.is_profiling:
            logger.warning("Profiling already active")
            return
        
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        self.is_profiling = True
        logger.info("Performance profiling started")
    
    def stop_profiling(self) -> pstats.Stats:
        """Stop profiling and return stats"""
        if not self.is_profiling:
            logger.warning("Profiling not active")
            return None
        
        self.profiler.disable()
        self.is_profiling = False
        
        # Create stats object
        stats_stream = io.StringIO()
        self.profile_stats = pstats.Stats(self.profiler, stream=stats_stream)
        
        logger.info("Performance profiling stopped")
        return self.profile_stats
    
    def get_profile_report(self, sort_by: str = 'cumulative', limit: int = 20) -> Dict[str, Any]:
        """Get formatted profiling report"""
        if not self.profile_stats:
            return {'error': 'No profiling data available'}
        
        # Capture stats output
        stats_stream = io.StringIO()
        stats = pstats.Stats(self.profiler, stream=stats_stream)
        stats.sort_stats(sort_by)
        stats.print_stats(limit)
        
        # Parse top functions
        top_functions = []
        stats.sort_stats(sort_by)
        
        for func_key, (cc, nc, tt, ct, callers) in list(stats.stats.items())[:limit]:
            filename, line_num, func_name = func_key
            
            profile_data = ProfileData(
                function_name=func_name,
                call_count=nc,
                total_time=tt,
                avg_time=tt / nc if nc > 0 else 0,
                cumulative_time=ct,
                file_location=filename,
                line_number=line_num
            )
            top_functions.append(asdict(profile_data))
        
        return {
            'sort_by': sort_by,
            'total_functions': len(stats.stats),
            'top_functions': top_functions,
            'raw_output': stats_stream.getvalue()
        }
    
    def benchmark_function(self, func: Callable, args: Tuple = (), kwargs: Dict = None,
                          iterations: int = 100, warmup: int = 10) -> BenchmarkResult:
        """
        Benchmark a function's performance.
        
        Args:
            func: Function to benchmark
            args: Arguments for the function
            kwargs: Keyword arguments for the function
            iterations: Number of benchmark iterations
            warmup: Number of warmup iterations
            
        Returns:
            BenchmarkResult with performance metrics
        """
        kwargs = kwargs or {}
        test_name = getattr(func, '__name__', str(func))
        
        logger.info(f"Benchmarking {test_name} with {iterations} iterations")
        
        # Warmup
        for _ in range(warmup):
            try:
                func(*args, **kwargs)
            except Exception:
                pass  # Ignore warmup errors
        
        # Benchmark
        execution_times = []
        errors = []
        successful_runs = 0
        
        # Memory tracking
        try:
            import psutil
            process = psutil.Process()
            start_memory = process.memory_info().rss / (1024 * 1024)
        except ImportError:
            start_memory = 0
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                execution_times.append(end_time - start_time)
                successful_runs += 1
            except Exception as e:
                end_time = time.perf_counter()
                execution_times.append(end_time - start_time)
                errors.append(f"Iteration {i}: {str(e)}")
        
        # Memory after benchmark
        try:
            end_memory = process.memory_info().rss / (1024 * 1024)
            memory_used = end_memory - start_memory
        except:
            memory_used = 0
        
        # Calculate statistics
        if execution_times:
            total_time = sum(execution_times)
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            median_time = statistics.median(execution_times)
            std_dev = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            throughput = iterations / total_time if total_time > 0 else 0
            success_rate = successful_runs / iterations
        else:
            total_time = avg_time = min_time = max_time = median_time = std_dev = throughput = 0
            success_rate = 0
        
        result = BenchmarkResult(
            test_name=test_name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            throughput=throughput,
            memory_used_mb=memory_used,
            success_rate=success_rate,
            errors=errors[:10]  # Keep first 10 errors
        )
        
        # Store result
        with self._lock:
            self.benchmark_results[test_name] = result
        
        logger.info(f"Benchmark completed: {test_name} - {avg_time:.4f}s avg, {throughput:.1f} ops/sec")
        return result
    
    def benchmark_multiple_functions(self, function_configs: List[Dict[str, Any]], 
                                   iterations: int = 100) -> Dict[str, BenchmarkResult]:
        """
        Benchmark multiple functions.
        
        Args:
            function_configs: List of config dicts with 'func', 'args', 'kwargs', 'name'
            iterations: Number of iterations per function
            
        Returns:
            Dictionary of benchmark results
        """
        results = {}
        
        for config in function_configs:
            func = config['func']
            args = config.get('args', ())
            kwargs = config.get('kwargs', {})
            name = config.get('name', getattr(func, '__name__', str(func)))
            
            try:
                result = self.benchmark_function(func, args, kwargs, iterations)
                results[name] = result
            except Exception as e:
                logger.error(f"Error benchmarking {name}: {e}")
                results[name] = BenchmarkResult(
                    test_name=name, iterations=0, total_time=0, avg_time=0,
                    min_time=0, max_time=0, median_time=0, std_dev=0,
                    throughput=0, memory_used_mb=0, success_rate=0,
                    errors=[str(e)]
                )
        
        return results
    
    def compare_implementations(self, implementations: Dict[str, Callable],
                              test_args: Tuple = (), test_kwargs: Dict = None,
                              iterations: int = 100) -> Dict[str, Any]:
        """
        Compare performance of different implementations.
        
        Args:
            implementations: Dict of name -> function mappings
            test_args: Common test arguments
            test_kwargs: Common test keyword arguments
            iterations: Number of test iterations
            
        Returns:
            Comparison results with rankings
        """
        test_kwargs = test_kwargs or {}
        
        logger.info(f"Comparing {len(implementations)} implementations")
        
        # Benchmark all implementations
        results = {}
        for name, func in implementations.items():
            try:
                result = self.benchmark_function(func, test_args, test_kwargs, iterations)
                results[name] = result
            except Exception as e:
                logger.error(f"Error benchmarking {name}: {e}")
        
        # Create comparison
        if results:
            # Sort by average time (fastest first)
            sorted_results = sorted(results.items(), key=lambda x: x[1].avg_time)
            
            # Calculate relative performance
            fastest_time = sorted_results[0][1].avg_time if sorted_results else 0
            
            comparison = {
                'fastest_implementation': sorted_results[0][0] if sorted_results else None,
                'results': {},
                'rankings': []
            }
            
            for rank, (name, result) in enumerate(sorted_results, 1):
                relative_speed = fastest_time / result.avg_time if result.avg_time > 0 else 0
                
                comparison['results'][name] = {
                    'benchmark': asdict(result),
                    'rank': rank,
                    'relative_speed': relative_speed,
                    'speed_description': self._get_speed_description(relative_speed)
                }
                
                comparison['rankings'].append({
                    'rank': rank,
                    'name': name,
                    'avg_time': result.avg_time,
                    'throughput': result.throughput
                })
            
            return comparison
        
        return {'error': 'No successful benchmarks'}
    
    def _get_speed_description(self, relative_speed: float) -> str:
        """Get human-readable speed description"""
        if relative_speed >= 1.0:
            return "baseline"
        elif relative_speed >= 0.8:
            return "slightly slower"
        elif relative_speed >= 0.5:
            return "moderately slower"
        elif relative_speed >= 0.2:
            return "much slower"
        else:
            return "significantly slower"
    
    def benchmark_parallel_vs_sequential(self, func: Callable, test_data: List[Any],
                                       max_workers: int = 4) -> Dict[str, Any]:
        """
        Compare parallel vs sequential execution performance.
        
        Args:
            func: Function to test
            test_data: List of test inputs
            max_workers: Maximum number of parallel workers
            
        Returns:
            Comparison of parallel vs sequential performance
        """
        logger.info(f"Benchmarking parallel vs sequential with {len(test_data)} items")
        
        # Sequential benchmark
        def sequential_execution():
            results = []
            for item in test_data:
                results.append(func(item))
            return results
        
        # Parallel benchmark
        def parallel_execution():
            results = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_item = {executor.submit(func, item): item for item in test_data}
                for future in as_completed(future_to_item):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Parallel execution error: {e}")
            return results
        
        # Benchmark both approaches
        sequential_result = self.benchmark_function(sequential_execution, iterations=5)
        parallel_result = self.benchmark_function(parallel_execution, iterations=5)
        
        # Calculate speedup
        speedup = sequential_result.avg_time / parallel_result.avg_time if parallel_result.avg_time > 0 else 0
        
        return {
            'sequential': asdict(sequential_result),
            'parallel': asdict(parallel_result),
            'speedup': speedup,
            'efficiency': speedup / max_workers,
            'test_data_size': len(test_data),
            'max_workers': max_workers,
            'recommendation': 'parallel' if speedup > 1.2 else 'sequential'
        }
    
    def profile_memory_usage(self, func: Callable, args: Tuple = (), kwargs: Dict = None) -> Dict[str, Any]:
        """
        Profile memory usage of a function.
        
        Args:
            func: Function to profile
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Memory usage profile
        """
        kwargs = kwargs or {}
        
        try:
            import tracemalloc
            import psutil
            
            # Start memory tracing
            tracemalloc.start()
            process = psutil.Process()
            
            # Initial memory
            initial_memory = process.memory_info().rss / (1024 * 1024)
            initial_traced = tracemalloc.get_traced_memory()[0] / (1024 * 1024)
            
            # Execute function
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time
            
            # Final memory
            final_memory = process.memory_info().rss / (1024 * 1024)
            final_traced, peak_traced = tracemalloc.get_traced_memory()
            final_traced = final_traced / (1024 * 1024)
            peak_traced = peak_traced / (1024 * 1024)
            
            # Get top allocations
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            top_allocations = []
            for stat in top_stats[:10]:
                top_allocations.append({
                    'file': stat.traceback.format()[-1] if stat.traceback.format() else 'unknown',
                    'size_mb': stat.size / (1024 * 1024),
                    'count': stat.count
                })
            
            tracemalloc.stop()
            
            return {
                'execution_time': execution_time,
                'memory_change_mb': final_memory - initial_memory,
                'traced_memory_change_mb': final_traced - initial_traced,
                'peak_traced_memory_mb': peak_traced,
                'top_allocations': top_allocations,
                'function_name': getattr(func, '__name__', str(func))
            }
            
        except ImportError as e:
            logger.warning(f"Memory profiling requires psutil and tracemalloc: {e}")
            return {'error': 'Required modules not available'}
        except Exception as e:
            logger.error(f"Error in memory profiling: {e}")
            return {'error': str(e)}
    
    def record_execution_time(self, function_name: str, execution_time: float):
        """Record execution time for a function"""
        with self._lock:
            self.execution_times[function_name].append(execution_time)
            
            # Maintain history size
            if len(self.execution_times[function_name]) > self.max_history:
                self.execution_times[function_name].popleft()
    
    def get_function_statistics(self, function_name: str) -> Dict[str, Any]:
        """Get statistics for a function's execution times"""
        with self._lock:
            times = list(self.execution_times[function_name])
        
        if not times:
            return {'error': 'No data available'}
        
        return {
            'function_name': function_name,
            'call_count': len(times),
            'total_time': sum(times),
            'avg_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'median_time': statistics.median(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
            'recent_times': times[-10:]  # Last 10 execution times
        }
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'timestamp': time.time(),
            'benchmark_results': {name: asdict(result) for name, result in self.benchmark_results.items()},
            'function_statistics': {},
            'profiling_active': self.is_profiling
        }
        
        # Add function statistics
        for func_name in self.execution_times:
            report['function_statistics'][func_name] = self.get_function_statistics(func_name)
        
        # Add profiling report if available
        if self.profile_stats:
            report['profiling_report'] = self.get_profile_report()
        
        return report
    
    def export_report(self, filepath: str):
        """Export performance report to file"""
        report = self.generate_performance_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Performance report exported to {filepath}")


def performance_timer(func: Callable) -> Callable:
    """Decorator to time function execution and record metrics"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            raise
        finally:
            execution_time = time.perf_counter() - start_time
            
            # Record timing (you can integrate with a global profiler instance)
            logger.debug(f"Function {func.__name__} executed in {execution_time:.4f}s, Success: {success}")
        
        return result
    
    return wrapper


def benchmark_decorator(iterations: int = 10, warmup: int = 2):
    """Decorator to automatically benchmark a function"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Normal execution
            result = func(*args, **kwargs)
            
            # Benchmark on first call (you can modify this logic)
            if not hasattr(wrapper, '_benchmarked'):
                profiler = PerformanceProfiler()
                benchmark_result = profiler.benchmark_function(func, args, kwargs, iterations, warmup)
                logger.info(f"Benchmark for {func.__name__}: {benchmark_result.avg_time:.4f}s avg")
                wrapper._benchmarked = True
                wrapper._benchmark_result = benchmark_result
            
            return result
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # Demo performance profiling
    profiler = PerformanceProfiler()
    
    # Example functions to benchmark
    def example_function_1(n: int) -> int:
        """Example function 1 - list comprehension"""
        return sum([x * x for x in range(n)])
    
    def example_function_2(n: int) -> int:
        """Example function 2 - generator expression"""
        return sum(x * x for x in range(n))
    
    def example_function_3(n: int) -> int:
        """Example function 3 - traditional loop"""
        total = 0
        for x in range(n):
            total += x * x
        return total
    
    # Benchmark individual function
    print("Benchmarking individual function...")
    result = profiler.benchmark_function(example_function_1, args=(1000,), iterations=100)
    print(f"Result: {result.avg_time:.4f}s avg, {result.throughput:.1f} ops/sec")
    
    # Compare implementations
    print("\nComparing implementations...")
    implementations = {
        'list_comprehension': example_function_1,
        'generator_expression': example_function_2,
        'traditional_loop': example_function_3
    }
    
    comparison = profiler.compare_implementations(implementations, test_args=(1000,), iterations=50)
    print(f"Fastest: {comparison['fastest_implementation']}")
    
    for name, info in comparison['results'].items():
        print(f"{name}: {info['avg_time']:.4f}s ({info['speed_description']})")
    
    # Memory profiling
    print("\nMemory profiling...")
    memory_profile = profiler.profile_memory_usage(example_function_1, args=(10000,))
    if 'error' not in memory_profile:
        print(f"Memory change: {memory_profile['memory_change_mb']:.2f}MB")
        print(f"Execution time: {memory_profile['execution_time']:.4f}s")
    
    # Generate report
    report = profiler.generate_performance_report()
    print(f"\nPerformance report generated with {len(report['benchmark_results'])} benchmarks")