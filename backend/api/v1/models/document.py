"""
Document upload and processing models for API v1
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class DocumentType(str, Enum):
    """Supported document types for upload"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    RTF = "rtf"
    HL7 = "hl7"


class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    filename: str = Field(..., description="Original filename")
    document_type: DocumentType = Field(..., description="Type of document")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata for the document"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "clinical_notes.pdf",
                "document_type": "pdf",
                "metadata": {
                    "patient_id": "12345",
                    "encounter_date": "2024-01-01"
                }
            }
        }
    )


class DocumentMetadata(BaseModel):
    """Document metadata model"""
    filename: str
    document_type: DocumentType
    file_size: int = Field(..., description="File size in bytes")
    upload_timestamp: datetime
    mime_type: str
    page_count: Optional[int] = Field(None, description="Number of pages (if applicable)")
    encoding: Optional[str] = Field(None, description="Text encoding")
    checksum: str = Field(..., description="SHA-256 checksum of the file")
    metadata: Optional[Dict[str, Any]] = None


class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    document_id: UUID = Field(..., description="Unique document identifier")
    status: DocumentStatus
    filename: str
    document_type: DocumentType
    file_size: int
    upload_timestamp: datetime
    processing_url: str = Field(..., description="URL to check processing status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "filename": "clinical_notes.pdf",
                "document_type": "pdf",
                "file_size": 102400,
                "upload_timestamp": "2024-01-01T10:00:00Z",
                "processing_url": "/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/status"
            }
        }
    )


class DocumentProcessingStatus(BaseModel):
    """Status of document processing"""
    document_id: UUID
    status: DocumentStatus
    progress: float = Field(..., ge=0, le=100, description="Processing progress percentage")
    current_step: Optional[str] = Field(None, description="Current processing step")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing",
                "progress": 45.5,
                "current_step": "Extracting text from PDF",
                "started_at": "2024-01-01T10:00:00Z"
            }
        }
    )


class ExtractedText(BaseModel):
    """Extracted text from document"""
    document_id: UUID
    text_content: str = Field(..., description="Extracted text content")
    sections: Optional[Dict[str, str]] = Field(
        None, 
        description="Text divided by sections (if detected)"
    )
    metadata: DocumentMetadata
    extraction_timestamp: datetime
    extraction_method: str = Field(..., description="Method used for extraction")
    

class DocumentListResponse(BaseModel):
    """Response for listing documents"""
    documents: List[DocumentUploadResponse]
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documents": [
                    {
                        "document_id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "completed",
                        "filename": "clinical_notes.pdf",
                        "document_type": "pdf",
                        "file_size": 102400,
                        "upload_timestamp": "2024-01-01T10:00:00Z",
                        "processing_url": "/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/status"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
        }
    )


class DocumentDeleteResponse(BaseModel):
    """Response for document deletion"""
    document_id: UUID
    message: str = Field(default="Document deleted successfully")
    deleted_at: datetime