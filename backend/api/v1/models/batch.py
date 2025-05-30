from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
from datetime import datetime

class BatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"

class FileFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    TXT = "txt"

class BatchJobRequest(BaseModel):
    job_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_format: FileFormat
    column_name: Optional[str] = Field(
        default="term",
        description="Column name containing terms (for CSV/Excel)"
    )
    systems: Optional[List[str]] = Field(default=["all"])
    context: Optional[str] = None
    fuzzy_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    fuzzy_algorithms: Optional[List[str]] = Field(default=["all"])
    max_results_per_term: Optional[int] = Field(default=5, ge=1, le=50)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "medical_terms.csv",
                "file_format": "csv",
                "column_name": "term",
                "systems": ["snomed", "loinc"],
                "fuzzy_threshold": 0.8,
                "max_results_per_term": 3
            }
        }
    )

class BatchJobStatus(BaseModel):
    job_id: str
    status: BatchStatus
    created_at: datetime
    updated_at: datetime
    total_terms: int
    processed_terms: int
    successful_mappings: int
    failed_mappings: int
    progress_percentage: float
    error_message: Optional[str] = None
    result_url: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:05:00Z",
                "total_terms": 100,
                "processed_terms": 45,
                "successful_mappings": 40,
                "failed_mappings": 5,
                "progress_percentage": 45.0
            }
        }
    )

class BatchJobResult(BaseModel):
    job_id: str
    status: BatchStatus
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    download_formats: Dict[str, str]  # format -> download URL
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "results": [
                    {
                        "original_term": "diabetes type 2",
                        "mappings": {
                            "snomed": [
                                {
                                    "code": "44054006",
                                    "display": "Diabetes mellitus type 2",
                                    "confidence": 0.95
                                }
                            ]
                        }
                    }
                ],
                "summary": {
                    "total_terms": 100,
                    "successful_mappings": 95,
                    "failed_mappings": 5,
                    "processing_time_seconds": 15.5
                },
                "download_formats": {
                    "csv": "/api/v1/batch/download/123e4567-e89b-12d3-a456-426614174000.csv",
                    "json": "/api/v1/batch/download/123e4567-e89b-12d3-a456-426614174000.json"
                }
            }
        }
    )