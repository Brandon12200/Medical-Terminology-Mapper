#!/usr/bin/env python3
"""
Command-line interface (CLI) for Medical Terminology Mapper.

This script provides a command-line interface for mapping medical terminology
to standardized codes, with support for batch processing and configuration options.
"""

import argparse
import sys
import logging
import json
import csv
import os
import time
from typing import List, Dict, Any, Optional, Tuple, Union

# Add the parent directory to the path to allow running from any location
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import application modules
try:
    from app.standards.terminology.mapper import TerminologyMapper
except ImportError:
    try:
        from standards.terminology.mapper import TerminologyMapper
    except ImportError:
        print("Error: TerminologyMapper module not found")
        sys.exit(1)

# Import configuration manager
try:
    from app.standards.terminology.configure_mappings import MappingConfiguration
except ImportError:
    try:
        from standards.terminology.configure_mappings import MappingConfiguration
    except ImportError:
        # MappingConfiguration is optional
        MappingConfiguration = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_argparse() -> argparse.ArgumentParser:
    """Set up command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description='Map medical terms to standardized terminology codes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Map a single term
  python map_terms.py --term "diabetes mellitus type 2" --system snomed
  
  # Map a term with context
  python map_terms.py --term "a1c" --system loinc --context "laboratory test"
  
  # Use specific fuzzy matching algorithm
  python map_terms.py --term "hypertenshun" --fuzzy-algorithm token
  
  # Enable medical abbreviation expansion
  python map_terms.py --term "HTN" --match-abbreviations
  
  # Adjust context influence weight
  python map_terms.py --term "glucose" --context "diabetes monitoring" --context-weight 0.5
  
  # Map a list of terms from a file
  python map_terms.py --input terms.txt --output mappings.json
  
  # Process a batch CSV file with fuzzy matching
  python map_terms.py --batch input.csv --output mappings.csv --format csv --fuzzy-algorithm cosine
  
  # Use custom threshold with strict matching
  python map_terms.py --term "hypertension" --threshold 0.8 --strict-match
  
  # Add a custom mapping to the database
  python map_terms.py --add-custom --term "heart condition" --system snomed --code "56265001" --display "Heart disease"
"""
    )
    
    # Term input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--term', '-t', help='Single term to map')
    input_group.add_argument('--input', '-i', help='Input file with terms (one per line)')
    input_group.add_argument('--batch', '-b', help='Batch input file (CSV with headers)')
    
    # System/vocabulary (specifies which terminology system to map to)
    parser.add_argument('--system', '-s', choices=['snomed', 'loinc', 'rxnorm', 'auto'],
                      help='Terminology system to map to (default: auto)', default='auto')
                      
    # Context (optional)
    parser.add_argument('--context', '-c', help='Context for the term to improve mapping accuracy')
    
    # Output options
    parser.add_argument('--output', '-o', help='Output file for results (default: stdout)')
    parser.add_argument('--format', choices=['json', 'csv', 'text'], default='json',
                      help='Output format (default: json)')
    
    # Matching options
    parser.add_argument('--threshold', '-th', type=float, default=0.7,
                      help='Minimum confidence threshold (0.0-1.0, default: 0.7)')
    parser.add_argument('--no-fuzzy', action='store_true',
                      help='Disable fuzzy matching')
    parser.add_argument('--max-results', type=int, default=1,
                      help='Maximum number of results per term (default: 1)')
    
    # Fuzzy matching options
    fuzzy_group = parser.add_argument_group('Fuzzy matching options')
    fuzzy_group.add_argument('--fuzzy-algorithm', choices=['auto', 'ratio', 'partial', 'token', 'levenshtein', 'cosine'], 
                           default='auto', help='Preferred fuzzy matching algorithm (default: auto)')
    fuzzy_group.add_argument('--match-abbreviations', action='store_true',
                           help='Enable matching of medical abbreviations')
    fuzzy_group.add_argument('--context-weight', type=float, default=0.3,
                           help='Weight for context-based adjustments (0.0-1.0, default: 0.3)')
    fuzzy_group.add_argument('--strict-match', action='store_true',
                           help='Only return high-confidence matches (>80%)')
    
    # Database options
    parser.add_argument('--data-dir', help='Directory containing terminology databases')
    parser.add_argument('--config', help='Path to configuration file')
    
    # Advanced options
    parser.add_argument('--add-custom', action='store_true',
                      help='Add custom mapping for a term (requires --code and --display)')
    parser.add_argument('--code', help='Code for custom mapping')
    parser.add_argument('--display', help='Display name for custom mapping')
    
    return parser

def initialize_mapper(args) -> TerminologyMapper:
    """
    Initialize the terminology mapper with appropriate configuration.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Initialized TerminologyMapper instance
    """
    # Determine data directory
    data_dir = args.data_dir
    if not data_dir:
        # Default to the standard data directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, 'data', 'terminology')
    
    # Make sure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Load configuration
    config_path = args.config
    if not config_path:
        config_path = os.path.join(data_dir, 'mapping_config.json')
    
    config_manager = MappingConfiguration(config_path)
    
    # Get configuration
    config = config_manager.config
    
    # Override config with command-line arguments
    config['data_dir'] = data_dir
    
    # Basic matching options
    config['matching']['enable_fuzzy_matching'] = not args.no_fuzzy
    config['matching']['default_threshold'] = args.threshold
    config['matching']['max_results'] = args.max_results
    
    # Enhanced fuzzy matching options
    if not 'fuzzy' in config:
        config['fuzzy'] = {}
    
    # Set fuzzy algorithm preference
    config['fuzzy']['preferred_algorithm'] = args.fuzzy_algorithm
    
    # Configure abbreviation matching
    config['fuzzy']['match_abbreviations'] = args.match_abbreviations
    
    # Set context weight for adjustments
    config['fuzzy']['context_weight'] = args.context_weight
    
    # Set strict matching mode if enabled
    if args.strict_match:
        # Override threshold for strict matching
        config['matching']['default_threshold'] = max(0.8, args.threshold)
        config['fuzzy']['strict_mode'] = True
    else:
        config['fuzzy']['strict_mode'] = False
    
    # Initialize mapper
    mapper = TerminologyMapper(config)
    if not mapper.initialize():
        logger.error("Failed to initialize terminology mapper")
        sys.exit(1)
    
    return mapper

def map_single_term(mapper: TerminologyMapper, term: str, system: str = 'auto',
                   context: Optional[str] = None, threshold: float = 0.7) -> Dict[str, Any]:
    """
    Map a single term to standardized terminology.
    
    Args:
        mapper: Terminology mapper
        term: Term to map
        system: Terminology system to map to
        context: Optional context for the term
        threshold: Confidence threshold
        
    Returns:
        Mapping result
    """
    start_time = time.time()
    
    # Preprocess the term and context
    clean_term = term.strip()
    
    # Create mapping options dictionary
    options = {
        'threshold': threshold,
        'with_context': True if context else False
    }
    
    if system == 'auto':
        # Auto-detect system
        result = {"error": "Auto mode not implemented"}
    else:
        # Map to specified system
        result = mapper.map_term(clean_term, system, context=context)
    
    duration = time.time() - start_time
    
    # Add timing information
    result['mapping_time_ms'] = round(duration * 1000, 2)
    
    # Add context information if available
    if context and result.get('found', False):
        if not 'context_info' in result:
            result['context_info'] = {
                'provided_context': context,
                'used_for_mapping': True
            }
            
        # If context enhanced the result, add additional information
        if result.get('context_enhanced', False):
            result['context_info']['enhanced_match'] = True
            if 'context_term' in result:
                result['context_info']['matched_context_term'] = result.pop('context_term')
    
    return result

def process_term_list(mapper: TerminologyMapper, terms: List[str], system: str = 'auto',
                     context: Optional[str] = None, threshold: float = 0.7) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Process a list of terms.
    
    Args:
        mapper: Terminology mapper
        terms: List of terms to map
        system: Terminology system to map to
        context: Optional context for the terms
        threshold: Confidence threshold
        
    Returns:
        Tuple of (list of mapping results, summary dictionary)
    """
    results = []
    
    # Create mapping options dictionary
    options = {
        'threshold': threshold,
        'with_context': True if context else False
    }
    
    start_time = time.time()
    for term in terms:
        term = term.strip()
        if not term:
            continue
        
        # Map the term using the map_single_term function for consistency
        result = map_single_term(mapper, term, system, context, threshold)
        results.append(result)
    
    total_duration = time.time() - start_time
    
    # Add summary information
    found_count = sum(1 for r in results if r.get('found', False))
    fuzzy_count = sum(1 for r in results if r.get('found', False) and r.get('match_type', '') != 'exact')
    context_enhanced = sum(1 for r in results if r.get('context_info', {}).get('enhanced_match', False))
    
    summary = {
        'total_terms': len(results),
        'found_terms': found_count,
        'fuzzy_matches': fuzzy_count,
        'context_enhanced': context_enhanced,
        'mapping_rate': round((found_count / len(results) * 100), 2) if results else 0,
        'fuzzy_rate': round((fuzzy_count / found_count * 100), 2) if found_count else 0,
        'total_time_ms': round(total_duration * 1000, 2),
        'avg_time_per_term_ms': round((total_duration * 1000) / len(results), 2) if results else 0
    }
    
    return results, summary

def process_batch_file(mapper: TerminologyMapper, batch_file: str,
                      threshold: float = 0.7) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Process a batch file of terms with metadata.
    
    Args:
        mapper: Terminology mapper
        batch_file: Path to batch file (CSV)
        threshold: Confidence threshold
        
    Returns:
        Tuple of (list of mapping results, summary dictionary)
    """
    results = []
    
    start_time = time.time()
    try:
        with open(batch_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Extract term, system and context
                term = row.get('term', '').strip()
                if not term:
                    continue
                    
                system = row.get('system', 'auto')
                context = row.get('context')
                
                # Allow per-row threshold override
                row_threshold = threshold
                if 'threshold' in row:
                    try:
                        row_threshold = float(row.get('threshold'))
                    except (ValueError, TypeError):
                        pass
                
                # Map the term using the map_single_term function for consistency
                result = map_single_term(mapper, term, system, context, row_threshold)
                
                # Add original data to result
                for key, value in row.items():
                    if key not in result:
                        result[f'input_{key}'] = value
                
                results.append(result)
    
    except Exception as e:
        logger.error(f"Error processing batch file: {e}")
        return results, {'error': str(e)}
    
    total_duration = time.time() - start_time
    
    # Add summary information
    found_count = sum(1 for r in results if r.get('found', False))
    fuzzy_count = sum(1 for r in results if r.get('found', False) and r.get('match_type', '') != 'exact')
    context_enhanced = sum(1 for r in results if r.get('context_info', {}).get('enhanced_match', False))
    
    summary = {
        'total_terms': len(results),
        'found_terms': found_count,
        'fuzzy_matches': fuzzy_count,
        'context_enhanced': context_enhanced,
        'mapping_rate': round((found_count / len(results) * 100), 2) if results else 0,
        'fuzzy_rate': round((fuzzy_count / found_count * 100), 2) if found_count else 0,
        'total_time_ms': round(total_duration * 1000, 2),
        'avg_time_per_term_ms': round((total_duration * 1000) / len(results), 2) if results else 0
    }
    
    # Additional batch-specific statistics
    if results:
        # Count systems used
        system_counts = {}
        for r in results:
            if r.get('found', False):
                sys_name = r.get('system', 'unknown')
                system_counts[sys_name] = system_counts.get(sys_name, 0) + 1
        
        summary['system_distribution'] = system_counts
        
        # Count match types
        match_types = {}
        for r in results:
            if r.get('found', False):
                match_type = r.get('match_type', 'unknown')
                match_types[match_type] = match_types.get(match_type, 0) + 1
        
        summary['match_types'] = match_types
    
    return results, summary

def output_results(results: Union[Dict[str, Any], Tuple[List[Dict[str, Any]], Dict[str, Any]], List[Dict[str, Any]]],
                  output_format: str = 'json', output_file: Optional[str] = None) -> None:
    """
    Output results in the specified format.
    
    Args:
        results: Results to output
        output_format: Format to use (json, csv, text)
        output_file: Optional output file (stdout if None)
    """
    if output_file:
        if output_format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
                
        elif output_format == 'csv':
            # Handle different result structures
            if isinstance(results, dict):
                # Single term result
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['term', 'found', 'system', 'code', 'display', 'confidence'])
                    writer.writerow([
                        results.get('term', ''),
                        results.get('found', False),
                        results.get('system', ''),
                        results.get('code', ''),
                        results.get('display', ''),
                        results.get('confidence', 0.0)
                    ])
            elif isinstance(results, tuple) and len(results) == 2:
                # Results with summary
                results_list, summary = results
                
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    # Write summary as comments
                    f.write('# Mapping Summary\n')
                    for key, value in summary.items():
                        f.write(f'# {key}: {value}\n')
                    f.write('#\n')
                    
                    # Write results
                    if results_list:
                        # Get all fields from first result
                        fieldnames = list(results_list[0].keys())
                        
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(results_list)
            else:
                # Standard list of results
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    if results:
                        fieldnames = list(results[0].keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(results)
                    else:
                        f.write('# No results found\n')
        
        elif output_format == 'text':
            with open(output_file, 'w', encoding='utf-8') as f:
                if isinstance(results, dict):
                    # Single term result
                    f.write(f"Term: {results.get('term', '')}\n")
                    f.write(f"Found: {results.get('found', False)}\n")
                    f.write(f"System: {results.get('system', '')}\n")
                    f.write(f"Code: {results.get('code', '')}\n")
                    f.write(f"Display: {results.get('display', '')}\n")
                    f.write(f"Confidence: {results.get('confidence', 0.0)}\n")
                elif isinstance(results, tuple) and len(results) == 2:
                    # Results with summary
                    results_list, summary = results
                    
                    # Write summary
                    f.write("=== Mapping Summary ===\n")
                    for key, value in summary.items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n=== Results ===\n")
                    
                    # Write each result
                    for i, result in enumerate(results_list):
                        f.write(f"\n--- Result {i+1} ---\n")
                        for key, value in result.items():
                            f.write(f"{key}: {value}\n")
                else:
                    # Standard list of results
                    for i, result in enumerate(results):
                        f.write(f"\n--- Result {i+1} ---\n")
                        for key, value in result.items():
                            f.write(f"{key}: {value}\n")
        
        logger.info(f"Results written to {output_file}")
    else:
        # Output to stdout
        if output_format == 'json':
            print(json.dumps(results, indent=2))
        elif output_format == 'csv':
            if isinstance(results, dict):
                # Single term result
                print(f"term,found,system,code,display,confidence")
                print(f"{results.get('term', '')},{results.get('found', False)},{results.get('system', '')},{results.get('code', '')},{results.get('display', '')},{results.get('confidence', 0.0)}")
            elif isinstance(results, tuple) and len(results) == 2:
                # Results with summary
                results_list, summary = results
                
                # Print summary
                print("# Mapping Summary")
                for key, value in summary.items():
                    print(f"# {key}: {value}")
                print("#")
                
                # Print results as CSV
                if results_list:
                    fieldnames = list(results_list[0].keys())
                    print(','.join(fieldnames))
                    
                    for result in results_list:
                        print(','.join(str(result.get(field, '')) for field in fieldnames))
            else:
                # Standard list of results
                if results:
                    fieldnames = list(results[0].keys())
                    print(','.join(fieldnames))
                    
                    for result in results:
                        print(','.join(str(result.get(field, '')) for field in fieldnames))
                else:
                    print("# No results found")
        elif output_format == 'text':
            if isinstance(results, dict):
                # Single term result
                print(f"Term: {results.get('term', '')}")
                print(f"Found: {results.get('found', False)}")
                print(f"System: {results.get('system', '')}")
                print(f"Code: {results.get('code', '')}")
                print(f"Display: {results.get('display', '')}")
                print(f"Confidence: {results.get('confidence', 0.0)}")
            elif isinstance(results, tuple) and len(results) == 2:
                # Results with summary
                results_list, summary = results
                
                # Print summary
                print("=== Mapping Summary ===")
                for key, value in summary.items():
                    print(f"{key}: {value}")
                print("\n=== Results ===")
                
                # Print each result
                for i, result in enumerate(results_list):
                    print(f"\n--- Result {i+1} ---")
                    for key, value in result.items():
                        print(f"{key}: {value}")
            else:
                # Standard list of results
                for i, result in enumerate(results):
                    print(f"\n--- Result {i+1} ---")
                    for key, value in result.items():
                        print(f"{key}: {value}")

def add_custom_mapping(mapper: TerminologyMapper, term: str, system: str, code: str, display: str) -> bool:
    """
    Add a custom mapping to the terminology database.
    
    Args:
        mapper: Terminology mapper
        term: Term to map
        system: Terminology system
        code: Code to map to
        display: Display name for the code
        
    Returns:
        bool: True if the mapping was added successfully
    """
    try:
        success = mapper.add_custom_mapping(system, term, code, display)
        if success:
            logger.info(f"Successfully added custom mapping for '{term}' to {system}:{code}")
        else:
            logger.error(f"Failed to add custom mapping for '{term}'")
        return success
    except Exception as e:
        logger.error(f"Error adding custom mapping: {e}")
        return False

def main():
    """Main entry point for the CLI."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    try:
        # Initialize the terminology mapper
        mapper = initialize_mapper(args)
        
        # Check if we're adding a custom mapping
        if args.add_custom:
            if not args.term or not args.system or not args.code or not args.display:
                logger.error("To add a custom mapping, you must provide --term, --system, --code, and --display")
                sys.exit(1)
                
            success = add_custom_mapping(mapper, args.term, args.system, args.code, args.display)
            sys.exit(0 if success else 1)
        
        # Process input based on provided arguments
        if args.term:
            # Single term mapping
            result = map_single_term(mapper, args.term, args.system, args.context, args.threshold)
            
            # Show fuzzy matching details if available
            if result.get('found', False) and result.get('match_type', '') != 'exact':
                logger.info(f"Fuzzy match found using '{result.get('match_type', 'unknown')}' algorithm with confidence {result.get('score', 0):.1f}%")
                
            # Show context enhancement if used
            if result.get('context_info', {}).get('enhanced_match', False):
                context_term = result.get('context_info', {}).get('matched_context_term', 'context')
                logger.info(f"Match enhanced using context term '{context_term}'")
                
            output_results(result, args.format, args.output)
            
        elif args.input:
            # Process term list from file
            try:
                with open(args.input, 'r', encoding='utf-8') as f:
                    terms = [line.strip() for line in f if line.strip()]
                
                logger.info(f"Processing {len(terms)} terms from {args.input}")
                results, summary = process_term_list(mapper, terms, args.system, args.context, args.threshold)
                
                # Log summary information
                logger.info(f"Found mappings for {summary['found_terms']} of {summary['total_terms']} terms ({summary['mapping_rate']}%)")
                if summary.get('fuzzy_matches', 0) > 0:
                    logger.info(f"Used fuzzy matching for {summary['fuzzy_matches']} terms ({summary['fuzzy_rate']}% of matches)")
                if summary.get('context_enhanced', 0) > 0:
                    logger.info(f"Context improved {summary['context_enhanced']} matches")
                    
                output_results((results, summary), args.format, args.output)
                
            except Exception as e:
                logger.error(f"Error processing input file: {e}")
                sys.exit(1)
                
        elif args.batch:
            # Process batch file
            try:
                logger.info(f"Processing batch file: {args.batch}")
                results, summary = process_batch_file(mapper, args.batch, args.threshold)
                
                # Log summary information
                logger.info(f"Found mappings for {summary['found_terms']} of {summary['total_terms']} terms ({summary['mapping_rate']}%)")
                if summary.get('fuzzy_matches', 0) > 0:
                    logger.info(f"Used fuzzy matching for {summary['fuzzy_matches']} terms ({summary['fuzzy_rate']}% of matches)")
                if summary.get('context_enhanced', 0) > 0:
                    logger.info(f"Context improved {summary['context_enhanced']} matches")
                
                # Log system distribution if available
                if 'system_distribution' in summary:
                    logger.info("Terminology system distribution:")
                    for system, count in summary['system_distribution'].items():
                        logger.info(f"  - {system}: {count} terms")
                
                # Log match types if available
                if 'match_types' in summary:
                    logger.info("Match type distribution:")
                    for match_type, count in summary['match_types'].items():
                        logger.info(f"  - {match_type}: {count} terms")
                
                output_results((results, summary), args.format, args.output)
            except Exception as e:
                logger.error(f"Error processing batch file: {e}")
                sys.exit(1)
        
        # Log final statistics if available
        try:
            stats = mapper.get_statistics()
            if isinstance(stats, dict) and 'total_requests' in stats:
                success_rate = stats.get('success_rate', 0)
                logger.info(f"Mapping statistics: {success_rate:.1f}% success rate over {stats['total_requests']} requests")
        except (AttributeError, KeyError):
            pass
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'mapper' in locals() and mapper:
            if hasattr(mapper, 'close'):
                mapper.close()

if __name__ == "__main__":
    main()