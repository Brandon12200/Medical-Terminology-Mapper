"""Maps medical terms to standard terminologies."""

import os
import json
import logging
import importlib.util
import glob
from typing import Dict, List, Optional, Any, Union

from app.standards.terminology.embedded_db import EmbeddedDatabaseManager

logger = logging.getLogger(__name__)

class TerminologyMapper:
    """Terminology mapper for medical terms."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize mapper with config."""
        self.db_manager = EmbeddedDatabaseManager(
            data_dir=config.get("data_dir") if config else None
        )
        self.config = config or {}
        self.fuzzy_matcher = None
        self.external_service = None
        self.synonyms = {}
        self.clinical_context_enhancers = {}
        
        self._setup_fuzzy_matching()
        self._setup_external_services()
        self._load_all_synonyms()
        self._load_abbreviations()
        self._setup_clinical_context_enhancers()
        self.initialize()
    
    def _setup_fuzzy_matching(self):
        """Setup fuzzy matching."""
        if self.config.get("use_fuzzy_matching", True):
            try:
                from app.standards.terminology.fuzzy_matcher import FuzzyMatcher
                self.fuzzy_matcher = FuzzyMatcher(self.db_manager, self.config)
                logger.info("Fuzzy matching initialized")
            except ImportError as e:
                logger.warning(f"Fuzzy matching dependencies not available: {e}")
    
    def _setup_external_services(self):
        """Setup external services."""
        if self.config.get("use_external_services", False):
            try:
                from app.standards.terminology.api_services import TerminologyAPIService
                self.external_service = TerminologyAPIService(
                    cache_dir=self.config.get("api_cache_dir", "app/cache/api_cache")
                )
                logger.info("External API services initialized")
            except ImportError as e:
                logger.warning(f"External terminology service dependencies not available: {e}")
    
    def _load_all_synonyms(self):
        """Load synonym dictionaries."""
        try:
            if self.config.get("data_dir"):
                data_dir = self.config.get("data_dir")
            else:
                data_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(
                        os.path.abspath(__file__)))),
                    'data', 'terminology'
                )
            
            synonyms_dir = os.path.join(data_dir, 'synonyms')
            
            if os.path.exists(synonyms_dir):
                synonym_files = glob.glob(os.path.join(synonyms_dir, "*.json"))
                
                total_sets = 0
                for syn_file in synonym_files:
                    try:
                        with open(syn_file, 'r') as f:
                            file_synonyms = json.load(f)
                            self.synonyms.update(file_synonyms)
                            total_sets += len(file_synonyms)
                    except Exception as e:
                        logger.warning(f"Error loading synonyms from {os.path.basename(syn_file)}: {e}")
                
                logger.info(f"Loaded {total_sets} synonym sets from {len(synonym_files)} files")
            else:
                logger.warning(f"Synonyms directory not found: {synonyms_dir}")
        except Exception as e:
            logger.error(f"Error loading synonyms: {e}")
    
    def _load_abbreviations(self):
        """Load medical abbreviations from JSON file."""
        try:
            # Try multiple locations for the abbreviations file
            script_dir = os.path.dirname(__file__)
            possible_paths = [
                os.path.join(script_dir, "../../../data/terminology/medical_abbreviations.json"),
                os.path.join(script_dir, "../../data/terminology/medical_abbreviations.json"),
                os.path.join(self.config.get("data_dir", ""), "medical_abbreviations.json") if self.config.get("data_dir") else None,
                "/Users/brandonkenney/Projects/medical-terminology-mapper/backend/data/terminology/medical_abbreviations.json"
            ]
            
            for path in possible_paths:
                if path and os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        self.abbreviations = data.get("abbreviations", {})
                        logger.info(f"Loaded {len(self.abbreviations)} medical abbreviations")
                        return
                        
            logger.warning("Medical abbreviations file not found")
            self.abbreviations = {}
            
        except Exception as e:
            logger.error(f"Error loading abbreviations: {e}")
            self.abbreviations = {}
    
    def _setup_clinical_context_enhancers(self):
        """Setup context enhancers."""
        self.clinical_context_enhancers = {
            "medical": self._enhance_medical_context,
            "condition": self._enhance_condition_context,
            "procedure": self._enhance_procedure_context,
            "medication": self._enhance_medication_context,
            "lab_test": self._enhance_lab_test_context,
            "measurement": self._enhance_measurement_context
        }
    
    def _enhance_medical_context(self, term: str, mapping_result: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Enhance mapping for medical context."""
        medical_keywords = [
            "patient", "diagnosis", "medical", "health", "clinical", "disease",
            "condition", "history", "assessment", "treatment", "healthcare",
            "physician", "doctor", "hospital", "clinic", "symptoms"
        ]
        
        medical_context = any(kw in context.lower() for kw in medical_keywords)
        
        if medical_context:
            if "score" in mapping_result:
                mapping_result["score"] = min(100, mapping_result["score"] + 10)
            mapping_result["context_enhanced"] = True
            mapping_result["medical_context"] = True
        
        return mapping_result
    
    def _enhance_condition_context(self, term: str, mapping_result: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Enhance mapping for condition context."""
        condition_keywords = [
            "diagnosis", "condition", "disease", "disorder", "syndrome", 
            "diagnosed with", "suffers from", "presents with", "symptoms of",
            "confirmed", "suspected", "chronic", "acute", "patient has",
            "history of", "assessment", "impression"
        ]
        
        condition_context = any(kw in context.lower() for kw in condition_keywords)
        
        if condition_context:
            if "score" in mapping_result:
                mapping_result["score"] = min(100, mapping_result["score"] + 15)
            mapping_result["context_enhanced"] = True
            mapping_result["condition_context"] = True
        
        return mapping_result
    
    def _enhance_procedure_context(self, term: str, mapping_result: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Enhance mapping for procedure context."""
        procedure_keywords = [
            "procedure", "surgery", "operation", "intervention", "test", "exam",
            "scan", "image", "performed", "underwent", "scheduled for",
            "surgical", "diagnostic", "examination", "imaging", "treatment"
        ]
        
        procedure_context = any(kw in context.lower() for kw in procedure_keywords)
        
        if procedure_context:
            if "score" in mapping_result:
                mapping_result["score"] = min(100, mapping_result["score"] + 12)
            mapping_result["context_enhanced"] = True
            mapping_result["procedure_context"] = True
        
        return mapping_result
    
    def _enhance_medication_context(self, term: str, mapping_result: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Enhance mapping for medication context."""
        medication_keywords = [
            "medication", "drug", "dose", "dosage", "tablet", "capsule", "pill",
            "injection", "infusion", "prescription", "mg", "mcg", "mL", "oral",
            "intravenous", "iv", "im", "subcutaneous", "sc", "daily", "bid", "tid",
            "taken", "prescribed", "therapy", "treatment", "administration"
        ]
        
        medication_context = any(kw in context.lower() for kw in medication_keywords)
        
        if medication_context:
            if "score" in mapping_result:
                mapping_result["score"] = min(100, mapping_result["score"] + 15)
            mapping_result["context_enhanced"] = True
            mapping_result["medication_context"] = True
        
        return mapping_result
    
    def _enhance_lab_test_context(self, term: str, mapping_result: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Enhance mapping for lab test context."""
        lab_keywords = [
            "laboratory", "lab", "blood test", "urine test", "serum", "plasma",
            "sample", "specimen", "test", "assay", "analysis", "level", "concentration",
            "chemistry", "hematology", "microbiology", "value", "elevated", "decreased",
            "normal range", "reference range", "results", "panel", "profile"
        ]
        
        # Check if the context contains any lab test-specific keywords
        lab_context = any(kw in context.lower() for kw in lab_keywords)
        
        if lab_context:
            # Increase confidence score if in a lab test context
            if "score" in mapping_result:
                mapping_result["score"] = min(100, mapping_result["score"] + 15)
            mapping_result["context_enhanced"] = True
            mapping_result["lab_test_context"] = True
        
        return mapping_result
    
    def _enhance_measurement_context(self, term: str, mapping_result: Dict[str, Any], context: str) -> Dict[str, Any]:
        """
        Enhance mapping results for measurement terms based on context.
        
        Args:
            term: The term being mapped
            mapping_result: Current mapping result
            context: Context information
            
        Returns:
            Enhanced mapping result
        """
        # Check for measurement-specific keywords in the context
        measurement_keywords = [
            "measurement", "measure", "assessment", "evaluate", "monitoring",
            "value", "level", "test", "testing", "parameter", "score", "index",
            "rate", "ratio", "concentration", "count", "percentage", "mmHg",
            "kg", "cm", "mm", "mmol/L", "mg/dL", "g/L", "frequency", "duration"
        ]
        
        # Check if the context contains any measurement-specific keywords
        measurement_context = any(kw in context.lower() for kw in measurement_keywords)
        
        if measurement_context:
            # Increase confidence score if in a measurement context
            if "score" in mapping_result:
                mapping_result["score"] = min(100, mapping_result["score"] + 10)
            mapping_result["context_enhanced"] = True
            mapping_result["measurement_context"] = True
        
        return mapping_result
    
    def initialize(self) -> bool:
        """
        Initialize the mapping database and services.
        
        Returns:
            bool: True if initialization was successful
        """
        try:
            # Connect to embedded databases
            db_success = self.db_manager.connect()
            
            # Initialize fuzzy matcher if available
            fuzzy_success = True
            if self.fuzzy_matcher:
                fuzzy_success = self.fuzzy_matcher.initialize()
            
            # Initialize external services if available
            external_success = True
            # External service doesn't need initialization - it's ready to use
            
            # Share synonyms with the fuzzy matcher
            if self.fuzzy_matcher:
                self.fuzzy_matcher.synonyms = self.synonyms
            
            # Log overall initialization status
            if db_success:
                logger.info("Terminology mapper initialized successfully")
                
                # Log component status
                if self.fuzzy_matcher and not fuzzy_success:
                    logger.warning("Fuzzy matching initialization incomplete")
                if self.external_service and not external_success:
                    logger.warning("External services initialization incomplete")
            else:
                logger.warning("Terminology mapper initialization incomplete")
                
            return db_success
        except Exception as e:
            logger.error(f"Error initializing terminology mapper: {e}")
            return False
    
    def map_to_snomed(self, term: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Map a medical term to SNOMED CT code.
        
        Args:
            term: The medical term to map
            context: Optional context information to improve mapping accuracy
            
        Returns:
            Dictionary with mapping results including code, display name,
            terminology system, and confidence score
        """
        if not term:
            return {
                "code": None, 
                "display": "", 
                "system": "http://snomed.info/sct", 
                "found": False
            }
            
        # Clean and normalize the term
        clean_term = self._normalize_term(term)
        
        # Check if term is an abbreviation and try expansions
        if clean_term.lower() in self.abbreviations:
            expansions = self.abbreviations[clean_term.lower()]
            logger.debug(f"Found abbreviation '{clean_term}' with expansions: {expansions}")
            
            for expansion in expansions:
                # Try exact match for each expansion
                result = self.db_manager.lookup_snomed(expansion)
                if result:
                    logger.debug(f"Found SNOMED match for abbreviation expansion '{expansion}': {result['code']}")
                    result['confidence'] = 0.95  # Slightly lower confidence for abbreviation
                    result['match_type'] = 'abbreviation'
                    result['original_term'] = term
                    result['expanded_term'] = expansion
                    result['found'] = True
                    if context:
                        result = self._apply_context_enhancement(expansion, result, context, "condition")
                    return result
        
        # Check for directly mappable synonyms from loaded dictionary
        synonym_result = self._check_synonyms(clean_term, "snomed")
        if synonym_result:
            logger.debug(f"Found synonym match for '{term}': {synonym_result['code']}")
            # Apply context enhancement for synonyms
            if context:
                synonym_result = self._apply_context_enhancement(clean_term, synonym_result, context, "condition")
            return synonym_result
            
        # 1. Try exact match in embedded database
        result = self.db_manager.lookup_snomed(clean_term)
        if result:
            logger.debug(f"Found exact SNOMED match for '{term}': {result['code']}")
            # Add confidence score for exact match
            result['confidence'] = 1.0
            result['match_type'] = 'exact'
            # Apply context enhancement
            if context:
                result = self._apply_context_enhancement(clean_term, result, context, "condition")
            return result
            
        # 2. Try fuzzy matching if available
        if self.fuzzy_matcher and self.config.get("use_fuzzy_matching", True):
            fuzzy_result = self.fuzzy_matcher.find_fuzzy_match(clean_term, "snomed", context)
            if fuzzy_result:
                logger.debug(f"Found fuzzy SNOMED match for '{term}': {fuzzy_result['code']} (match type: {fuzzy_result.get('match_type', 'unknown')}, score: {fuzzy_result.get('score', 0)})")
                # Apply context enhancement
                if context:
                    fuzzy_result = self._apply_context_enhancement(clean_term, fuzzy_result, context, "condition")
                return fuzzy_result
                
        # 3. Try external API if available
        if self.external_service and self.config.get("use_external_services", False):
            try:
                api_results = self.external_service.search_snomed_browser(clean_term)
                if api_results:
                    # Take the first result
                    result = api_results[0]
                    result['match_type'] = 'api'
                    result['confidence'] = 0.8
                    logger.debug(f"Found SNOMED API match for '{term}': {result['code']}")
                    # Apply context enhancement
                    if context:
                        result = self._apply_context_enhancement(clean_term, result, context)
                    return result
            except Exception as e:
                logger.warning(f"External SNOMED API error: {e}")
        
        # 4. Return not found with the original term
        logger.debug(f"No SNOMED mapping found for '{term}'")
        return {
            "code": None, 
            "display": term, 
            "system": "http://snomed.info/sct", 
            "found": False,
            "attempted_methods": ["exact", 
                                 "fuzzy" if self.fuzzy_matcher else "",
                                 "api" if self.external_service else ""]
        }
    
    def map_to_loinc(self, term: str, context: Optional[str] = None, include_details: bool = False) -> Dict[str, Any]:
        """
        Map a medical term to LOINC code with enhanced laboratory test matching.
        
        Args:
            term: The medical term to map
            context: Optional context information to improve mapping accuracy
            include_details: Whether to include detailed LOINC information
            
        Returns:
            Dictionary with mapping results including code, display name,
            terminology system, and confidence score
        """
        if not term:
            return {
                "code": None, 
                "display": "", 
                "system": "http://loinc.org", 
                "found": False
            }
            
        # Clean and normalize the term
        clean_term = self._normalize_term(term)
        
        # Special normalization for laboratory terms
        lab_term = self.db_manager._normalize_lab_term(clean_term) if self._is_lab_term(clean_term) else clean_term
        
        # Check for directly mappable synonyms from loaded dictionary
        synonym_result = self._check_synonyms(clean_term, "loinc")
        if synonym_result:
            logger.debug(f"Found synonym match for '{term}': {synonym_result['code']}")
            # Apply context enhancement for synonyms
            if context:
                context_type = "lab_test" if self._is_lab_term(clean_term) else "measurement"
                synonym_result = self._apply_context_enhancement(clean_term, synonym_result, context, context_type)
            
            # Add detailed information if requested
            if include_details and "code" in synonym_result:
                synonym_result = self.db_manager.get_loinc_concept(synonym_result["code"], include_details=True)
                
            return synonym_result
            
        # 1. Try enhanced lookup with specialized matching and details
        result = self.db_manager.lookup_loinc(lab_term, include_details=include_details)
        if result:
            logger.debug(f"Found LOINC match for '{term}': {result['code']} (match type: {result.get('match_type', 'exact')})")
            # Add confidence score for exact match
            result['confidence'] = 1.0
            result['match_type'] = 'exact'
            # Apply context enhancement
            if context:
                context_type = "lab_test" if self._is_lab_term(clean_term) else "measurement"
                result = self._apply_context_enhancement(clean_term, result, context, context_type)
            return result
            
        # 2. Try fuzzy matching if available and first attempt failed
        if self.fuzzy_matcher and self.config.get("use_fuzzy_matching", True):
            # Determine if this is likely a lab test or other measurement
            context_type = "lab_test" if self._is_lab_term(clean_term) else "measurement"
            fuzzy_result = self.fuzzy_matcher.find_fuzzy_match(clean_term, "loinc", context)
            if fuzzy_result:
                logger.debug(f"Found fuzzy LOINC match for '{term}': {fuzzy_result['code']} (match type: {fuzzy_result.get('match_type', 'unknown')}, score: {fuzzy_result.get('score', 0)})")
                # Apply context enhancement
                if context:
                    fuzzy_result = self._apply_context_enhancement(clean_term, fuzzy_result, context, context_type)
                
                # Add detailed information if requested
                if include_details and "code" in fuzzy_result:
                    detailed_result = self.db_manager.get_loinc_concept(fuzzy_result["code"], include_details=True)
                    if detailed_result:
                        # Preserve the original fuzzy match information
                        detailed_result["match_type"] = fuzzy_result.get("match_type", "fuzzy")
                        detailed_result["score"] = fuzzy_result.get("score", 0)
                        fuzzy_result = detailed_result
                        
                return fuzzy_result
        
        # 3. Try specialized pattern matching for common lab terms
        if self._is_lab_term(clean_term):
            try:
                # Get database connection directly for advanced pattern matching
                conn = self.db_manager.connections.get("loinc")
                if conn:
                    cursor = conn.cursor()
                    pattern_match = self.db_manager._try_common_lab_patterns(cursor, lab_term)
                    if pattern_match:
                        logger.debug(f"Found pattern-based LOINC match for '{term}': {pattern_match['code']} (pattern: {pattern_match.get('match_type', 'unknown')})")
                        # Apply context enhancement
                        if context:
                            pattern_match = self._apply_context_enhancement(clean_term, pattern_match, context, "lab_test")
                        
                        # Add detailed information if requested
                        if include_details and "code" in pattern_match:
                            detailed_result = self.db_manager.get_loinc_concept(pattern_match["code"], include_details=True)
                            if detailed_result:
                                # Preserve the original pattern match information
                                detailed_result["match_type"] = pattern_match.get("match_type", "pattern")
                                detailed_result["confidence"] = pattern_match.get("confidence", 0.8)
                                pattern_match = detailed_result
                                
                        return pattern_match
            except Exception as e:
                logger.error(f"Error during advanced LOINC pattern matching: {e}")
                
        # 4. Try external API if available
        if self.external_service and self.config.get("use_external_services", False):
            try:
                api_results = self.external_service.search_clinical_tables(clean_term, 'loinc')
                if api_results:
                    # Take the first result
                    result = api_results[0]
                    result['match_type'] = 'api'
                    result['confidence'] = 0.8
                    result['found'] = True
                    logger.debug(f"Found LOINC API match for '{term}': {result['code']}")
                    # Apply context enhancement
                    if context:
                        result = self._apply_context_enhancement(clean_term, result, context, "lab_test")
                    return result
            except Exception as e:
                logger.warning(f"External LOINC API error: {e}")
        
        # 5. Return not found with the original term
        logger.debug(f"No LOINC mapping found for '{term}'")
        return {
            "code": None, 
            "display": term, 
            "system": "http://loinc.org", 
            "found": False,
            "attempted_methods": ["exact", "pattern", 
                                 "fuzzy" if self.fuzzy_matcher else "",
                                 "api" if self.external_service else ""]
        }
    
    def map_to_rxnorm(self, term: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Map a medication term to RxNorm code.
        
        Args:
            term: The medication term to map
            context: Optional context information to improve mapping accuracy
            
        Returns:
            Dictionary with mapping results including code, display name,
            terminology system, and confidence score
        """
        if not term:
            return {
                "code": None, 
                "display": "", 
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm", 
                "found": False
            }
            
        # Clean and normalize the term
        clean_term = self._normalize_term(term)
        
        # Check for directly mappable synonyms from loaded dictionary
        synonym_result = self._check_synonyms(clean_term, "rxnorm")
        if synonym_result:
            logger.debug(f"Found synonym match for '{term}': {synonym_result['code']}")
            # Apply context enhancement for synonyms
            if context:
                synonym_result = self._apply_context_enhancement(clean_term, synonym_result, context, "medication")
            return synonym_result
            
        # 1. Try exact match in embedded database
        result = self.db_manager.lookup_rxnorm(clean_term)
        if result:
            logger.debug(f"Found exact RxNorm match for '{term}': {result['code']}")
            # Add confidence score for exact match
            result['confidence'] = 1.0
            result['match_type'] = 'exact'
            # Apply context enhancement
            if context:
                result = self._apply_context_enhancement(clean_term, result, context, "medication")
            return result
            
        # 2. Try fuzzy matching if available
        if self.fuzzy_matcher and self.config.get("use_fuzzy_matching", True):
            fuzzy_result = self.fuzzy_matcher.find_fuzzy_match(clean_term, "rxnorm", context)
            if fuzzy_result:
                logger.debug(f"Found fuzzy RxNorm match for '{term}': {fuzzy_result['code']} (match type: {fuzzy_result.get('match_type', 'unknown')}, score: {fuzzy_result.get('score', 0)})")
                # Apply context enhancement
                if context:
                    fuzzy_result = self._apply_context_enhancement(clean_term, fuzzy_result, context, "medication")
                return fuzzy_result
                
        # 3. Try external API if available
        if self.external_service and self.config.get("use_external_services", False):
            try:
                # Try RxNorm API first
                api_results = self.external_service.search_rxnorm(clean_term)
                if not api_results:
                    # Fallback to Clinical Tables
                    api_results = self.external_service.search_clinical_tables(clean_term, 'rxterms')
                
                if api_results:
                    # Take the first result
                    result = api_results[0]
                    result['match_type'] = 'api'
                    result['confidence'] = 0.8
                    result['found'] = True
                    logger.debug(f"Found RxNorm API match for '{term}': {result['code']}")
                    # Apply context enhancement
                    if context:
                        result = self._apply_context_enhancement(clean_term, result, context, "medication")
                    return result
            except Exception as e:
                logger.warning(f"External RxNorm API error: {e}")
        
        # 4. Return not found with the original term
        logger.debug(f"No RxNorm mapping found for '{term}'")
        return {
            "code": None, 
            "display": term, 
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm", 
            "found": False,
            "attempted_methods": ["exact", 
                                 "fuzzy" if self.fuzzy_matcher else "",
                                 "api" if self.external_service else ""]
        }
    
    def _normalize_term(self, term: str) -> str:
        """
        Normalize a medical term for better mapping.
        
        Args:
            term: The term to normalize
            
        Returns:
            Normalized term
        """
        if not term:
            return ""
        
        # Convert to lowercase
        term = term.lower()
        
        # Remove common prefix/suffix terms that might affect matching
        prefixes_to_remove = [
            "history of ", "chronic ", "acute ", "suspected ", "possible ",
            "probable ", "diagnosis of ", "patient has ", "patient with ",
            "underlying ", "recurrent ", "documented ", "confirmed ", "active "
        ]
        for prefix in prefixes_to_remove:
            if term.startswith(prefix):
                term = term[len(prefix):]
        
        # Remove punctuation that doesn't affect meaning
        import re
        term = re.sub(r'[,.;:!?()]', ' ', term)
        
        # Normalize whitespace
        term = re.sub(r'\s+', ' ', term).strip()
        
        # Normalize common symbols
        term = term.replace('%', ' percent').replace('&', ' and ')
        
        return term
    
    def _check_synonyms(self, term: str, system: str) -> Optional[Dict[str, Any]]:
        """
        Check if a term matches any synonym in our loaded synonym dictionaries.
        
        Args:
            term: The normalized term to check
            system: The terminology system to map to (snomed, loinc, rxnorm)
            
        Returns:
            Dictionary with mapping information or None if no synonym found
        """
        # Mapping of synonym set types to likely terminology systems
        system_mappings = {
            "snomed": ["_syn", "disease", "condition", "disorder", "finding", "procedure", "operation", "surgery"],
            "loinc": ["_test", "_measurement", "_lab", "_assessment", "_scale", "_score"],
            "rxnorm": ["_drug", "_medication", "_antibiotic", "_agent", "_therapy"]
        }
        
        # Check each synonym set
        for syn_key, syn_list in self.synonyms.items():
            # Skip sets that don't seem relevant to this system
            relevant_suffixes = system_mappings.get(system, [])
            if not any(suffix in syn_key.lower() for suffix in relevant_suffixes) and not syn_key.endswith("_syn"):
                continue
            
            # Check if term is in the synonym list
            if isinstance(syn_list, list) and term in syn_list:
                # Found a synonym match
                primary_term = syn_list[0]  # Primary term is usually the first one
                
                # Try to lookup the primary term in the database
                if system == "snomed":
                    result = self.db_manager.lookup_snomed(primary_term)
                elif system == "loinc":
                    result = self.db_manager.lookup_loinc(primary_term)
                    if result:
                        # Add confidence score for exact match
                        result['confidence'] = 1.0
                        result['match_type'] = 'exact'
                elif system == "rxnorm":
                    result = self.db_manager.lookup_rxnorm(primary_term)
                    if result:
                        # Add confidence score for exact match
                        result['confidence'] = 1.0
                        result['match_type'] = 'exact'
                else:
                    result = None
                
                if result:
                    # Add synonym information to the result
                    result["match_type"] = "synonym"
                    result["synonym_set"] = syn_key
                    result["score"] = 95  # High confidence for synonym matches
                    return result
        
        return None
    
    def _apply_context_enhancement(self, term: str, mapping_result: Dict[str, Any], 
                                  context: str, context_type: str) -> Dict[str, Any]:
        """
        Apply context-based enhancements to mapping results.
        
        Args:
            term: The term being mapped
            mapping_result: Current mapping result
            context: Context information
            context_type: Type of context enhancement to apply
            
        Returns:
            Enhanced mapping result
        """
        # Skip if no context provided or result already contains context enhancement
        if not context or mapping_result.get("context_enhanced", False):
            return mapping_result
        
        # Get the appropriate context enhancer function
        enhancer = self.clinical_context_enhancers.get(context_type)
        if not enhancer:
            # Try with a generic "medical" enhancer as fallback
            enhancer = self.clinical_context_enhancers.get("medical")
        
        # Apply the enhancer if available
        if enhancer:
            enhanced_result = enhancer(term, mapping_result, context)
            return enhanced_result
        
        return mapping_result
    
    def _is_lab_term(self, term: str) -> bool:
        """
        Check if a term is likely to be a laboratory test term.
        
        Args:
            term: The normalized term to check
            
        Returns:
            bool: True if the term appears to be a lab test
        """
        lab_keywords = [
            "test", "level", "measurement", "laboratory", "lab", "analysis",
            "count", "profile", "panel", "assay", "culture", "titer", "screen",
            "ratio", "blood", "serum", "plasma", "urine", "csf", "biopsy",
            "hemoglobin", "glucose", "creatinine", "sodium", "potassium",
            "calcium", "albumin", "bilirubin", "cholesterol", "triglyceride",
            "ldl", "hdl", "ast", "alt", "ggt", "wbc", "rbc", "platelet",
            "inr", "ptt", "troponin", "bnp", "tsh", "hba1c", "antibody"
        ]
        
        # Check for direct match with keywords
        if any(kw == term for kw in lab_keywords):
            return True
        
        # Check for partial matches
        return any(kw in term for kw in lab_keywords)
    
    def add_custom_mapping(self, system: str, term: str, code: str, display: str) -> bool:
        """
        Add a custom mapping to the database.
        
        Args:
            system: The terminology system (snomed, loinc, rxnorm)
            term: The term to map
            code: The code to map to
            display: The display name for the code
            
        Returns:
            bool: True if the mapping was added successfully
        """
        mapping = {
            "code": code,
            "display": display,
            "system": self._get_system_uri(system),
            "found": True
        }
        
        return self.db_manager.add_mapping(system, self._normalize_term(term), mapping)
    
    def _get_system_uri(self, system: str) -> str:
        """Get the URI for a terminology system."""
        systems = {
            "snomed": "http://snomed.info/sct",
            "loinc": "http://loinc.org",
            "rxnorm": "http://www.nlm.nih.gov/research/umls/rxnorm"
        }
        return systems.get(system.lower(), "unknown")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the terminology mapper.
        
        Returns:
            Dictionary with statistics about available mappings
        """
        stats = self.db_manager.get_statistics()
        
        # Add loaded synonyms statistics
        stats["synonyms"] = {
            "total_sets": len(self.synonyms),
            "total_terms": sum(len(syn_set) for syn_set in self.synonyms.values() if isinstance(syn_set, list))
        }
        
        # Add fuzzy matching statistics if available
        if self.fuzzy_matcher:
            stats["fuzzy_matching"] = {
                "available": True,
                "thresholds": getattr(self.fuzzy_matcher, "thresholds", {})
            }
        else:
            stats["fuzzy_matching"] = {"available": False}
        
        return stats
    
    def map_term(self, term: str, system: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Map a medical term to the specified terminology system.
        
        Args:
            term: The medical term to map
            system: The terminology system to map to (snomed, loinc, rxnorm)
            context: Optional context information to improve mapping accuracy
            
        Returns:
            Dictionary with mapping results including code, display name,
            terminology system, and confidence score
        """
        if not term or not system:
            return {
                "code": None,
                "display": term or "",
                "system": self._get_system_uri(system),
                "found": False
            }
            
        # Route to the appropriate mapping method
        system = system.lower()
        if system == "snomed":
            return self.map_to_snomed(term, context)
        elif system == "loinc":
            return self.map_to_loinc(term, context)
        elif system == "rxnorm":
            return self.map_to_rxnorm(term, context)
        else:
            logger.warning(f"Unsupported terminology system: {system}")
            return {
                "code": None,
                "display": term,
                "system": "unknown",
                "found": False,
                "error": f"Unsupported terminology system: {system}"
            }
    
    def add_synonyms(self, term: str, synonyms: List[str]) -> bool:
        """
        Add synonym mappings for a term.
        
        Args:
            term: The primary term
            synonyms: List of synonyms for the term
            
        Returns:
            bool: True if synonyms were added successfully
        """
        if not self.fuzzy_matcher:
            logger.warning("Fuzzy matcher not available, cannot add synonyms")
            return False
            
        return self.fuzzy_matcher.add_synonym(term, synonyms)
    
    def get_loinc_hierarchy(self, code: str, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get parent and child concepts in the LOINC hierarchy.
        
        Args:
            code: The LOINC code
            relationship_type: Optional specific hierarchy relationship type
            
        Returns:
            List of related LOINC concepts in the hierarchy
        """
        return self.db_manager.get_loinc_hierarchy(code, relationship_type)
    
    def get_loinc_by_part(self, part_number: str, part_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get LOINC concepts that contain a specific part.
        
        Args:
            part_number: The LOINC part number
            part_type: Optional specific part type (COMPONENT, METHOD, etc.)
            
        Returns:
            List of LOINC concepts that contain the specified part
        """
        return self.db_manager.get_loinc_by_part(part_number, part_type)
    
    def get_loinc_concept(self, code: str, include_details: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a LOINC concept by its code with optional details.
        
        Args:
            code: The LOINC code
            include_details: Whether to include detailed information about the concept
            
        Returns:
            Dictionary with LOINC concept information or None if not found
        """
        return self.db_manager.get_loinc_concept(code, include_details)
    
    def find_similar_lab_tests(self, term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar laboratory tests based on a search term.
        
        This is useful for suggesting alternatives when an exact match is not found.
        
        Args:
            term: The search term
            limit: Maximum number of results to return
            
        Returns:
            List of similar LOINC concepts
        """
        if not term:
            return []
            
        # Normalize the term for better matching
        normalized_term = self._normalize_term(term)
        lab_term = self.db_manager._normalize_lab_term(normalized_term)
        
        similar_concepts = []
        
        try:
            # Only proceed if we have a LOINC database connection
            if "loinc" not in self.db_manager.connections:
                return []
                
            conn = self.db_manager.connections["loinc"]
            cursor = conn.cursor()
            
            # First try to match on component
            cursor.execute(
                """SELECT code, display, component, property, system, long_common_name
                   FROM loinc_concepts
                   WHERE LOWER(component) LIKE ?
                   LIMIT ?""", 
                (f"%{lab_term}%", limit)
            )
            
            for row in cursor.fetchall():
                similar_concepts.append({
                    "code": row[0],
                    "display": row[1],
                    "component": row[2],
                    "property": row[3],
                    "specimen": row[4],
                    "long_common_name": row[5] if row[5] else row[1],
                    "system": "http://loinc.org",
                    "match_type": "component_similarity"
                })
                
            # If we still need more results, try matching on display or long name
            if len(similar_concepts) < limit:
                remaining = limit - len(similar_concepts)
                existing_codes = [c["code"] for c in similar_concepts]
                
                # Exclude codes we already found
                placeholders = ','.join(['?'] * len(existing_codes)) if existing_codes else "''"
                exclude_clause = f"AND code NOT IN ({placeholders})" if existing_codes else ""
                
                query = f"""SELECT code, display, component, property, system, long_common_name
                           FROM loinc_concepts
                           WHERE (LOWER(display) LIKE ? OR LOWER(long_common_name) LIKE ?)
                           {exclude_clause}
                           LIMIT ?"""
                
                params = [f"%{lab_term}%", f"%{lab_term}%"] + existing_codes + [remaining] if existing_codes else [f"%{lab_term}%", f"%{lab_term}%", remaining]
                
                cursor.execute(query, params)
                
                for row in cursor.fetchall():
                    similar_concepts.append({
                        "code": row[0],
                        "display": row[1],
                        "component": row[2],
                        "property": row[3],
                        "specimen": row[4],
                        "long_common_name": row[5] if row[5] else row[1],
                        "system": "http://loinc.org",
                        "match_type": "name_similarity"
                    })
            
            return similar_concepts
                
        except Exception as e:
            logger.error(f"Error finding similar lab tests for '{term}': {e}")
            return []
    
    def close(self):
        """Close all database connections and resources."""
        # Close database connections
        if self.db_manager:
            self.db_manager.close()
            
        # Close external services if available
        if self.external_service and hasattr(self.external_service, "close"):
            self.external_service.close()