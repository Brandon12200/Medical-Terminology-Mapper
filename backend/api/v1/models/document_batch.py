"""
Document batch upload and processing models
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from .document import DocumentType, DocumentStatus, DocumentUploadResponse


class BatchUploadStatus(str, Enum):
    """Batch upload processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class BatchDocumentItem(BaseModel):
    """Individual document in a batch"""
    document_id: UUID
    filename: str
    document_type: DocumentType
    status: DocumentStatus
    file_size: int
    error_message: Optional[str] = None
    processing_time: Optional[float] = None  # in seconds


class BatchUploadRequest(BaseModel):
    """Request model for batch document upload"""
    batch_name: Optional[str] = Field(
        None,
        description="Optional name for the batch"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata for the batch"
    )
    process_async: bool = Field(
        default=True,
        description="Whether to process documents asynchronously"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "batch_name": "Clinical Reports Q1 2024",
                "metadata": {
                    "department": "cardiology",
                    "upload_source": "EHR_EXPORT"
                },
                "process_async": True
            }
        }
    )


class BatchUploadResponse(BaseModel):
    """Response model for batch document upload"""
    batch_id: UUID = Field(..., description="Unique batch identifier")
    status: BatchUploadStatus
    total_documents: int
    batch_name: Optional[str] = None
    created_at: datetime
    status_url: str = Field(..., description="URL to check batch status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "batch_id": "456e7890-e89b-12d3-a456-426614174000",
                "status": "pending",
                "total_documents": 25,
                "batch_name": "Clinical Reports Q1 2024",
                "created_at": "2024-01-01T10:00:00Z",
                "status_url": "/api/v1/documents/batch/456e7890-e89b-12d3-a456-426614174000/status"
            }
        }
    )


class BatchProcessingStatus(BaseModel):
    """Status of batch document processing"""
    batch_id: UUID
    status: BatchUploadStatus
    total_documents: int
    processed_documents: int
    successful_documents: int
    failed_documents: int
    progress_percentage: float = Field(..., ge=0, le=100)
    current_document: Optional[str] = Field(None, description="Currently processing document")
    documents: List[BatchDocumentItem] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "batch_id": "456e7890-e89b-12d3-a456-426614174000",
                "status": "processing",
                "total_documents": 25,
                "processed_documents": 15,
                "successful_documents": 14,
                "failed_documents": 1,
                "progress_percentage": 60.0,
                "current_document": "report_16.pdf",
                "started_at": "2024-01-01T10:00:00Z",
                "estimated_completion": "2024-01-01T10:15:00Z"
            }
        }
    )


class BatchResultsSummary(BaseModel):
    """Summary of batch processing results"""
    batch_id: UUID
    batch_name: Optional[str]
    status: BatchUploadStatus
    total_documents: int
    successful_documents: int
    failed_documents: int
    total_entities_extracted: int
    entities_by_type: Dict[str, int]
    terminology_mappings: Dict[str, int]  # system -> count
    processing_time: float  # total time in seconds
    started_at: datetime
    completed_at: datetime
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "batch_id": "456e7890-e89b-12d3-a456-426614174000",
                "batch_name": "Clinical Reports Q1 2024",
                "status": "completed",
                "total_documents": 25,
                "successful_documents": 24,
                "failed_documents": 1,
                "total_entities_extracted": 1250,
                "entities_by_type": {
                    "CONDITION": 450,
                    "MEDICATION": 380,
                    "PROCEDURE": 220,
                    "LAB_TEST": 200
                },
                "terminology_mappings": {
                    "snomed": 670,
                    "rxnorm": 380,
                    "loinc": 200
                },
                "processing_time": 450.5,
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:07:30Z"
            }
        }
    )


class BatchExportFormat(str, Enum):
    """Supported export formats for batch results"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "xlsx"
    FHIR = "fhir"  # FHIR Bundle format


class BatchExportRequest(BaseModel):
    """Request model for exporting batch results"""
    format: BatchExportFormat = Field(..., description="Export format")
    include_failed: bool = Field(
        default=False,
        description="Include failed documents in export"
    )
    include_raw_text: bool = Field(
        default=False,
        description="Include extracted text in export"
    )
    include_terminology_mappings: bool = Field(
        default=True,
        description="Include terminology mappings"
    )