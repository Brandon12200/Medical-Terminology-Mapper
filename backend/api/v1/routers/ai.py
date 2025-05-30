"""
AI-powered term extraction and mapping endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import logging

from api.v1.services.terminology_service import TerminologyService

router = APIRouter(prefix="/ai", tags=["AI"])
logger = logging.getLogger(__name__)

# Dependency to get terminology service
def get_terminology_service() -> TerminologyService:
    return TerminologyService()

class TextExtractionRequest(BaseModel):
    """Request model for text extraction."""
    text: str = Field(..., description="Clinical text to extract terms from", max_length=10000)
    systems: List[str] = Field(default=["all"], description="Terminology systems to map extracted terms to")
    fuzzy_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold for fuzzy matching")
    include_context: bool = Field(default=True, description="Use surrounding text as context for mapping")

class ExtractedTerm(BaseModel):
    """Model for an extracted term."""
    text: str
    entity_type: str
    confidence: float
    start: int
    end: int

class ExtractionResponse(BaseModel):
    """Response model for text extraction."""
    ai_enabled: bool
    extracted_terms: List[ExtractedTerm]
    mapped_terms: Dict[str, Any]
    extraction_method: str

@router.get(
    "/status",
    summary="Get AI capabilities status",
    description="Check if AI-powered features are enabled and available"
)
async def get_ai_status(
    service: TerminologyService = Depends(get_terminology_service)
):
    """Get the current status of AI capabilities."""
    try:
        return service.get_ai_status()
    except Exception as e:
        logger.error(f"Error getting AI status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/extract",
    response_model=ExtractionResponse,
    summary="Extract medical terms from text",
    description="Use AI (BioBERT) to extract medical terms from clinical text and optionally map them to standard terminologies"
)
async def extract_and_map_terms(
    request: TextExtractionRequest,
    service: TerminologyService = Depends(get_terminology_service)
):
    """
    Extract medical terms from clinical text using AI and map them to standard terminologies.
    
    This endpoint uses BioBERT for Named Entity Recognition (NER) to identify medical terms
    in free text, then maps those terms to standard terminology systems.
    
    Example:
    ```
    {
        "text": "Patient has diabetes mellitus type 2 and is taking metformin 1000mg daily",
        "systems": ["snomed", "rxnorm"],
        "fuzzy_threshold": 0.8
    }
    ```
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) > 10000:
            raise HTTPException(status_code=400, detail="Text too long (max 10000 characters)")
        
        # Extract and map terms
        result = await service.extract_and_map_terms(
            text=request.text,
            systems=request.systems,
            fuzzy_threshold=request.fuzzy_threshold,
            include_context=request.include_context
        )
        
        # Add extraction method to response
        extraction_method = "BioBERT NER" if result["ai_enabled"] else "Pattern Matching"
        
        return ExtractionResponse(
            ai_enabled=result["ai_enabled"],
            extracted_terms=result["extracted_terms"],
            mapped_terms=result["mapped_terms"],
            extraction_method=extraction_method
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in extract_and_map_terms: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class ExtractOnlyRequest(BaseModel):
    text: str = Field(..., description="Clinical text to extract terms from")

@router.post(
    "/extract-only",
    summary="Extract medical terms without mapping",
    description="Extract medical terms from text without mapping to terminologies"
)
async def extract_terms_only(
    request: ExtractOnlyRequest,
    service: TerminologyService = Depends(get_terminology_service)
):
    """Extract medical terms without mapping them to terminologies."""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Extract terms without mapping
        result = await service.extract_and_map_terms(
            text=request.text,
            systems=[],  # Empty systems list means no mapping
            fuzzy_threshold=0.0,
            include_context=False
        )
        
        return {
            "ai_enabled": result["ai_enabled"],
            "extracted_terms": result["extracted_terms"],
            "extraction_method": "BioBERT NER" if result["ai_enabled"] else "Pattern Matching"
        }
        
    except Exception as e:
        logger.error(f"Error in extract_terms_only: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))