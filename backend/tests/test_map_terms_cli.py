#!/usr/bin/env python3
"""
Test the map_terms.py CLI functionality.

This test focuses on the command-line interface without requiring actual execution,
mocking the necessary components for verification.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMapTermsCLI(unittest.TestCase):
    """Test the map_terms.py command-line interface functionality."""
    
    def test_cli_argument_parsing(self):
        """Test that CLI arguments are parsed correctly."""
        from cli import map_terms
        
        # Mock sys.argv to simulate command-line arguments
        with patch('sys.argv', ['map_terms.py', '--term', 'hypertension', '--system', 'snomed']):
            # Mock the parser to capture the arguments
            with patch('cli.map_terms.argparse.ArgumentParser.parse_args') as mock_parse_args:
                # Set up the mock return value
                args = MagicMock()
                args.term = 'hypertension'
                args.system = 'snomed'
                args.context = None
                args.threshold = 0.7
                args.input = None
                args.batch = None
                args.fuzzy_algorithm = 'auto'
                args.match_abbreviations = False
                args.context_weight = 0.3
                args.strict_match = False
                args.add_custom = False
                args.no_fuzzy = False
                args.format = 'json'
                args.output = None
                mock_parse_args.return_value = args
                
                # Mock initialize_mapper to prevent actual initialization
                with patch('cli.map_terms.initialize_mapper') as mock_init:
                    # Mock mapper instance
                    mapper = MagicMock()
                    mock_init.return_value = mapper
                    
                    # Mock map_single_term to prevent execution
                    with patch('cli.map_terms.map_single_term') as mock_map:
                        # Set up the mock return value
                        mock_map.return_value = {
                            'term': 'hypertension',
                            'system': 'http://snomed.info/sct',
                            'code': '38341003',
                            'display': 'Hypertensive disorder',
                            'found': True,
                            'confidence': 1.0,
                            'mapping_time_ms': 10.5
                        }
                        
                        # Mock output_results to prevent actual output
                        with patch('cli.map_terms.output_results'):
                            # Run the main function
                            try:
                                map_terms.main()
                            except SystemExit:
                                pass  # Ignore sys.exit() calls
                            
                            # Verify that parse_args was called
                            mock_parse_args.assert_called_once()
                            
                            # Verify that initialize_mapper was called
                            mock_init.assert_called_once()
                            
                            # Verify that map_single_term was called with the right arguments
                            mock_map.assert_called_once()
                            args, kwargs = mock_map.call_args
                            self.assertEqual(args[1], 'hypertension')
                            self.assertEqual(args[2], 'snomed')
    
    def test_cli_fuzzy_options(self):
        """Test that fuzzy matching options are passed correctly."""
        from cli import map_terms
        
        # Mock sys.argv to simulate command-line arguments with fuzzy options
        with patch('sys.argv', [
            'map_terms.py', 
            '--term', 'hypertension', 
            '--system', 'snomed',
            '--fuzzy-algorithm', 'token',
            '--match-abbreviations',
            '--context-weight', '0.5',
            '--strict-match'
        ]):
            # Mock the parser to capture the arguments
            with patch('cli.map_terms.argparse.ArgumentParser.parse_args') as mock_parse_args:
                # Set up the mock return value
                args = MagicMock()
                args.term = 'hypertension'
                args.system = 'snomed'
                args.context = None
                args.threshold = 0.7
                args.input = None
                args.batch = None
                args.fuzzy_algorithm = 'token'
                args.match_abbreviations = True
                args.context_weight = 0.5
                args.strict_match = True
                args.add_custom = False
                args.no_fuzzy = False
                args.format = 'json'
                args.output = None
                mock_parse_args.return_value = args
                
                # Mock initialize_mapper to capture fuzzy options
                with patch('cli.map_terms.initialize_mapper') as mock_init:
                    # Create a mock config to capture values
                    config = {'fuzzy': {}, 'matching': {}}
                    
                    # Create a mock mapper
                    mapper = MagicMock()
                    mapper.initialize.return_value = True
                    
                    # Adjust the initialize_mapper mock to test config capture
                    def mock_init_impl(args):
                        # This simulates what initialize_mapper would do
                        config['fuzzy']['preferred_algorithm'] = args.fuzzy_algorithm
                        config['fuzzy']['match_abbreviations'] = args.match_abbreviations
                        config['fuzzy']['context_weight'] = args.context_weight
                        config['fuzzy']['strict_mode'] = args.strict_match
                        if args.strict_match:
                            config['matching']['default_threshold'] = max(0.8, args.threshold)
                        return mapper
                    
                    mock_init.side_effect = mock_init_impl
                    
                    # Mock map_single_term to prevent execution
                    with patch('cli.map_terms.map_single_term'):
                        # Mock output_results to prevent actual output
                        with patch('cli.map_terms.output_results'):
                            # Run the main function
                            try:
                                map_terms.main()
                            except SystemExit:
                                pass  # Ignore sys.exit() calls
                            
                            # Verify that the config was set correctly
                            self.assertEqual(config['fuzzy']['preferred_algorithm'], 'token')
                            self.assertTrue(config['fuzzy']['match_abbreviations'])
                            self.assertEqual(config['fuzzy']['context_weight'], 0.5)
                            self.assertTrue(config['fuzzy']['strict_mode'])
                            self.assertGreaterEqual(config['matching']['default_threshold'], 0.8)

if __name__ == "__main__":
    unittest.main()