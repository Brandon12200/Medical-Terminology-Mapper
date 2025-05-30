"""
Compatibility layer for the TerminologyMapper.

This module provides backwards compatibility between the original
terminology_mapper.py used by term_extractor.py and our new refactored 
implementation based on the clinical-protocol-extractor.
"""

import logging
import time
from typing import List, Dict, Any, Optional

# Import both implementations
try:
    # Import the original embedded_db manager which the term_extractor expects
    from app.standards.terminology.embedded_db import EmbeddedDatabaseManager
except ImportError:
    try:
        from standards.terminology.embedded_db import EmbeddedDatabaseManager
    except ImportError:
        EmbeddedDatabaseManager = None
        
# Import the new mapper implementation
try:
    from app.standards.terminology.mapper import TerminologyMapper as NewTerminologyMapper
except ImportError:
    try:
        from standards.terminology.mapper import TerminologyMapper as NewTerminologyMapper
    except ImportError:
        NewTerminologyMapper = None

# Import the new configuration manager
try:
    from app.standards.terminology.configure_mappings import MappingConfiguration
except ImportError:
    try:
        from standards.terminology.configure_mappings import MappingConfiguration
    except ImportError:
        MappingConfiguration = None

# Configure logging
logger = logging.getLogger(__name__)

class TerminologyMapper:
    """
    Compatibility wrapper for the terminology mapper.
    
    This class provides backwards compatibility with the original
    TerminologyMapper API while using the new refactored implementation.
    """
    
    def __init__(self, db_manager=None):
        """
        Initialize the terminology mapper.
        
        Args:
            db_manager: Optional EmbeddedDatabaseManager instance. If not provided,
                       a new instance will be created and initialized.
        """
        self.db_manager = db_manager
        self.is_connected = False
        
        # Set up the configuration
        self.config = self._setup_config()
        
        # Create new mapper instance
        try:
            self.new_mapper = NewTerminologyMapper(self.config)
            self.is_connected = self.new_mapper.initialize()
            logger.info(f"New terminology mapper initialized: connected={self.is_connected}")
        except Exception as e:
            logger.error(f"Error initializing new terminology mapper: {e}")
            self.new_mapper = None
            self.is_connected = False
    
    def _setup_config(self) -> Dict[str, Any]:
        """
        Set up configuration for the new mapper.
        
        Returns:
            Dict: Configuration dictionary
        """
        config = {
            'matching': {
                'default_threshold': 0.7,
                'enable_fuzzy_matching': True,
                'fuzzy_threshold': 0.6,
                'enable_context_aware_matching': True,
                'max_results': 5
            }
        }
        
        # Add database path if db_manager is provided
        if self.db_manager and hasattr(self.db_manager, 'data_dir'):
            config['data_dir'] = self.db_manager.data_dir
        
        # Try to load configuration from file
        try:
            if MappingConfiguration:
                config_manager = MappingConfiguration()
                # Merge configurations, letting our defaults take precedence
                merged_config = config_manager.config.copy()
                merged_config.update(config)
                config = merged_config
        except Exception as e:
            logger.warning(f"Error loading configuration file: {e}")
        
        return config
    
    def connect(self) -> bool:
        """
        Connect to the terminology databases.
        
        Returns:
            bool: True if connection was successful
        """
        try:
            # Try to initialize the new mapper if it exists
            if self.new_mapper:
                self.is_connected = self.new_mapper.initialize()
                if self.is_connected:
                    logger.info("Successfully connected to terminology databases")
                else:
                    logger.warning("Failed to connect to terminology databases")
                return self.is_connected
            # Otherwise fall back to the old connection method
            elif self.db_manager:
                connected = self.db_manager.connect()
                self.is_connected = connected
                if connected:
                    logger.info("Successfully connected to terminology databases (legacy)")
                else:
                    logger.warning("Failed to connect to terminology databases (legacy)")
                return connected
            else:
                logger.error("No database manager or mapper available for connection")
                return False
        except Exception as e:
            logger.error(f"Error connecting to terminology databases: {e}")
            self.is_connected = False
            return False
    
    def map_terms(self, terms: List[Dict[str, Any]], threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Map a list of extracted terms to standardized terminology codes.
        
        Args:
            terms: List of extracted terms to map
            threshold: Minimum confidence threshold for mappings
            
        Returns:
            List of terms with added terminology mappings
        """
        start_time = time.time()
        
        # Ensure connection
        if not self.is_connected:
            self.connect()
            if not self.is_connected:
                logger.warning("Unable to map terms: database connection failed")
                return terms
        
        # Use new mapper if available
        if self.new_mapper:
            try:
                # Track mapping statistics
                mapped_count = 0
                total_count = len(terms)
                
                # Process each term
                for term in terms:
                    # Skip if confidence below threshold
                    if term.get('confidence', 0) < threshold:
                        continue
                        
                    # Get term type to determine which vocabulary to use
                    term_type = term.get('type', '')
                    term_text = term.get('text', '')
                    
                    if not term_text or not term_type:
                        continue
                    
                    # Map term based on its type
                    mapping = None
                    if term_type == 'CONDITION' or term_type == 'OBSERVATION':
                        mapping = self.new_mapper.map_to_snomed(term_text)
                    elif term_type == 'MEDICATION':
                        mapping = self.new_mapper.map_to_rxnorm(term_text)
                    elif term_type == 'LAB_TEST':
                        mapping = self.new_mapper.map_to_loinc(term_text)
                    elif term_type == 'PROCEDURE':
                        # Try SNOMED CT first, fallback to LOINC for lab procedures
                        mapping = self.new_mapper.map_to_snomed(term_text)
                        if not mapping or not mapping.get('found', False):
                            mapping = self.new_mapper.map_to_loinc(term_text)
                    
                    # If mapping found, update the term
                    if mapping and mapping.get('found', False):
                        # Update terminology information
                        term['terminology'] = {
                            'mapped': True,
                            'vocabulary': mapping.get('system', '').split('/')[-1].upper(),
                            'code': mapping.get('code'),
                            'description': mapping.get('display'),
                            'confidence': mapping.get('confidence', 0.9)
                        }
                        mapped_count += 1
                    else:
                        # Set mapped to False in terminology info
                        if 'terminology' not in term:
                            term['terminology'] = {
                                'mapped': False,
                                'vocabulary': self._get_vocabulary_for_type(term_type),
                                'code': None,
                                'description': None
                            }
                        else:
                            term['terminology']['mapped'] = False
                
                # Log mapping statistics
                duration = time.time() - start_time
                mapping_percentage = (mapped_count / total_count * 100) if total_count > 0 else 0
                logger.info(f"Mapped {mapped_count}/{total_count} terms ({mapping_percentage:.1f}%) in {duration:.3f}s")
                
                return terms
                
            except Exception as e:
                logger.error(f"Error using new mapper: {e}, falling back to legacy mapping")
                # Fall back to legacy mapping if available
        
        # Fall back to legacy implementation if new mapper failed or is not available
        if self.db_manager:
            # Track mapping statistics
            mapped_count = 0
            total_count = len(terms)
            
            # Process each term
            for term in terms:
                # Skip if confidence below threshold
                if term.get('confidence', 0) < threshold:
                    continue
                    
                # Get term type to determine which vocabulary to use
                term_type = term.get('type', '')
                term_text = term.get('text', '')
                
                if not term_text or not term_type:
                    continue
                
                # Map term based on its type
                mapping = None
                if term_type == 'CONDITION' or term_type == 'OBSERVATION':
                    mapping = self.db_manager.lookup_snomed(term_text)
                elif term_type == 'MEDICATION':
                    mapping = self.db_manager.lookup_rxnorm(term_text)
                elif term_type == 'LAB_TEST':
                    mapping = self.db_manager.lookup_loinc(term_text)
                elif term_type == 'PROCEDURE':
                    # Try SNOMED CT first, fallback to LOINC for lab procedures
                    mapping = self.db_manager.lookup_snomed(term_text)
                    if not mapping:
                        mapping = self.db_manager.lookup_loinc(term_text)
                
                # If mapping found, update the term
                if mapping:
                    # Update terminology information
                    term['terminology'] = {
                        'mapped': True,
                        'vocabulary': mapping.get('system', '').split('/')[-1].upper(),
                        'code': mapping.get('code'),
                        'description': mapping.get('display'),
                        'confidence': mapping.get('confidence', 0.9)
                    }
                    mapped_count += 1
                else:
                    # Set mapped to False in terminology info
                    if 'terminology' not in term:
                        term['terminology'] = {
                            'mapped': False,
                            'vocabulary': self._get_vocabulary_for_type(term_type),
                            'code': None,
                            'description': None
                        }
                    else:
                        term['terminology']['mapped'] = False
            
            # Log mapping statistics
            duration = time.time() - start_time
            mapping_percentage = (mapped_count / total_count * 100) if total_count > 0 else 0
            logger.info(f"Mapped {mapped_count}/{total_count} terms ({mapping_percentage:.1f}%) in {duration:.3f}s (legacy)")
            
            return terms
        else:
            logger.warning("No mapping implementation available, returning terms unmapped")
            return terms
    
    def _get_vocabulary_for_type(self, term_type: str) -> str:
        """
        Determine the appropriate terminology vocabulary for a given term type.
        
        Args:
            term_type (str): The type of term
            
        Returns:
            str: Vocabulary name
        """
        vocab_mapping = {
            'CONDITION': 'SNOMED CT',
            'MEDICATION': 'RXNORM',
            'PROCEDURE': 'SNOMED CT',
            'LAB_TEST': 'LOINC',
            'OBSERVATION': 'SNOMED CT'
        }
        return vocab_mapping.get(term_type, 'SNOMED CT')
    
    def add_custom_mapping(self, system: str, term: str, code: str, display: str) -> bool:
        """
        Add a custom mapping for a term.
        
        Args:
            system: The vocabulary system (snomed, loinc, rxnorm)
            term: The term to map
            code: The terminology code
            display: The human-readable display name
            
        Returns:
            bool: True if the mapping was added successfully
        """
        if not self.is_connected:
            self.connect()
            if not self.is_connected:
                logger.warning("Unable to add custom mapping: database connection failed")
                return False
        
        # Use the new mapper if available
        if self.new_mapper:
            try:
                return self.new_mapper.add_custom_mapping(system, term, code, display)
            except Exception as e:
                logger.error(f"Error adding custom mapping with new mapper: {e}")
                # Fall back to legacy implementation if new mapper failed
        
        # Fall back to legacy implementation
        if self.db_manager:
            # Normalize vocabulary name
            norm_vocab = system.lower()
            if norm_vocab == 'snomed ct' or norm_vocab == 'snomedct':
                norm_vocab = 'snomed'
            
            # Create the mapping object
            mapping = {
                "code": code,
                "display": display,
                "system": self._get_system_url(norm_vocab),
                "found": True,
                "custom": True
            }
            
            # Add the mapping
            return self.db_manager.add_mapping(norm_vocab, term, mapping)
        
        return False
    
    def _get_system_url(self, vocabulary: str) -> str:
        """
        Get the system URL for a vocabulary.
        
        Args:
            vocabulary: The vocabulary name (snomed, loinc, rxnorm)
            
        Returns:
            str: The system URL
        """
        urls = {
            'snomed': 'http://snomed.info/sct',
            'loinc': 'http://loinc.org',
            'rxnorm': 'http://www.nlm.nih.gov/research/umls/rxnorm'
        }
        return urls.get(vocabulary.lower(), '')
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the terminology databases.
        
        Returns:
            dict: Statistics about the databases
        """
        if not self.is_connected:
            self.connect()
            
        stats = {
            'is_connected': self.is_connected,
            'databases': {},
            'using_new_mapper': self.new_mapper is not None
        }
        
        # Get statistics from the new mapper if available
        if self.new_mapper and hasattr(self.new_mapper, 'get_statistics'):
            try:
                mapper_stats = self.new_mapper.get_statistics()
                stats['databases'] = mapper_stats
                return stats
            except Exception as e:
                logger.error(f"Error getting statistics from new mapper: {e}")
        
        # Fall back to the old database manager
        if self.is_connected and self.db_manager:
            try:
                db_stats = self.db_manager.get_statistics()
                stats['databases'] = db_stats
            except Exception as e:
                logger.error(f"Error getting statistics from database manager: {e}")
        
        return stats
    
    def close(self):
        """Close database connections."""
        # Close new mapper if available
        if self.new_mapper and hasattr(self.new_mapper, 'close'):
            try:
                self.new_mapper.close()
            except Exception as e:
                logger.error(f"Error closing new mapper: {e}")
        
        # Close legacy database manager if available
        if self.is_connected and self.db_manager and hasattr(self.db_manager, 'close'):
            try:
                self.db_manager.close()
            except Exception as e:
                logger.error(f"Error closing database manager: {e}")
        
        self.is_connected = False