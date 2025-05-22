"""
Configure and update the terminology mapping system.

This module provides functionality for configuring terminology mapping settings,
including database setup, vocabularies, matching thresholds, and custom mapping rules.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Try to import the TerminologyDatabaseUpdater from local module
try:
    from app.standards.terminology.db_updater import TerminologyDatabaseUpdater
except ImportError:
    try:
        from standards.terminology.db_updater import TerminologyDatabaseUpdater
    except ImportError:
        # Handle case where module can't be imported
        TerminologyDatabaseUpdater = None
        print("Warning: TerminologyDatabaseUpdater not found")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MappingConfiguration:
    """
    Configuration manager for terminology mapping.
    
    This class handles loading, saving, and accessing configuration settings
    for terminology mapping across the application.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Optional path to configuration file. If not provided,
                        defaults to 'mapping_config.json' in the data/terminology directory.
        """
        self.config_path = config_path
        
        if not config_path:
            # Default configuration path
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))))
            self.config_path = os.path.join(base_dir, 'data', 'terminology', 'mapping_config.json')
        
        # Default configuration settings
        self.config = {
            'vocabularies': {
                'snomed': {
                    'enabled': True,
                    'match_threshold': 0.7,
                    'system_url': 'http://snomed.info/sct',
                    'preferred_for': ['CONDITION', 'PROCEDURE', 'OBSERVATION']
                },
                'rxnorm': {
                    'enabled': True,
                    'match_threshold': 0.7,
                    'system_url': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                    'preferred_for': ['MEDICATION']
                },
                'loinc': {
                    'enabled': True,
                    'match_threshold': 0.7,
                    'system_url': 'http://loinc.org',
                    'preferred_for': ['LAB_TEST']
                }
            },
            'matching': {
                'default_threshold': 0.7,
                'enable_fuzzy_matching': True,
                'fuzzy_threshold': 0.6,
                'enable_context_aware_matching': True,
                'max_results': 5
            },
            'term_types': {
                'CONDITION': {
                    'default_vocabulary': 'snomed',
                    'match_threshold': 0.7
                },
                'MEDICATION': {
                    'default_vocabulary': 'rxnorm',
                    'match_threshold': 0.7
                },
                'PROCEDURE': {
                    'default_vocabulary': 'snomed',
                    'match_threshold': 0.7
                },
                'LAB_TEST': {
                    'default_vocabulary': 'loinc',
                    'match_threshold': 0.7
                },
                'OBSERVATION': {
                    'default_vocabulary': 'snomed',
                    'match_threshold': 0.7
                }
            },
            'external_services': {
                'use_external_services': True,
                'use_umls_api': False,
                'umls_api_key': '',
                'use_bioportal_api': False,
                'bioportal_api_key': '',
                'use_rxnav_api': True
            },
            'custom_rules': []
        }
        
        # Load configuration from file if exists
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            bool: True if configuration was loaded successfully
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    
                    # Update configuration with loaded values
                    self._update_nested_dict(self.config, loaded_config)
                    
                    logger.info(f"Configuration loaded from {self.config_path}")
                    return True
            else:
                logger.info(f"Configuration file not found at {self.config_path}, using defaults")
                # Save default configuration
                self.save_config()
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
        
        return False
    
    def save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            bool: True if configuration was saved successfully
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def _update_nested_dict(self, d: Dict, u: Dict) -> None:
        """
        Update a nested dictionary with values from another dictionary.
        
        Args:
            d: Dictionary to update
            u: Dictionary with update values
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
    
    def get_vocabulary_config(self, vocabulary: str) -> Dict[str, Any]:
        """
        Get configuration for a specific vocabulary.
        
        Args:
            vocabulary: Vocabulary name (e.g., 'snomed', 'rxnorm', 'loinc')
            
        Returns:
            Dictionary with vocabulary configuration
        """
        vocabulary = vocabulary.lower()
        default_config = {
            'enabled': True,
            'match_threshold': 0.7,
            'system_url': '',
            'preferred_for': []
        }
        
        vocab_config = self.config.get('vocabularies', {}).get(vocabulary, {})
        
        # Combine with defaults for any missing keys
        for key, value in default_config.items():
            if key not in vocab_config:
                vocab_config[key] = value
                
        return vocab_config
    
    def get_term_type_config(self, term_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific term type.
        
        Args:
            term_type: Term type (e.g., 'CONDITION', 'MEDICATION')
            
        Returns:
            Dictionary with term type configuration
        """
        default_config = {
            'default_vocabulary': 'snomed',
            'match_threshold': 0.7
        }
        
        type_config = self.config.get('term_types', {}).get(term_type, {})
        
        # Combine with defaults for any missing keys
        for key, value in default_config.items():
            if key not in type_config:
                type_config[key] = value
                
        return type_config
    
    def get_matching_config(self) -> Dict[str, Any]:
        """
        Get matching configuration.
        
        Returns:
            Dictionary with matching configuration
        """
        default_config = {
            'default_threshold': 0.7,
            'enable_fuzzy_matching': True,
            'fuzzy_threshold': 0.6,
            'enable_context_aware_matching': True,
            'max_results': 5
        }
        
        match_config = self.config.get('matching', {})
        
        # Combine with defaults for any missing keys
        for key, value in default_config.items():
            if key not in match_config:
                match_config[key] = value
                
        return match_config
    
    def get_external_services_config(self) -> Dict[str, Any]:
        """
        Get external services configuration.
        
        Returns:
            Dictionary with external services configuration
        """
        default_config = {
            'use_external_services': True,
            'use_umls_api': False,
            'umls_api_key': '',
            'use_bioportal_api': False,
            'bioportal_api_key': '',
            'use_rxnav_api': True
        }
        
        services_config = self.config.get('external_services', {})
        
        # Combine with defaults for any missing keys
        for key, value in default_config.items():
            if key not in services_config:
                services_config[key] = value
                
        return services_config
    
    def get_custom_rules(self) -> List[Dict[str, Any]]:
        """
        Get custom mapping rules.
        
        Returns:
            List of custom mapping rules
        """
        return self.config.get('custom_rules', [])
    
    def add_custom_rule(self, rule: Dict[str, Any]) -> bool:
        """
        Add a custom mapping rule.
        
        Args:
            rule: The rule to add
            
        Returns:
            bool: True if the rule was added successfully
        """
        try:
            # Validate rule structure
            required_fields = ['term', 'vocabulary', 'code', 'display']
            for field in required_fields:
                if field not in rule:
                    logger.error(f"Custom rule is missing required field: {field}")
                    return False
            
            # Add the rule
            if 'custom_rules' not in self.config:
                self.config['custom_rules'] = []
                
            # Check for duplicates
            for existing_rule in self.config['custom_rules']:
                if (existing_rule.get('term') == rule['term'] and 
                    existing_rule.get('vocabulary') == rule['vocabulary']):
                    # Update existing rule
                    existing_rule.update(rule)
                    logger.info(f"Updated existing custom rule for '{rule['term']}'")
                    self.save_config()
                    return True
            
            # Add new rule
            self.config['custom_rules'].append(rule)
            logger.info(f"Added custom rule for '{rule['term']}'")
            
            # Save changes
            self.save_config()
            return True
            
        except Exception as e:
            logger.error(f"Error adding custom rule: {e}")
            return False
    
    def remove_custom_rule(self, term: str, vocabulary: str) -> bool:
        """
        Remove a custom mapping rule.
        
        Args:
            term: The term to remove
            vocabulary: The vocabulary to remove it from
            
        Returns:
            bool: True if the rule was removed successfully
        """
        try:
            if 'custom_rules' not in self.config:
                return False
                
            initial_count = len(self.config['custom_rules'])
            
            # Filter out the rule to remove
            self.config['custom_rules'] = [
                rule for rule in self.config['custom_rules']
                if not (rule.get('term') == term and rule.get('vocabulary') == vocabulary)
            ]
            
            # Check if any rules were removed
            if len(self.config['custom_rules']) < initial_count:
                logger.info(f"Removed custom rule for '{term}' in {vocabulary}")
                self.save_config()
                return True
            else:
                logger.info(f"No custom rule found for '{term}' in {vocabulary}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing custom rule: {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary with new configuration values
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            self._update_nested_dict(self.config, updates)
            logger.info("Configuration updated")
            
            # Save changes
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False


# Standalone functions from clinical-protocol-extractor

def setup_terminology_databases(data_dir: str, force_update: bool = False) -> bool:
    """
    Set up and populate the terminology databases.
    
    Args:
        data_dir: Path to the data directory
        force_update: Whether to force an update even if databases exist
        
    Returns:
        bool: True if setup was successful
    """
    if TerminologyDatabaseUpdater is None:
        logger.error("TerminologyDatabaseUpdater not available, cannot set up databases")
        return False
        
    logger.info(f"Setting up terminology databases in {data_dir}")
    
    # Check if databases already exist
    snomed_db = os.path.join(data_dir, "snomed_core.sqlite")
    loinc_db = os.path.join(data_dir, "loinc_core.sqlite")
    rxnorm_db = os.path.join(data_dir, "rxnorm_core.sqlite")
    
    # Check if all databases exist and have data
    databases_exist = all([
        os.path.exists(snomed_db),
        os.path.exists(loinc_db),
        os.path.exists(rxnorm_db)
    ])
    
    if databases_exist and not force_update:
        # Try to open each database and check if it has data
        import sqlite3
        try:
            non_empty = True
            for db_path in [snomed_db, loinc_db, rxnorm_db]:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get the table name based on the database
                table_name = os.path.basename(db_path).replace("_core.sqlite", "_concepts")
                
                # Check if the table has any rows
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                conn.close()
                
                if count == 0:
                    non_empty = False
                    break
                    
            if non_empty:
                logger.info("Terminology databases already exist and contain data, skipping update")
                return True
        except Exception as e:
            logger.warning(f"Error checking databases, will update: {e}")
    
    # Create and run the database updater
    updater = TerminologyDatabaseUpdater(data_dir=data_dir)
    return updater.update_all()
    
def check_and_configure_external_services(config_path: str = None) -> dict:
    """
    Check and configure external terminology services.
    
    Args:
        config_path: Path to configuration file with API keys
        
    Returns:
        dict: Configuration for external services
    """
    logger.info("Checking external terminology services")
    
    # Default configuration
    config = {
        "use_external_services": True,
        "use_fuzzy_matching": True,
        "use_rxnav_api": True,
        "use_redis_cache": False,
    }
    
    # Load configuration from file if provided
    if config_path:
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
                logger.info(f"Loaded external service configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    # Check if we have API keys for each service
    if "umls_api_key" not in config or not config["umls_api_key"]:
        logger.warning("No UMLS API key found. UMLS services will be unavailable.")
        config["use_umls_api"] = False
    else:
        config["use_umls_api"] = True
        logger.info("UMLS API key found.")
    
    if "bioportal_api_key" not in config or not config["bioportal_api_key"]:
        logger.warning("No BioPortal API key found. BioPortal services will be unavailable.")
        config["use_bioportal_api"] = False
    else:
        config["use_bioportal_api"] = True
        logger.info("BioPortal API key found.")
    
    # Test RxNav API since it doesn't require authentication
    import requests
    try:
        response = requests.get("https://rxnav.nlm.nih.gov/REST/version")
        if response.status_code == 200:
            logger.info("RxNav API is available.")
            config["use_rxnav_api"] = True
        else:
            logger.warning("RxNav API is not responding. RxNav services will be unavailable.")
            config["use_rxnav_api"] = False
    except Exception:
        logger.warning("Could not connect to RxNav API. RxNav services will be unavailable.")
        config["use_rxnav_api"] = False
    
    return config

def test_terminology_mapper(data_dir: str, config: dict) -> bool:
    """
    Test the terminology mapper with the current configuration.
    
    Args:
        data_dir: Path to the data directory
        config: Configuration dictionary
        
    Returns:
        bool: True if tests pass
    """
    try:
        from app.standards.terminology.mapper import TerminologyMapper
    except ImportError:
        try:
            from standards.terminology.mapper import TerminologyMapper
        except ImportError:
            logger.error("TerminologyMapper not found, cannot run tests")
            return False
            
    logger.info("Testing terminology mapper")
    
    # Set the data directory in the config
    config["data_dir"] = data_dir
    
    # Create a mapper instance
    mapper = TerminologyMapper(config)
    
    # Test initialization
    if not mapper.initialize():
        logger.error("Terminology mapper initialization failed")
        return False
        
    # Test some basic mappings
    logger.info("Testing SNOMED mappings:")
    test_terms = ["hypertension", "diabetes", "asthma", "pneumonia"]
    for term in test_terms:
        result = mapper.map_to_snomed(term)
        found = result.get("found", False)
        code = result.get("code", "none")
        logger.info(f"  - {term}: {'✓' if found else '✗'} (code: {code})")
        
    logger.info("Testing LOINC mappings:")
    test_terms = ["hemoglobin a1c", "blood pressure", "glucose"]
    for term in test_terms:
        result = mapper.map_to_loinc(term)
        found = result.get("found", False)
        code = result.get("code", "none")
        logger.info(f"  - {term}: {'✓' if found else '✗'} (code: {code})")
        
    logger.info("Testing RxNorm mappings:")
    test_terms = ["metformin", "lisinopril", "aspirin"]
    for term in test_terms:
        result = mapper.map_to_rxnorm(term)
        found = result.get("found", False)
        code = result.get("code", "none")
        logger.info(f"  - {term}: {'✓' if found else '✗'} (code: {code})")
        
    # Test fuzzy matching
    logger.info("Testing fuzzy matching:")
    fuzzy_tests = [
        ("htn", "snomed"),  # Abbreviation
        ("hypertention", "snomed"),  # Misspelling
        ("a1c", "loinc"),  # Abbreviation
        ("metphormin", "rxnorm")  # Misspelling
    ]
    
    for term, system in fuzzy_tests:
        result = mapper.map_term(term, system)
        found = result.get("found", False)
        code = result.get("code", "none")
        display = result.get("display", "")
        logger.info(f"  - {term} → {display}: {'✓' if found else '✗'} (code: {code})")
        
    # Get statistics
    try:
        stats = mapper.get_statistics()
        logger.info(f"Database statistics: {json.dumps(stats, indent=2)}")
    except AttributeError:
        logger.warning("get_statistics method not available")
    
    return True

def main():
    """Main entry point for the configuration script."""
    parser = argparse.ArgumentParser(description='Configure terminology mapping system')
    parser.add_argument('--config', dest='config_path', help='Path to configuration file')
    parser.add_argument('--data-dir', dest='data_dir', help='Path to data directory')
    parser.add_argument('--force-update', action='store_true', help='Force database update')
    parser.add_argument('--skip-db-update', action='store_true', help='Skip database update')
    parser.add_argument('--test-mapper', action='store_true', help='Test the terminology mapper')
    parser.add_argument('--save-config', action='store_true', help='Save the configuration to file')
    args = parser.parse_args()
    
    # Set up data directory
    data_dir = args.data_dir
    if not data_dir:
        # Default to the standard data directory
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        except NameError:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
        data_dir = os.path.join(base_dir, 'data', 'terminology')
    
    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Update databases if requested
    if not args.skip_db_update:
        if not setup_terminology_databases(data_dir, args.force_update):
            logger.error("Failed to set up terminology databases")
            return 1
    
    # Configure external services
    external_config = check_and_configure_external_services(args.config_path)
    
    # Create a configuration object
    config_path = args.config_path
    if not config_path:
        config_path = os.path.join(data_dir, "mapping_config.json")
    
    config_manager = MappingConfiguration(config_path)
    
    # Update with external services configuration
    config_manager.update_config({
        'external_services': external_config
    })
    
    # Save configuration if requested
    if args.save_config:
        if not config_manager.save_config():
            logger.error("Failed to save configuration")
            return 1
    
    # Test the mapper if requested
    if args.test_mapper:
        combined_config = config_manager.config
        combined_config['data_dir'] = data_dir
        if not test_terminology_mapper(data_dir, combined_config):
            logger.error("Terminology mapper tests failed")
            return 1
    
    logger.info("Terminology mapping system configured successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())