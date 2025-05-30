#!/usr/bin/env python
"""
Add custom mappings to the terminology database.

This script adds custom mappings to the embedded terminology database,
allowing users to define their own mappings for specific terms.
"""

import os
import sys
import json
import logging
import argparse
from typing import List, Dict, Any, Optional

# Try importing from both potential module paths
try:
    from app.standards.terminology.mapper import TerminologyMapper
except ImportError:
    try:
        from standards.terminology.mapper import TerminologyMapper
    except ImportError:
        # Handle case where module can't be imported
        print("Error: TerminologyMapper module not found")
        TerminologyMapper = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_mapping(term: str, system: str, code: str, display: str, data_dir: str = None) -> bool:
    """
    Add a custom mapping to the terminology database.
    
    Args:
        term: The term to map
        system: The terminology system (snomed, loinc, rxnorm)
        code: The code to map to
        display: The display name for the code
        data_dir: Optional path to data directory
        
    Returns:
        bool: True if the mapping was added successfully
    """
    if TerminologyMapper is None:
        logger.error("TerminologyMapper module not available")
        return False
        
    # Set up data directory
    if not data_dir:
        # Default to the standard data directory
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))))
        except NameError:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(sys.argv[0])))))
        data_dir = os.path.join(base_dir, 'data', 'terminology')
    
    # Create a mapper instance
    config = {"data_dir": data_dir}
    mapper = TerminologyMapper(config)
    mapper.initialize()
    
    # Add the mapping
    success = mapper.add_custom_mapping(system, term, code, display)
    
    if success:
        logger.info(f"Successfully added mapping for '{term}' to {system} code {code}")
    else:
        logger.error(f"Failed to add mapping for '{term}' to {system} code {code}")
        
    return success

def add_synonym(term: str, synonyms: List[str], data_dir: str = None) -> bool:
    """
    Add synonym mappings for a term.
    
    Args:
        term: The primary term
        synonyms: List of synonyms for the term
        data_dir: Optional path to data directory
        
    Returns:
        bool: True if synonyms were added successfully
    """
    if TerminologyMapper is None:
        logger.error("TerminologyMapper module not available")
        return False
        
    # Set up data directory
    if not data_dir:
        # Default to the standard data directory
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))))
        except NameError:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(sys.argv[0])))))
        data_dir = os.path.join(base_dir, 'data', 'terminology')
    
    # Create a mapper instance
    config = {
        "data_dir": data_dir,
        "use_fuzzy_matching": True
    }
    mapper = TerminologyMapper(config)
    mapper.initialize()
    
    # Add the synonyms
    if not hasattr(mapper, 'fuzzy_matcher') or mapper.fuzzy_matcher is None:
        logger.error("Fuzzy matcher not available, cannot add synonyms")
        return False
        
    success = mapper.add_synonyms(term, synonyms)
    
    if success:
        logger.info(f"Successfully added {len(synonyms)} synonyms for '{term}'")
    else:
        logger.error(f"Failed to add synonyms for '{term}'")
        
    return success

def add_from_file(file_path: str, data_dir: str = None) -> bool:
    """
    Add mappings from a JSON file.
    
    The JSON file should have the following structure:
    {
        "mappings": [
            {
                "term": "hypertension",
                "system": "snomed",
                "code": "38341003",
                "display": "Hypertensive disorder"
            },
            ...
        ],
        "synonyms": [
            {
                "term": "hypertension",
                "synonyms": ["HTN", "high blood pressure", "hypertensive disorder"]
            },
            ...
        ]
    }
    
    Args:
        file_path: Path to the JSON file with mappings
        data_dir: Optional path to data directory
        
    Returns:
        bool: True if all mappings were added successfully
    """
    # Load the mappings from file
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading mappings file: {e}")
        return False
    
    # Check if we have mappings
    if "mappings" not in data:
        logger.error("No mappings found in file. Expecting a 'mappings' key.")
        return False
        
    # Add each mapping
    success = True
    for mapping in data["mappings"]:
        try:
            term = mapping["term"]
            system = mapping["system"]
            code = mapping["code"]
            display = mapping["display"]
            
            result = add_mapping(term, system, code, display, data_dir)
            success = result and success
        except KeyError as e:
            logger.error(f"Missing required field in mapping: {e}")
            success = False
    
    # Check if we have synonyms
    if "synonyms" in data:
        for synonym_set in data["synonyms"]:
            try:
                term = synonym_set["term"]
                synonyms = synonym_set["synonyms"]
                
                result = add_synonym(term, synonyms, data_dir)
                success = result and success
            except KeyError as e:
                logger.error(f"Missing required field in synonym set: {e}")
                success = False
    
    return success

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Add custom mappings to terminology database')
    parser.add_argument('--term', dest='term', help='Term to map')
    parser.add_argument('--system', dest='system', choices=['snomed', 'loinc', 'rxnorm'], help='Terminology system')
    parser.add_argument('--code', dest='code', help='Code to map to')
    parser.add_argument('--display', dest='display', help='Display name for the code')
    parser.add_argument('--synonyms', dest='synonyms', nargs='+', help='Synonyms for a term')
    parser.add_argument('--file', dest='file', help='JSON file with mappings')
    parser.add_argument('--data-dir', dest='data_dir', help='Path to data directory')
    parser.add_argument('--examples', action='store_true', help='Show example mappings file format')
    args = parser.parse_args()
    
    # Check if we're showing examples
    if args.examples:
        example = {
            "mappings": [
                {
                    "term": "hypertension",
                    "system": "snomed",
                    "code": "38341003",
                    "display": "Hypertensive disorder"
                },
                {
                    "term": "hemoglobin a1c",
                    "system": "loinc",
                    "code": "4548-4",
                    "display": "Hemoglobin A1c/Hemoglobin.total in Blood"
                }
            ],
            "synonyms": [
                {
                    "term": "hypertension",
                    "synonyms": ["HTN", "high blood pressure", "hypertensive disorder"]
                },
                {
                    "term": "hemoglobin a1c",
                    "synonyms": ["A1C", "HbA1c", "glycated hemoglobin"]
                }
            ]
        }
        print("Example mappings file format:")
        print(json.dumps(example, indent=2))
        return 0
    
    # Check if we're adding from a file
    if args.file:
        success = add_from_file(args.file, args.data_dir)
        return 0 if success else 1
    
    # Check if we're adding synonyms
    if args.term and args.synonyms:
        success = add_synonym(args.term, args.synonyms, args.data_dir)
        return 0 if success else 1
    
    # Check if we're adding a mapping
    if args.term and args.system and args.code and args.display:
        success = add_mapping(args.term, args.system, args.code, args.display, args.data_dir)
        return 0 if success else 1
    
    # If we get here, we don't have enough arguments
    logger.error("Not enough arguments provided. Use --help for usage information.")
    return 1

if __name__ == "__main__":
    sys.exit(main())