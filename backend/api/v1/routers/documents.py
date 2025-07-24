"""
Document upload and processing API endpoints
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models.document import (
    DocumentType, DocumentStatus, DocumentUploadResponse,
    DocumentProcessingStatus, DocumentListResponse,
    DocumentDeleteResponse, ExtractedText
)
from ..models.document_batch import (
    BatchUploadResponse, BatchProcessingStatus,
    BatchResultsSummary, BatchExportFormat,
    BatchUploadStatus, BatchDocumentItem
)
from typing import List, Dict, Any
from ..services.document_service import DocumentService
from app.utils.logger import setup_logger


logger = setup_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service() -> DocumentService:
    """Dependency to get document service instance"""
    return DocumentService()


@router.post("/upload", 
    response_model=DocumentUploadResponse,
    summary="Upload a document",
    description="Upload a medical document (PDF, DOCX, TXT, RTF, or HL7) for processing"
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to upload"),
    document_type: DocumentType = Form(..., description="Type of document being uploaded"),
    metadata: Optional[str] = Form(None, description="Optional JSON metadata"),
    service: DocumentService = Depends(get_document_service)
):
    """
    Upload a document for text extraction and medical term processing.
    
    Supported file types:
    - PDF: Clinical reports, lab results, discharge summaries
    - DOCX: Medical notes, consultation reports
    - TXT: Plain text clinical notes
    - RTF: Formatted medical documents
    - HL7: Health Level 7 messages
    
    The document will be validated, stored, and queued for processing.
    """
    try:
        # Validate file extension matches document type
        file_ext = file.filename.split('.')[-1].lower()
        expected_ext = document_type.value
        
        if file_ext != expected_ext:
            raise HTTPException(
                status_code=400,
                detail=f"File extension '{file_ext}' does not match document type '{document_type}'"
            )
        
        # Read file content
        content = await file.read()
        
        # Parse metadata if provided
        parsed_metadata = None
        if metadata:
            try:
                import json
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid metadata format. Must be valid JSON"
                )
        
        # Save document
        response = await service.save_document(
            content=content,
            filename=file.filename,
            document_type=document_type,
            metadata=parsed_metadata
        )
        
        # Queue document for text extraction processing
        try:
            from app.processing.document_processor import queue_document_processing
            task_id = queue_document_processing(str(response.document_id))
            logger.info(f"Document {response.document_id} queued for processing with task ID: {task_id}")
        except Exception as e:
            logger.warning(f"Failed to queue document for processing: {e}")
            # Don't fail the upload if queueing fails - document is still saved
        
        logger.info(f"Document uploaded successfully: {response.document_id}")
        return response
        
    except ValueError as e:
        logger.error(f"Document upload validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during upload")


@router.get("/{document_id}/status",
    response_model=DocumentProcessingStatus,
    summary="Get document processing status",
    description="Check the processing status of an uploaded document"
)
async def get_document_status(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service)
):
    """
    Get the current processing status of a document.
    
    Status values:
    - pending: Document uploaded, waiting for processing
    - processing: Text extraction in progress
    - completed: Processing finished successfully
    - failed: Processing failed with error
    - cancelled: Processing was cancelled
    """
    status = service.get_document_status(document_id)
    
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID {document_id} not found"
        )
    
    return status


@router.get("/",
    response_model=DocumentListResponse,
    summary="List uploaded documents",
    description="Get a paginated list of uploaded documents"
)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    service: DocumentService = Depends(get_document_service)
):
    """
    List all uploaded documents with pagination support.
    
    Optional filtering by processing status.
    """
    documents, total = service.list_documents(page, page_size, status)
    
    return DocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document",
    description="Delete an uploaded document and its associated data"
)
async def delete_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service)
):
    """
    Delete a document and all associated data.
    
    This will remove:
    - The uploaded file
    - Database entries
    - Any extracted text or processing results
    """
    from datetime import datetime
    
    deleted = await service.delete_document(document_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID {document_id} not found"
        )
    
    return DocumentDeleteResponse(
        document_id=document_id,
        deleted_at=datetime.utcnow()
    )


@router.get("/{document_id}/metadata",
    summary="Get document metadata",
    description="Retrieve metadata for an uploaded document"
)
async def get_document_metadata(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service)
):
    """
    Get detailed metadata about an uploaded document.
    
    Includes:
    - File information (size, type, checksum)
    - Upload details
    - Processing metadata
    - Custom metadata if provided
    """
    metadata = service.get_document_metadata(document_id)
    
    if not metadata:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID {document_id} not found"
        )
    
    return metadata


@router.get("/{document_id}/text",
    response_model=ExtractedText,
    summary="Get extracted text",
    description="Retrieve extracted text content from a processed document"
)
async def get_extracted_text(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service)
):
    """
    Get the extracted text content from a document.
    
    This endpoint returns the full extracted text along with metadata
    about the extraction process. The document must have been successfully
    processed for text to be available.
    
    Returns:
    - text_content: The extracted text
    - sections: Text divided by sections if detected
    - metadata: Document metadata
    - extraction_method: Method used for extraction
    """
    extracted_text = service.get_extracted_text(document_id)
    
    if not extracted_text:
        # Check if document exists
        status = service.get_document_status(document_id)
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        
        if status.status == DocumentStatus.PENDING:
            raise HTTPException(
                status_code=202,
                detail="Document is pending processing"
            )
        elif status.status == DocumentStatus.PROCESSING:
            raise HTTPException(
                status_code=202,
                detail="Document is currently being processed"
            )
        elif status.status == DocumentStatus.FAILED:
            raise HTTPException(
                status_code=422,
                detail=f"Document processing failed: {status.error_message}"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="No extracted text available for this document"
            )
    
    return extracted_text


@router.get("/{document_id}/extract-entities",
    summary="Extract medical entities from document",
    description="Extract medical entities using advanced BioBERT with NER capabilities"
)
async def extract_entities(
    document_id: UUID,
    use_advanced: bool = Query(True, description="Use advanced MedicalEntityExtractor"),
    include_negation: bool = Query(True, description="Include negation detection"),
    include_uncertainty: bool = Query(True, description="Include uncertainty detection"),
    confidence_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    map_to_terminologies: bool = Query(False, description="Map entities to standard terminologies (SNOMED, LOINC, RxNorm)"),
    service: DocumentService = Depends(get_document_service)
):
    """
    Extract medical entities from a processed document using BioBERT.
    
    Entity types extracted:
    - CONDITION: Diseases, disorders, symptoms
    - DRUG: Medications, drugs
    - PROCEDURE: Medical procedures
    - TEST: Lab tests, diagnostic tests
    - ANATOMY: Body parts, organs
    - DOSAGE: Medication dosages
    - FREQUENCY: Medication frequencies
    - OBSERVATION: Clinical observations
    
    Advanced features:
    - Negation detection (e.g., "no evidence of diabetes")
    - Uncertainty detection (e.g., "possible pneumonia")
    - Confidence calibration
    - Entity linking to knowledge bases
    - Hierarchical entity recognition
    - Terminology mapping to standard codes:
      - CONDITIONS → SNOMED CT
      - DRUGS → RxNorm
      - LAB TESTS → LOINC
    """
    # Get extracted text first
    extracted_text = service.get_extracted_text(document_id)
    
    if not extracted_text:
        # Check if document exists
        status = service.get_document_status(document_id)
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        
        if status.status != DocumentStatus.COMPLETED:
            raise HTTPException(
                status_code=422,
                detail=f"Document must be processed first. Current status: {status.status}"
            )
    
    try:
        from app.ml.biobert.biobert_service import BioBERTService
        
        # Initialize terminology mapper if requested
        terminology_mapper = None
        if map_to_terminologies:
            from app.standards.terminology.mapper import TerminologyMapper
            terminology_mapper = TerminologyMapper()
        
        # Initialize BioBERT service with advanced extractor
        biobert_service = BioBERTService(
            use_advanced_extractor=use_advanced,
            confidence_threshold=confidence_threshold,
            terminology_mapper=terminology_mapper
        )
        
        # Extract entities
        entities = biobert_service.extract_entities(
            extracted_text.text_content,
            extract_context=True,
            map_to_terminologies=map_to_terminologies
        )
        
        # Convert to response format
        response_entities = []
        for entity in entities:
            entity_dict = {
                "text": entity.text,
                "normalized_text": entity.normalized_text,
                "type": entity.entity_type,
                "start": entity.start_position,
                "end": entity.end_position,
                "confidence": entity.confidence,
                "source": entity.source,
                "context": entity.context
            }
            
            # Add advanced attributes if available
            if entity.attributes:
                if include_negation and "negated" in entity.attributes:
                    entity_dict["negated"] = entity.attributes["negated"]
                if include_uncertainty and "uncertain" in entity.attributes:
                    entity_dict["uncertain"] = entity.attributes["uncertain"]
                if "linked_id" in entity.attributes:
                    entity_dict["linked_id"] = entity.attributes["linked_id"]
                if "hierarchy" in entity.attributes:
                    entity_dict["hierarchy"] = entity.attributes["hierarchy"]
            
            # Add terminology mappings if available
            if entity.terminology_mappings:
                entity_dict["terminology_mappings"] = entity.terminology_mappings
            
            response_entities.append(entity_dict)
        
        # Group by entity type
        entities_by_type = {}
        for entity in response_entities:
            entity_type = entity["type"]
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        return {
            "document_id": str(document_id),
            "total_entities": len(response_entities),
            "entities": response_entities,
            "entities_by_type": entities_by_type,
            "extraction_method": "advanced_biobert" if use_advanced else "standard_biobert",
            "confidence_threshold": confidence_threshold,
            "features": {
                "negation_detection": include_negation,
                "uncertainty_detection": include_uncertainty,
                "entity_linking": use_advanced,
                "hierarchical_recognition": use_advanced,
                "terminology_mapping": map_to_terminologies
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to extract entities for document {document_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract entities: {str(e)}"
        )


# Health check for document service
@router.get("/health",
    summary="Document service health check",
    description="Check if document upload service is operational"
)
async def document_service_health():
    """
    Verify that the document service is running and storage is accessible.
    """
    try:
        service = DocumentService()
        # Test database connection
        with service._get_db() as conn:
            conn.execute("SELECT 1")
        
        # Test upload directory access
        if not service.upload_dir.exists():
            raise Exception("Upload directory not accessible")
        
        return {
            "status": "healthy",
            "service": "document_upload",
            "upload_directory": str(service.upload_dir),
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Document service health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "document_upload",
                "error": str(e)
            }
        )


# Batch document upload endpoints
@router.post("/batch/upload",
    response_model=BatchUploadResponse,
    summary="Upload multiple documents as a batch",
    description="Upload multiple medical documents for batch processing"
)
async def upload_document_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="List of document files to upload"),
    batch_name: Optional[str] = Form(None, description="Optional name for the batch"),
    metadata: Optional[str] = Form(None, description="Optional JSON metadata for the batch"),
    service: DocumentService = Depends(get_document_service)
):
    """
    Upload multiple documents for batch processing.
    
    Supported file types per document:
    - PDF: Clinical reports, lab results, discharge summaries
    - DOCX: Medical notes, consultation reports
    - TXT: Plain text clinical notes
    - RTF: Formatted medical documents
    - HL7: Health Level 7 messages
    
    The batch will be created and documents will be queued for processing.
    Use the status endpoint to monitor progress.
    """
    try:
        # Validate file count
        if len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail="No files provided"
            )
        
        if len(files) > 50:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail="Batch size limited to 50 documents"
            )
        
        # Parse metadata if provided
        parsed_metadata = None
        if metadata:
            try:
                import json
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid metadata format. Must be valid JSON"
                )
        
        # Create batch in database
        batch_id = service.create_document_batch(
            batch_name=batch_name,
            metadata=parsed_metadata,
            total_documents=len(files)
        )
        
        # Process each file
        document_ids = []
        for file in files:
            try:
                # Determine document type from extension
                file_ext = file.filename.split('.')[-1].lower()
                document_type = None
                for dt in DocumentType:
                    if dt.value == file_ext:
                        document_type = dt
                        break
                
                if not document_type:
                    # Skip unsupported files
                    logger.warning(f"Skipping unsupported file type: {file.filename}")
                    continue
                
                # Read file content
                content = await file.read()
                
                # Save document with batch association
                response = await service.save_document(
                    content=content,
                    filename=file.filename,
                    document_type=document_type,
                    metadata={"batch_id": str(batch_id)},
                    batch_id=batch_id
                )
                
                document_ids.append(response.document_id)
                
            except Exception as e:
                logger.error(f"Failed to upload file {file.filename}: {e}")
                # Continue with other files
        
        # Queue batch for processing
        if document_ids:
            try:
                from app.processing.document_processor import queue_batch_processing
                task_id = queue_batch_processing(str(batch_id), [str(id) for id in document_ids])
                logger.info(f"Batch {batch_id} queued for processing with task ID: {task_id}")
            except Exception as e:
                logger.warning(f"Failed to queue batch for processing: {e}")
        
        return BatchUploadResponse(
            batch_id=batch_id,
            status=BatchUploadStatus.PENDING,
            total_documents=len(document_ids),
            batch_name=batch_name,
            created_at=datetime.utcnow(),
            status_url=f"/api/v1/documents/batch/{batch_id}/status"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create document batch: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create batch: {str(e)}"
        )


@router.get("/batch/{batch_id}/status",
    response_model=BatchProcessingStatus,
    summary="Get batch processing status",
    description="Get the current status of a document batch"
)
async def get_batch_status(
    batch_id: UUID,
    service: DocumentService = Depends(get_document_service)
):
    """
    Get detailed status of a document batch including:
    - Overall batch status
    - Progress percentage
    - Individual document statuses
    - Error information for failed documents
    """
    try:
        batch_status = service.get_batch_status(batch_id)
        
        if not batch_status:
            raise HTTPException(
                status_code=404,
                detail=f"Batch with ID {batch_id} not found"
            )
        
        return batch_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch status: {str(e)}"
        )


@router.get("/batch/{batch_id}/results",
    response_model=BatchResultsSummary,
    summary="Get batch processing results summary",
    description="Get aggregated results for a completed batch"
)
async def get_batch_results(
    batch_id: UUID,
    service: DocumentService = Depends(get_document_service)
):
    """
    Get summary of batch processing results including:
    - Total entities extracted across all documents
    - Entity type distribution
    - Terminology mapping statistics
    - Processing time and performance metrics
    """
    try:
        results = service.get_batch_results_summary(batch_id)
        
        if not results:
            # Check if batch exists
            batch_status = service.get_batch_status(batch_id)
            if not batch_status:
                raise HTTPException(
                    status_code=404,
                    detail=f"Batch with ID {batch_id} not found"
                )
            
            if batch_status.status not in [BatchUploadStatus.COMPLETED, BatchUploadStatus.PARTIALLY_COMPLETED]:
                raise HTTPException(
                    status_code=422,
                    detail=f"Batch processing not complete. Current status: {batch_status.status}"
                )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch results: {str(e)}"
        )


@router.get("/batch/{batch_id}/export/{format}",
    summary="Export batch results",
    description="Export batch processing results in specified format"
)
async def export_batch_results(
    batch_id: UUID,
    format: BatchExportFormat,
    include_failed: bool = Query(False, description="Include failed documents"),
    include_raw_text: bool = Query(False, description="Include extracted text"),
    include_terminology_mappings: bool = Query(True, description="Include terminology mappings"),
    service: DocumentService = Depends(get_document_service)
):
    """
    Export batch processing results in various formats:
    - JSON: Complete structured data
    - CSV: Flattened entity data
    - Excel: Multi-sheet workbook with entities and mappings
    - FHIR: FHIR Bundle format (if applicable)
    """
    try:
        export_path = service.export_batch_results(
            batch_id=batch_id,
            format=format,
            include_failed=include_failed,
            include_raw_text=include_raw_text,
            include_terminology_mappings=include_terminology_mappings
        )
        
        if not export_path:
            raise HTTPException(
                status_code=404,
                detail=f"No results to export for batch {batch_id}"
            )
        
        from fastapi.responses import FileResponse
        
        media_type_map = {
            BatchExportFormat.JSON: "application/json",
            BatchExportFormat.CSV: "text/csv",
            BatchExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            BatchExportFormat.FHIR: "application/fhir+json"
        }
        
        return FileResponse(
            path=export_path,
            filename=f"batch_{batch_id}_results.{format}",
            media_type=media_type_map.get(format, "application/octet-stream")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export batch results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export results: {str(e)}"
        )