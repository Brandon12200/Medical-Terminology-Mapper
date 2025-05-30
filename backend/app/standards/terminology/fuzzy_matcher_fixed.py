"""Fixed fuzzy matcher that handles each terminology system independently."""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Try to import scikit-learn for TF-IDF vectorization
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

class FuzzyMatcherFixed:
    """Fixed fuzzy matcher that properly handles per-system vectorization."""
    
    def __init__(self, original_matcher):
        """Initialize with reference to original matcher."""
        self.original_matcher = original_matcher
        self.vectorizers = {}  # Separate vectorizer for each system
        self.vector_matrices = {}
        
    def find_cosine_match(self, term: str, system: str) -> Optional[Dict[str, Any]]:
        """
        Find the best cosine similarity match using TF-IDF with per-system vectorizers.
        
        Args:
            term: The term to match
            system: The terminology system to search
            
        Returns:
            Dictionary with mapping information or None if no good match
        """
        if not HAS_SKLEARN or system not in self.original_matcher.term_lists:
            return None
            
        try:
            # Initialize vectorizer for this system if needed
            if system not in self.vectorizers and self.original_matcher.term_lists[system]:
                terms = [term for _, term, _ in self.original_matcher.term_lists[system]]
                
                # Create system-specific vectorizer
                self.vectorizers[system] = TfidfVectorizer(
                    analyzer='word',
                    tokenizer=self.original_matcher._tokenize,
                    lowercase=True,
                    stop_words=self.original_matcher.stopwords,
                    ngram_range=(1, 2)
                )
                
                # Fit and transform on this system's terms
                self.vector_matrices[system] = self.vectorizers[system].fit_transform(terms)
                logger.info(f"Built TF-IDF matrix for {system} with shape {self.vector_matrices[system].shape}")
            
            # If we have a vectorizer for this system, use it
            if system in self.vectorizers:
                # Transform the query term using the system-specific vectorizer
                term_vector = self.vectorizers[system].transform([term])
                
                # Calculate cosine similarities
                similarities = cosine_similarity(term_vector, self.vector_matrices[system]).flatten()
                
                # Find the best match
                best_idx = np.argmax(similarities)
                best_score = similarities[best_idx]
                
                if best_score >= self.original_matcher.thresholds.get("cosine", 0.7):
                    code, _, display = self.original_matcher.term_lists[system][best_idx]
                    
                    return {
                        "code": code,
                        "display": display,
                        "system": self.original_matcher._get_system_uri(system),
                        "found": True,
                        "match_type": "cosine",
                        "score": float(best_score * 100)  # Convert to percentage
                    }
        except Exception as e:
            logger.warning(f"Error in cosine similarity for term '{term}' in {system}: {e}")
            
        return None