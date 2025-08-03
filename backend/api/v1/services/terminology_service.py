import sys
import os
from typing import List, Dict, Optional, Any
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.v1.services.thread_safe_mapper import ThreadSafeTerminologyMapper
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class TerminologyService:
    def __init__(self):
        """Initialize terminology service."""
        try:
            self.mapper = ThreadSafeTerminologyMapper()
            
            # AI term extraction disabled - only fuzzy matching available
            self.term_extractor = None
            self.ai_enabled = False
            logger.info("Terminology service initialized (fuzzy matching only)")
                
            logger.info("Terminology service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize terminology service: {str(e)}")
            raise

    async def map_term(
        self,
        term: str,
        systems: List[str] = ["all"],
        context: Optional[str] = None,
        fuzzy_threshold: float = 0.7,
        fuzzy_algorithms: List[str] = ["all"],
        max_results: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Map term to standardized terminologies.
            context: Clinical context for better matching
            fuzzy_threshold: Minimum confidence for fuzzy matches
            fuzzy_algorithms: List of fuzzy algorithms to use
            max_results: Maximum results per system
            
        Returns:
            Dictionary mapping system names to lists of matches
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Determine which systems to search
            if "all" in systems:
                target_systems = ["snomed", "loinc", "rxnorm"]
            else:
                target_systems = [s.lower() for s in systems]
            
            # Map term using thread-safe mapper
            results = await loop.run_in_executor(
                None,
                lambda: self.mapper.map_term(
                    term=term,
                    systems=target_systems,
                    fuzzy_threshold=fuzzy_threshold,
                    context=context,
                    max_results_per_system=max_results
                )
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error mapping term '{term}': {str(e)}", exc_info=True)
            raise


    async def batch_map_terms(
        self,
        terms: List[str],
        systems: List[str] = ["all"],
        context: Optional[str] = None,
        fuzzy_threshold: float = 0.7,
        fuzzy_algorithms: List[str] = ["all"],
        max_results_per_term: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Map multiple terms in batch.
        
        Args:
            terms: List of medical terms to map
            systems: List of terminology systems to search
            context: Clinical context for better matching
            fuzzy_threshold: Minimum confidence for fuzzy matches
            fuzzy_algorithms: List of fuzzy algorithms to use
            max_results_per_term: Maximum results per term
            
        Returns:
            List of mapping results for each term
        """
        try:
            # Process terms with rate limiting to avoid overwhelming APIs
            results = []
            batch_size = 5  # Process 5 terms at a time
            delay_between_batches = 0.2  # 200ms delay between batches
            
            for i in range(0, len(terms), batch_size):
                batch_terms = terms[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}: terms {i+1}-{min(i+batch_size, len(terms))} of {len(terms)}")
                
                # Process current batch concurrently
                tasks = []
                for term in batch_terms:
                    task = self.map_term(
                        term=term,
                        systems=systems,
                        context=context,
                        fuzzy_threshold=fuzzy_threshold,
                        fuzzy_algorithms=fuzzy_algorithms,
                        max_results=max_results_per_term
                    )
                    tasks.append(task)
                
                # Wait for current batch to complete with timeout
                try:
                    batch_results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=15  # 15 second timeout per batch
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Batch {i//batch_size + 1} timed out, creating error results")
                    batch_results = [Exception("Request timed out") for _ in batch_terms]
                results.extend(batch_results)
                
                # Add delay between batches to avoid rate limiting
                if i + batch_size < len(terms):
                    await asyncio.sleep(delay_between_batches)
            
            # Format results
            formatted_results = []
            for i, (term, result) in enumerate(zip(terms, results)):
                if isinstance(result, Exception):
                    logger.error(f"Error mapping term '{term}': {str(result)}")
                    formatted_results.append({
                        "term": term,
                        "results": {},
                        "error": str(result)
                    })
                else:
                    formatted_results.append({
                        "term": term,
                        "results": result
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in batch mapping: {str(e)}", exc_info=True)
            raise

    def get_ai_status(self) -> Dict[str, Any]:
        """Get the status of AI capabilities."""
        return {
            "ai_enabled": self.ai_enabled,
            "model": "BioBERT (dmis-lab/biobert-base-cased-v1.2)" if self.ai_enabled else None,
            "capabilities": ["medical_term_extraction", "named_entity_recognition"] if self.ai_enabled else [],
            "status": "active" if self.ai_enabled else "disabled"
        }
    
    async def extract_and_map_terms(
        self,
        text: str,
        systems: List[str] = ["all"],
        fuzzy_threshold: float = 0.7,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Extract medical terms from text using AI and map them to terminologies.
        
        Args:
            text: Clinical text to extract terms from
            systems: Terminology systems to map to
            fuzzy_threshold: Minimum confidence for fuzzy matches
            include_context: Whether to use surrounding text as context
            
        Returns:
            Dictionary with extracted terms and their mappings
        """
        try:
            result = {
                "ai_enabled": self.ai_enabled,
                "extracted_terms": [],
                "mapped_terms": {}
            }
            
            # AI term extraction disabled - use pattern-based extraction as fallback
            logger.info("AI term extraction disabled - using pattern-based extraction")
            
            # Simple pattern matching for common medical terms
            import re
            medical_patterns = [
                r'\b(?:diabetes|hypertension|asthma|pneumonia|covid-19|coronavirus)\b',
                r'\b(?:glucose|hemoglobin|creatinine|cholesterol)\b',
                r'\b(?:metformin|insulin|aspirin|lisinopril)\b'
            ]
            
            for pattern in medical_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    term = match.group()
                    if term not in [t["text"] for t in result["extracted_terms"]]:
                        term_info = {
                            "text": term,
                            "entity_type": "PATTERN_MATCH",
                            "confidence": 0.7,
                            "start": match.start(),
                            "end": match.end()
                        }
                        result["extracted_terms"].append(term_info)
                        
                        # Map the term
                        mapping_result = await self.map_term(
                            term=term,
                            systems=systems,
                            fuzzy_threshold=fuzzy_threshold
                        )
                        
                        if mapping_result:
                            result["mapped_terms"][term] = mapping_result
            
            return result
            
        except Exception as e:
            logger.error(f"Error in extract_and_map_terms: {str(e)}")
            raise