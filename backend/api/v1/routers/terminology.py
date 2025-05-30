from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import time
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.v1.models.terminology import (
    MappingRequest, MappingResponse, TermMapping,
    TerminologySystem, FuzzyAlgorithm, ErrorResponse
)
from api.v1.services.terminology_service import TerminologyService
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

# Initialize service
terminology_service = TerminologyService()

@router.post(
    "/map",
    response_model=MappingResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Term not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Map a medical term",
    description="Map a medical term to standardized terminology codes"
)
async def map_term(request: MappingRequest):
    """
    Map a medical term to standardized terminology systems.
    
    - **term**: The medical term to map
    - **systems**: List of terminology systems to search (default: all)
    - **context**: Clinical context for better matching
    - **fuzzy_threshold**: Minimum confidence for fuzzy matches (0.0-1.0)
    - **fuzzy_algorithms**: List of fuzzy algorithms to use
    - **max_results**: Maximum results per system
    """
    try:
        start_time = time.time()
        
        # Convert enums to strings
        systems = [s.value if isinstance(s, TerminologySystem) else s for s in request.systems]
        algorithms = [a.value if isinstance(a, FuzzyAlgorithm) else a for a in request.fuzzy_algorithms]
        
        # Call service
        results = await terminology_service.map_term(
            term=request.term,
            systems=systems,
            context=request.context,
            fuzzy_threshold=request.fuzzy_threshold,
            fuzzy_algorithms=algorithms,
            max_results=request.max_results
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Count total matches
        total_matches = sum(len(mappings) for mappings in results.values())
        
        return MappingResponse(
            term=request.term,
            results=results,
            total_matches=total_matches,
            processing_time_ms=round(processing_time, 2)
        )
        
    except ValueError as e:
        logger.error(f"Value error mapping term '{request.term}': {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error mapping term '{request.term}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error processing term: {str(e)}"
        )

@router.get(
    "/map",
    response_model=MappingResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Term not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Map a medical term (GET)",
    description="Map a medical term using query parameters"
)
async def map_term_get(
    term: str = Query(..., min_length=1, description="Medical term to map"),
    systems: Optional[List[str]] = Query(default=["all"], description="Terminology systems"),
    context: Optional[str] = Query(default=None, description="Clinical context"),
    fuzzy_threshold: float = Query(default=0.7, ge=0.0, le=1.0),
    fuzzy_algorithms: Optional[List[str]] = Query(default=["all"]),
    max_results: int = Query(default=10, ge=1, le=100)
):
    """
    Map a medical term using GET request with query parameters.
    """
    request = MappingRequest(
        term=term,
        systems=[TerminologySystem(s) if s in [e.value for e in TerminologySystem] else s for s in systems],
        context=context,
        fuzzy_threshold=fuzzy_threshold,
        fuzzy_algorithms=[FuzzyAlgorithm(a) if a in [e.value for e in FuzzyAlgorithm] else a for a in fuzzy_algorithms],
        max_results=max_results
    )
    
    return await map_term(request)