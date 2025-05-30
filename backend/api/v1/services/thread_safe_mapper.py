"""Thread-safe terminology mapper for use with FastAPI."""
import threading
from typing import Dict, List, Optional, Any
from app.standards.terminology.mapper import TerminologyMapper
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ThreadSafeTerminologyMapper:
    """Thread-safe wrapper for TerminologyMapper that creates new instances per thread."""
    
    def __init__(self):
        self._local = threading.local()
        self._lock = threading.Lock()
    
    def _get_mapper(self) -> TerminologyMapper:
        """Get or create a mapper instance for the current thread."""
        if not hasattr(self._local, 'mapper'):
            with self._lock:
                if not hasattr(self._local, 'mapper'):
                    logger.info(f"Creating new mapper instance for thread {threading.current_thread().ident}")
                    self._local.mapper = TerminologyMapper()
        return self._local.mapper
    
    def map_term(
        self,
        term: str,
        systems: List[str] = None,
        fuzzy_threshold: float = 0.7,
        context: Optional[str] = None,
        include_fuzzy: bool = True,
        max_results_per_system: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Thread-safe term mapping."""
        mapper = self._get_mapper()
        
        # Map term for each system
        all_results = {}
        if systems is None or 'all' in systems:
            systems = ['snomed', 'loinc', 'rxnorm']
            
        for system in systems:
            try:
                results = mapper.map_term(
                    term=term,
                    system=system,
                    context=context
                )
                
                # Format results
                if results and results.get("found", False):
                    system_results = [{
                        "code": results.get("code", ""),
                        "display": results.get("display", ""),
                        "system": system,
                        "confidence": results.get("confidence", 1.0),
                        "match_type": results.get("match_type", "exact")
                    }]
                    all_results[system] = system_results
                        
            except Exception as e:
                logger.warning(f"Error mapping term '{term}' in system '{system}': {str(e)}")
                
        return all_results
    
    def get_systems_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available terminology systems."""
        mapper = self._get_mapper()
        return mapper.get_systems_info()