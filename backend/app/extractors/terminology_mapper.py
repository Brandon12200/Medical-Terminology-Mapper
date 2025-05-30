"""
Terminology mapper for Medical Terminology Mapper.
This module maps extracted medical terms to standard terminology codes using
the embedded databases. It provides integration between term extraction and 
standardized terminologies.
"""

import logging
from typing import List, Dict, Any, Optional
import time

from app.standards.terminology.embedded_db import EmbeddedDatabaseManager

# Configure logging
logger = logging.getLogger(__name__)

class TerminologyMapper:
    """
    Maps extracted terms to standardized terminology codes.
    
    This class provides mapping capabilities between extracted medical terms
    and standard terminology systems (SNOMED CT, LOINC, RxNorm).
    """
    
    def __init__(self, db_manager=None):
        """
        Initialize the terminology mapper.
        
        Args:
            db_manager: Optional EmbeddedDatabaseManager instance. If not provided,
                        a new instance will be created and initialized.
        """
        self.db_manager = db_manager or EmbeddedDatabaseManager()
        self.is_connected = False
        
        # Connect to databases if not already connected
        if not self.is_connected:
            self.connect()
    
    def connect(self) -> bool:
        """
        Connect to the terminology databases.
        
        Returns:
            bool: True if connection was successful
        """
        try:
            # Connect to the databases
            connected = self.db_manager.connect()
            self.is_connected = connected
            if connected:
                logger.info("Successfully connected to terminology databases")
            else:
                logger.warning("Failed to connect to terminology databases")
            return connected
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
        
        # Ensure connection to database
        if not self.is_connected:
            self.connect()
            if not self.is_connected:
                logger.warning("Unable to map terms: database connection failed")
                return terms
        
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
        logger.info(f"Mapped {mapped_count}/{total_count} terms ({mapping_percentage:.1f}%) in {duration:.3f}s")
        
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
    
    def add_custom_mapping(self, term: str, vocabulary: str, code: str, display: str) -> bool:
        """
        Add a custom mapping for a term.
        
        Args:
            term: The term to map
            vocabulary: The vocabulary system (SNOMED, LOINC, RXNORM)
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
        
        # Normalize vocabulary name
        norm_vocab = vocabulary.lower()
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
            'databases': {}
        }
        
        # Get statistics from the database manager if connected
        if self.is_connected:
            db_stats = self.db_manager.get_statistics()
            stats['databases'] = db_stats
        
        return stats
    
    def close(self):
        """Close database connections."""
        if self.is_connected and self.db_manager:
            self.db_manager.close()
            self.is_connected = False