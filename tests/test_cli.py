#!/usr/bin/env python3
"""
Test script for the Medical Terminology Mapper CLI.

This script tests the CLI with various scenarios to ensure proper functionality
of the fuzzy matching, context-aware mapping, and batch processing features.
"""

import os
import sys
import subprocess
import json
import csv
import time
import argparse
from typing import List, Dict, Any, Optional

def run_cli_command(command: str) -> str:
    """Run a CLI command and return its output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running command: {result.stderr}")
        return ""
    
    return result.stdout

def test_single_term_mapping():
    """Test mapping a single term with various options."""
    tests = [
        {
            "name": "Basic exact match",
            "command": "python map_terms.py --term 'diabetes mellitus type 2' --system snomed",
            "check": lambda output: "found" in output and "true" in output.lower()
        },
        {
            "name": "Fuzzy match with token algorithm",
            "command": "python map_terms.py --term 'diabetes type 2 mellitus' --system snomed --fuzzy-algorithm token",
            "check": lambda output: "found" in output and "true" in output.lower() and "token" in output.lower()
        },
        {
            "name": "Abbreviation match",
            "command": "python map_terms.py --term 'HTN' --system snomed --match-abbreviations",
            "check": lambda output: "found" in output and "true" in output.lower()
        },
        {
            "name": "Context-enhanced match",
            "command": "python map_terms.py --term 'glucose' --system loinc --context 'diabetes monitoring' --context-weight 0.5",
            "check": lambda output: "found" in output and "true" in output.lower()
        },
        {
            "name": "Strict match mode",
            "command": "python map_terms.py --term 'hypertension' --system snomed --strict-match",
            "check": lambda output: "found" in output and "true" in output.lower() and "confidence" in output.lower()
        }
    ]
    
    results = []
    for test in tests:
        print(f"\nTesting: {test['name']}")
        output = run_cli_command(test["command"])
        passed = test["check"](output)
        results.append({
            "name": test["name"],
            "passed": passed,
            "output": output[:100] + "..." if len(output) > 100 else output
        })
        print(f"Result: {'PASS' if passed else 'FAIL'}")
    
    return results

def test_batch_processing():
    """Test batch processing functionality."""
    # Ensure sample file exists
    if not os.path.exists("sample_terms.csv"):
        print("Sample terms file not found. Please create sample_terms.csv first.")
        return []
    
    tests = [
        {
            "name": "Basic batch processing",
            "command": "python map_terms.py --batch sample_terms.csv --output batch_results.json",
            "check": lambda: os.path.exists("batch_results.json") and check_json_results("batch_results.json")
        },
        {
            "name": "Batch with fuzzy matching",
            "command": "python map_terms.py --batch sample_terms.csv --output batch_fuzzy_results.json --fuzzy-algorithm token",
            "check": lambda: os.path.exists("batch_fuzzy_results.json") and check_json_results("batch_fuzzy_results.json")
        },
        {
            "name": "Batch with abbreviations",
            "command": "python map_terms.py --batch sample_terms.csv --output batch_abbrev_results.json --match-abbreviations",
            "check": lambda: os.path.exists("batch_abbrev_results.json") and check_json_results("batch_abbrev_results.json")
        },
        {
            "name": "Batch with all options",
            "command": "python map_terms.py --batch sample_terms.csv --output batch_all_results.json --match-abbreviations --fuzzy-algorithm cosine --context-weight 0.5",
            "check": lambda: os.path.exists("batch_all_results.json") and check_json_results("batch_all_results.json")
        }
    ]
    
    results = []
    for test in tests:
        print(f"\nTesting: {test['name']}")
        output = run_cli_command(test["command"])
        passed = test["check"]()
        results.append({
            "name": test["name"],
            "passed": passed,
            "output": output[:100] + "..." if len(output) > 100 else output
        })
        print(f"Result: {'PASS' if passed else 'FAIL'}")
    
    return results

def check_json_results(file_path: str) -> bool:
    """Check if JSON results file contains valid data."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        if not isinstance(data, list) and not (isinstance(data, tuple) and len(data) == 2):
            return False
            
        # Extract results list
        results = data[0] if isinstance(data, tuple) else data
        
        # Check if we have at least some matches
        found_count = sum(1 for r in results if r.get('found', False))
        return found_count > 0
    except Exception as e:
        print(f"Error checking results: {e}")
        return False

def test_output_formats():
    """Test various output formats."""
    tests = [
        {
            "name": "JSON output",
            "command": "python map_terms.py --term 'hypertension' --format json --output json_output.json",
            "check": lambda: os.path.exists("json_output.json") and check_json_file("json_output.json")
        },
        {
            "name": "CSV output",
            "command": "python map_terms.py --term 'hypertension' --format csv --output csv_output.csv",
            "check": lambda: os.path.exists("csv_output.csv") and check_csv_file("csv_output.csv")
        },
        {
            "name": "Text output",
            "command": "python map_terms.py --term 'hypertension' --format text --output text_output.txt",
            "check": lambda: os.path.exists("text_output.txt") and check_text_file("text_output.txt")
        }
    ]
    
    results = []
    for test in tests:
        print(f"\nTesting: {test['name']}")
        output = run_cli_command(test["command"])
        passed = test["check"]()
        results.append({
            "name": test["name"],
            "passed": passed,
            "output": output[:100] + "..." if len(output) > 100 else output
        })
        print(f"Result: {'PASS' if passed else 'FAIL'}")
    
    return results

def check_json_file(file_path: str) -> bool:
    """Check if a file contains valid JSON."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return isinstance(data, dict) and 'term' in data
    except Exception:
        return False

def check_csv_file(file_path: str) -> bool:
    """Check if a file contains valid CSV."""
    try:
        with open(file_path, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)
            return 'term' in headers and 'found' in headers
    except Exception:
        return False

def check_text_file(file_path: str) -> bool:
    """Check if a file contains valid text output."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return 'Term:' in content and 'Found:' in content
    except Exception:
        return False

def clean_up_files():
    """Clean up test output files."""
    files_to_remove = [
        "batch_results.json",
        "batch_fuzzy_results.json", 
        "batch_abbrev_results.json",
        "batch_all_results.json",
        "json_output.json",
        "csv_output.csv",
        "text_output.txt"
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"Removed test file: {file}")
            except Exception as e:
                print(f"Error removing file {file}: {e}")

def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description='Test the Medical Terminology Mapper CLI')
    parser.add_argument('--cleanup', action='store_true', help='Clean up test files after running')
    args = parser.parse_args()
    
    all_results = []
    
    # Run test categories
    all_results.extend(test_single_term_mapping())
    all_results.extend(test_batch_processing())
    all_results.extend(test_output_formats())
    
    # Print summary
    passed = sum(1 for r in all_results if r["passed"])
    total = len(all_results)
    
    print("\n" + "="*50)
    print(f"Test Summary: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    print("="*50)
    
    # Print failed tests
    failed = [r for r in all_results if not r["passed"]]
    if failed:
        print("\nFailed Tests:")
        for i, test in enumerate(failed, 1):
            print(f"{i}. {test['name']}")
    
    # Clean up test files if requested
    if args.cleanup:
        clean_up_files()
    
    # Return success if all tests passed
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())