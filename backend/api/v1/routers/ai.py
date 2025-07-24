"""
AI-powered medical entity extraction API endpoints

This module provides REST API endpoints for BioBERT-based medical entity
extraction and document analysis.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from app.ml.biobert import create_biobert_service, MedicalEntity, DocumentAnalysis
from app.utils.logger import setup_logger
from api.v1.models.document import DocumentStatus
from api.v1.services.document_service import DocumentService

logger = setup_logger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Entity Extraction"])


# Pydantic models for API
class EntityExtractionRequest(BaseModel):
    """Request model for entity extraction"""
    text: str = Field(..., description="Text to extract entities from")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum confidence threshold")
    extract_context: bool = Field(True, description="Extract surrounding context for entities")
    map_to_terminologies: bool = Field(True, description="Map entities to standard terminologies")
    use_ensemble: bool = Field(True, description="Use ensemble approach (BioBERT + regex)")


class MedicalEntityResponse(BaseModel):
    """Response model for medical entity"""
    text: str
    normalized_text: str
    entity_type: str
    start_position: int
    end_position: int
    confidence: float
    source: str
    context: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    terminology_mappings: Optional[Dict[str, List[Dict[str, Any]]]] = None


class EntityExtractionResponse(BaseModel):
    """Response model for entity extraction"""
    entities: List[MedicalEntityResponse]
    processing_time: float
    entity_count: int
    extraction_methods: List[str]


class DocumentAnalysisResponse(BaseModel):
    """Response model for document analysis"""
    entities: List[MedicalEntityResponse]
    entity_summary: Dict[str, int]
    processing_time: float
    chunks_processed: int
    extraction_methods: List[str]
    confidence_stats: Dict[str, float]
    total_entities: int


class BatchExtractionRequest(BaseModel):
    """Request model for batch entity extraction"""
    texts: List[str] = Field(..., description="List of texts to process")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)
    batch_size: int = Field(8, ge=1, le=32, description="Processing batch size")


class ModelStatusResponse(BaseModel):
    """Response model for model status"""
    service_name: str
    model_loaded: bool
    model_info: Dict[str, Any]
    configuration: Dict[str, Any]


# Service dependencies
_biobert_service = None

def get_biobert_service():
    """Get or create BioBERT service instance"""
    global _biobert_service
    if _biobert_service is None:
        # Import terminology mapper if available
        try:
            from app.standards.terminology.mapper import TerminologyMapper
            terminology_mapper = TerminologyMapper()
        except ImportError:
            logger.warning("Terminology mapper not available")
            terminology_mapper = None
        
        _biobert_service = create_biobert_service(
            use_regex_patterns=True,
            use_ensemble=True,
            confidence_threshold=0.7,
            terminology_mapper=terminology_mapper
        )
    return _biobert_service


@router.post("/extract-entities", response_model=EntityExtractionResponse)
async def extract_entities(request: EntityExtractionRequest):
    """
    Extract medical entities from text using BioBERT
    
    This endpoint uses BioBERT and optional regex patterns to extract medical
    entities such as conditions, medications, procedures, and lab tests from
    the provided text.
    """
    try:
        service = get_biobert_service()
        
        # Update service configuration based on request
        service.confidence_threshold = request.confidence_threshold
        service.use_ensemble = request.use_ensemble
        
        # Extract entities
        entities = service.extract_entities(
            text=request.text,
            extract_context=request.extract_context,
            map_to_terminologies=request.map_to_terminologies
        )
        
        # Determine extraction methods used
        extraction_methods = list(set(entity.source for entity in entities))
        
        # Convert to response model
        entity_responses = [
            MedicalEntityResponse(
                text=entity.text,
                normalized_text=entity.normalized_text,
                entity_type=entity.entity_type,
                start_position=entity.start_position,
                end_position=entity.end_position,
                confidence=entity.confidence,
                source=entity.source,
                context=entity.context,
                attributes=entity.attributes,
                terminology_mappings=entity.terminology_mappings
            )
            for entity in entities
        ]
        
        return EntityExtractionResponse(
            entities=entity_responses,
            processing_time=0.0,  # Would be tracked in service
            entity_count=len(entities),
            extraction_methods=extraction_methods
        )
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-document", response_model=DocumentAnalysisResponse)
async def analyze_document(request: EntityExtractionRequest):
    """
    Perform comprehensive document analysis
    
    This endpoint provides detailed analysis of a medical document including
    entity extraction, statistics, and confidence scores.
    """
    try:
        service = get_biobert_service()
        
        # Perform analysis
        analysis = service.analyze_document(
            text=request.text,
            extract_context=request.extract_context,
            map_to_terminologies=request.map_to_terminologies
        )
        
        # Convert entities to response model
        entity_responses = [
            MedicalEntityResponse(
                text=entity.text,
                normalized_text=entity.normalized_text,
                entity_type=entity.entity_type,
                start_position=entity.start_position,
                end_position=entity.end_position,
                confidence=entity.confidence,
                source=entity.source,
                context=entity.context,
                attributes=entity.attributes,
                terminology_mappings=entity.terminology_mappings
            )
            for entity in analysis.entities
        ]
        
        return DocumentAnalysisResponse(
            entities=entity_responses,
            entity_summary=analysis.entity_summary,
            processing_time=analysis.processing_time,
            chunks_processed=analysis.chunks_processed,
            extraction_methods=analysis.extraction_methods,
            confidence_stats=analysis.confidence_stats,
            total_entities=len(analysis.entities)
        )
        
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-entities-batch")
async def extract_entities_batch(request: BatchExtractionRequest):
    """
    Extract entities from multiple texts in batch
    
    This endpoint efficiently processes multiple texts using batch processing
    for improved performance.
    """
    try:
        service = get_biobert_service()
        service.confidence_threshold = request.confidence_threshold
        
        # Process batch
        batch_results = service.extract_entities_batch(
            texts=request.texts,
            batch_size=request.batch_size
        )
        
        # Format response
        results = []
        for text, entities in zip(request.texts, batch_results):
            results.append({
                "text": text[:100] + "..." if len(text) > 100 else text,
                "entities": [
                    {
                        "text": entity.text,
                        "type": entity.entity_type,
                        "confidence": entity.confidence,
                        "position": [entity.start_position, entity.end_position]
                    }
                    for entity in entities
                ],
                "entity_count": len(entities)
            })
        
        return {
            "batch_size": len(request.texts),
            "results": results,
            "total_entities": sum(r["entity_count"] for r in results)
        }
        
    except Exception as e:
        logger.error(f"Batch extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-document-file")
async def analyze_document_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    confidence_threshold: float = 0.7,
    map_to_terminologies: bool = True
):
    """
    Analyze uploaded document file
    
    This endpoint accepts document files (PDF, DOCX, TXT) and performs
    entity extraction after text extraction.
    """
    try:
        # Validate file type
        allowed_types = [".pdf", ".docx", ".txt", ".rtf"]
        file_extension = "." + file.filename.split(".")[-1].lower()
        
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_extension} not supported. Allowed types: {allowed_types}"
            )
        
        # Create document record
        document_service = DocumentService()
        document_id = str(uuid.uuid4())
        
        # Save file and create document record
        file_content = await file.read()
        document_info = {
            "id": document_id,
            "filename": file.filename,
            "status": DocumentStatus.PENDING,
            "created_at": datetime.utcnow()
        }
        
        # Queue for background processing
        background_tasks.add_task(
            process_document_with_ai,
            document_id,
            file_content,
            file.filename,
            confidence_threshold,
            map_to_terminologies
        )
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "processing",
            "message": "Document queued for AI analysis"
        }
        
    except Exception as e:
        logger.error(f"Document file analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/status", response_model=ModelStatusResponse)
async def get_model_status():
    """
    Get AI model status and information
    
    This endpoint provides information about loaded models and service configuration.
    """
    try:
        service = get_biobert_service()
        service_info = service.get_service_info()
        
        return ModelStatusResponse(
            service_name=service_info["service"],
            model_loaded=service_info["model"]["is_loaded"],
            model_info=service_info["model"],
            configuration=service_info["configuration"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/initialize")
async def initialize_models():
    """
    Initialize AI models
    
    This endpoint triggers model initialization if not already loaded.
    """
    try:
        service = get_biobert_service()
        manager = service.model_manager
        
        if manager._is_loaded:
            return {
                "status": "already_initialized",
                "message": "Models are already loaded"
            }
        
        success = manager.initialize_model()
        
        if success:
            return {
                "status": "initialized",
                "message": "Models initialized successfully",
                "model_info": manager.get_model_info()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Model initialization failed"
            )
            
    except Exception as e:
        logger.error(f"Model initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task function
async def process_document_with_ai(
    document_id: str,
    file_content: bytes,
    filename: str,
    confidence_threshold: float,
    map_to_terminologies: bool
):
    """Background task to process document with AI"""
    try:
        # This would integrate with the document processing pipeline
        # For now, it's a placeholder
        logger.info(f"Processing document {document_id} with AI analysis")
        # Implementation would extract text and run AI analysis
        
    except Exception as e:
        logger.error(f"Background AI processing failed for {document_id}: {e}")