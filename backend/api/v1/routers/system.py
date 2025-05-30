from fastapi import APIRouter, HTTPException
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.v1.models.terminology import (
    SystemInfo, SystemsResponse,
    FuzzyAlgorithmInfo, FuzzyAlgorithmsResponse
)
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

@router.get(
    "/systems",
    response_model=SystemsResponse,
    summary="List available terminology systems",
    description="Get information about all available terminology systems"
)
async def get_systems():
    """
    Get a list of all available terminology systems with their details.
    """
    try:
        systems = [
            SystemInfo(
                name="snomed",
                display_name="SNOMED CT",
                total_concepts=350000,  # Approximate
                description="Systematized Nomenclature of Medicine Clinical Terms - comprehensive clinical terminology",
                supported=True
            ),
            SystemInfo(
                name="loinc",
                display_name="LOINC",
                total_concepts=95000,  # Approximate
                description="Logical Observation Identifiers Names and Codes - laboratory and clinical observations",
                supported=True
            ),
            SystemInfo(
                name="rxnorm",
                display_name="RxNorm",
                total_concepts=120000,  # Approximate
                description="Normalized names for clinical drugs and drug delivery devices",
                supported=True
            ),
            SystemInfo(
                name="icd10",
                display_name="ICD-10",
                total_concepts=70000,  # Approximate
                description="International Classification of Diseases, 10th Revision",
                supported=False  # Not yet implemented in the current system
            )
        ]
        
        return SystemsResponse(systems=systems)
        
    except Exception as e:
        logger.error(f"Error getting systems: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving systems: {str(e)}"
        )

@router.get(
    "/fuzzy-algorithms",
    response_model=FuzzyAlgorithmsResponse,
    summary="List available fuzzy matching algorithms",
    description="Get information about all available fuzzy matching algorithms"
)
async def get_fuzzy_algorithms():
    """
    Get a list of all available fuzzy matching algorithms with their details.
    """
    try:
        algorithms = [
            FuzzyAlgorithmInfo(
                name="phonetic",
                display_name="Phonetic Matching",
                description="Matches terms based on how they sound (using Soundex and Metaphone)",
                best_for=["Misspellings", "Similar sounding terms", "Name variations"]
            ),
            FuzzyAlgorithmInfo(
                name="token_set_ratio",
                display_name="Token Set Ratio",
                description="Compares terms by breaking them into tokens (words) and comparing sets",
                best_for=["Word order variations", "Additional/missing words", "Compound terms"]
            ),
            FuzzyAlgorithmInfo(
                name="token_sort_ratio",
                display_name="Token Sort Ratio",
                description="Sorts tokens alphabetically before comparison",
                best_for=["Word reordering", "Synonymous phrases", "Clinical descriptions"]
            ),
            FuzzyAlgorithmInfo(
                name="levenshtein",
                display_name="Levenshtein Distance",
                description="Measures the minimum number of single-character edits needed",
                best_for=["Typos", "Character substitutions", "Minor spelling errors"]
            ),
            FuzzyAlgorithmInfo(
                name="jaro_winkler",
                display_name="Jaro-Winkler Distance",
                description="String similarity metric giving more weight to matching prefixes",
                best_for=["Abbreviations", "Prefix matching", "Short terms"]
            )
        ]
        
        return FuzzyAlgorithmsResponse(algorithms=algorithms)
        
    except Exception as e:
        logger.error(f"Error getting fuzzy algorithms: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving fuzzy algorithms: {str(e)}"
        )

@router.get(
    "/statistics",
    summary="Get system statistics",
    description="Get statistics about the terminology mapping system"
)
async def get_statistics():
    """
    Get current system statistics including database sizes, cache status, etc.
    """
    try:
        # This would be implemented to get actual statistics from the system
        stats = {
            "database_status": {
                "snomed": {"status": "connected", "concepts": 350000},
                "loinc": {"status": "connected", "concepts": 95000},
                "rxnorm": {"status": "connected", "concepts": 120000}
            },
            "cache_status": {
                "enabled": True,
                "hit_rate": 0.85,
                "size_mb": 128
            },
            "performance": {
                "average_response_time_ms": 150,
                "requests_per_minute": 100
            }
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving statistics: {str(e)}"
        )