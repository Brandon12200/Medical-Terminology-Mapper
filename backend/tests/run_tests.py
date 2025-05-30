#!/usr/bin/env python3
"""
Test runner for Medical Terminology Mapper.
Runs all tests and reports results with timing information.
"""

import os
import sys
import unittest
import time
import logging
import argparse
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def discover_and_run_tests(
    test_dir: str = None, 
    pattern: str = 'test_*.py',
    verbose: bool = False,
    run_benchmarks: bool = False
) -> Dict[str, Any]:
    """
    Discover and run all tests in the specified directory.
    
    Args:
        test_dir: Directory containing tests (defaults to script directory)
        pattern: Pattern to match test files
        verbose: Whether to show verbose output
        run_benchmarks: Whether to run benchmark tests
        
    Returns:
        Dict containing test results and timing information
    """
    start_time = time.time()
    
    # Default to the directory containing this script
    if test_dir is None:
        test_dir = os.path.dirname(os.path.abspath(__file__))
    
    logger.info(f"Discovering tests in {test_dir} with pattern '{pattern}'")
    
    # Set verbosity level
    verbosity = 2 if verbose else 1
    
    # Skip benchmark tests unless explicitly requested
    if not run_benchmarks:
        pattern = pattern.replace('*', '[!benchmark_]*')
        logger.info(f"Skipping benchmark tests. Run with --benchmarks to include them.")
    
    # Discover and load tests
    try:
        test_suite = unittest.defaultTestLoader.discover(
            test_dir,
            pattern=pattern
        )
        
        # Count tests
        test_count = 0
        for suite in test_suite:
            for test_case in suite:
                test_count += test_case.countTestCases()
        
        logger.info(f"Found {test_count} tests to run")
        
        # Run tests
        test_runner = unittest.TextTestRunner(verbosity=verbosity)
        test_result = test_runner.run(test_suite)
        
        # Calculate duration
        end_time = time.time()
        duration = end_time - start_time
        
        # Compile results
        results = {
            'total_tests': test_result.testsRun,
            'failures': len(test_result.failures),
            'errors': len(test_result.errors),
            'skipped': len(test_result.skipped),
            'duration': duration,
            'success': test_result.wasSuccessful()
        }
        
        # Report results
        logger.info(f"Test Summary: {results['total_tests']} tests run in {duration:.2f} seconds")
        logger.info(f"Results: {results['failures']} failures, {results['errors']} errors, {results['skipped']} skipped")
        if results['success']:
            logger.info("SUCCESS: All tests passed!")
        else:
            logger.error("FAILURE: Some tests failed or had errors")
        
        return results
    
    except Exception as e:
        logger.error(f"Error discovering or running tests: {e}")
        return {
            'total_tests': 0,
            'failures': 0,
            'errors': 1,
            'skipped': 0,
            'duration': time.time() - start_time,
            'success': False,
            'error_message': str(e)
        }

def main():
    """Main entry point for test runner."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run tests for Medical Terminology Mapper')
    parser.add_argument('--dir', '-d', help='Directory containing tests')
    parser.add_argument('--pattern', '-p', default='test_*.py', help='Pattern to match test files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose output')
    parser.add_argument('--benchmarks', '-b', action='store_true', help='Run benchmark tests')
    args = parser.parse_args()
    
    # Run tests
    results = discover_and_run_tests(
        test_dir=args.dir,
        pattern=args.pattern,
        verbose=args.verbose,
        run_benchmarks=args.benchmarks
    )
    
    # Set exit code based on test success
    sys.exit(0 if results['success'] else 1)

if __name__ == '__main__':
    main()