"""
Test Batch Document Upload Functionality

This test verifies the batch document upload and processing capabilities.
"""

import pytest
import asyncio
from uuid import UUID
from datetime import datetime
from pathlib import Path
import tempfile
import json

from api.v1.models.document import DocumentType, DocumentStatus
from api.v1.models.document_batch import (
    BatchUploadStatus, BatchProcessingStatus, 
    BatchResultsSummary, BatchExportFormat
)
from api.v1.services.document_service import DocumentService
from app.processing.document_processor import queue_batch_processing


@pytest.fixture
def document_service():
    """Create a test document service"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = DocumentService(
            upload_dir=temp_dir,
            db_path=f"{temp_dir}/test_documents.db"
        )
        yield service


@pytest.fixture
def sample_documents():
    """Create sample test documents"""
    documents = [
        {
            "filename": "test_report1.txt",
            "content": b"Patient presents with diabetes mellitus type 2. Current medications include metformin 500mg.",
            "type": DocumentType.TXT
        },
        {
            "filename": "test_report2.txt", 
            "content": b"Lab results show elevated glucose levels. HbA1c is 8.5%. Recommend insulin therapy.",
            "type": DocumentType.TXT
        },
        {
            "filename": "test_report3.txt",
            "content": b"Follow-up visit: Blood pressure 140/90. Started on lisinopril 10mg daily.",
            "type": DocumentType.TXT
        }
    ]
    return documents


async def test_batch_creation(document_service):
    """Test creating a document batch"""
    
    # Create a batch
    batch_id = document_service.create_document_batch(
        batch_name="Test Batch Q1 2024",
        metadata={"department": "cardiology"},
        total_documents=3
    )
    
    assert isinstance(batch_id, UUID)
    
    # Verify batch was created
    batch_status = document_service.get_batch_status(batch_id)
    assert batch_status is not None
    assert batch_status.status == BatchUploadStatus.PENDING
    assert batch_status.total_documents == 3
    assert batch_status.processed_documents == 0


async def test_batch_document_upload(document_service, sample_documents):
    """Test uploading multiple documents as a batch"""
    
    # Create batch
    batch_id = document_service.create_document_batch(
        batch_name="Test Medical Reports",
        metadata={"source": "test_suite"},
        total_documents=len(sample_documents)
    )
    
    # Upload documents
    document_ids = []
    for doc in sample_documents:
        response = await document_service.save_document(
            content=doc["content"],
            filename=doc["filename"],
            document_type=doc["type"],
            batch_id=batch_id
        )
        document_ids.append(response.document_id)
    
    assert len(document_ids) == 3
    
    # Check batch status
    batch_status = document_service.get_batch_status(batch_id)
    assert batch_status.total_documents == 3
    assert len(batch_status.documents) == 3
    
    # Verify all documents are associated with the batch
    for doc_item in batch_status.documents:
        assert doc_item.document_id in document_ids
        assert doc_item.status == DocumentStatus.PENDING


async def test_batch_progress_tracking(document_service, sample_documents):
    """Test batch processing progress tracking"""
    
    # Create and upload batch
    batch_id = document_service.create_document_batch(
        batch_name="Progress Test Batch",
        metadata={},
        total_documents=len(sample_documents)
    )
    
    document_ids = []
    for doc in sample_documents:
        response = await document_service.save_document(
            content=doc["content"],
            filename=doc["filename"],
            document_type=doc["type"],
            batch_id=batch_id
        )
        document_ids.append(str(response.document_id))
    
    # Simulate processing (in real scenario, Celery would handle this)
    # For testing, we'll manually update document statuses
    with document_service._get_db() as conn:
        # Mark first document as completed
        conn.execute("""
            UPDATE documents 
            SET status = ?, completed_at = ?
            WHERE document_id = ?
        """, (DocumentStatus.COMPLETED.value, datetime.utcnow().isoformat(), document_ids[0]))
        
        # Mark second document as processing
        conn.execute("""
            UPDATE documents 
            SET status = ?, started_at = ?
            WHERE document_id = ?
        """, (DocumentStatus.PROCESSING.value, datetime.utcnow().isoformat(), document_ids[1]))
    
    # Check batch progress
    batch_status = document_service.get_batch_status(batch_id)
    assert batch_status.processed_documents == 1  # Only completed docs count as processed
    assert batch_status.successful_documents == 1
    assert batch_status.failed_documents == 0
    assert batch_status.progress_percentage == pytest.approx(33.33, rel=0.1)


async def test_batch_results_aggregation(document_service):
    """Test batch results summary generation"""
    
    # Create a completed batch
    batch_id = document_service.create_document_batch(
        batch_name="Completed Batch",
        metadata={},
        total_documents=2
    )
    
    # Mark batch as completed with some mock data
    with document_service._get_db() as conn:
        conn.execute("""
            UPDATE document_batches
            SET status = ?, successful_documents = ?, failed_documents = ?,
                started_at = ?, completed_at = ?
            WHERE batch_id = ?
        """, (
            BatchUploadStatus.COMPLETED.value,
            2, 0,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
            str(batch_id)
        ))
    
    # Get results summary
    results = document_service.get_batch_results_summary(batch_id)
    assert results is not None
    assert results.status == BatchUploadStatus.COMPLETED
    assert results.successful_documents == 2
    assert results.failed_documents == 0
    assert results.processing_time >= 0


async def test_batch_export(document_service, sample_documents):
    """Test exporting batch results"""
    
    # Create batch with documents
    batch_id = document_service.create_document_batch(
        batch_name="Export Test",
        metadata={},
        total_documents=len(sample_documents)
    )
    
    # Add documents
    for doc in sample_documents:
        await document_service.save_document(
            content=doc["content"],
            filename=doc["filename"],
            document_type=doc["type"],
            batch_id=batch_id
        )
    
    # Mark all as completed for export test
    with document_service._get_db() as conn:
        conn.execute("""
            UPDATE documents 
            SET status = ?, extracted_text = ?
            WHERE batch_id = ?
        """, (DocumentStatus.COMPLETED.value, "Test extracted text", str(batch_id)))
    
    # Test JSON export
    export_path = document_service.export_batch_results(
        batch_id=batch_id,
        format=BatchExportFormat.JSON,
        include_raw_text=True
    )
    
    assert export_path is not None
    assert Path(export_path).exists()
    
    # Verify export content
    with open(export_path, 'r') as f:
        export_data = json.load(f)
    
    assert export_data["batch_id"] == str(batch_id)
    assert len(export_data["documents"]) == 3
    assert all("extracted_text" in doc for doc in export_data["documents"])
    
    # Clean up
    Path(export_path).unlink()


def test_batch_status_updates(document_service):
    """Test various batch status transitions"""
    
    # Create batch
    batch_id = document_service.create_document_batch(
        batch_name="Status Test",
        metadata={},
        total_documents=1
    )
    
    # Test status transitions
    statuses_to_test = [
        BatchUploadStatus.PROCESSING,
        BatchUploadStatus.COMPLETED,
        BatchUploadStatus.PARTIALLY_COMPLETED,
        BatchUploadStatus.FAILED
    ]
    
    for status in statuses_to_test:
        with document_service._get_db() as conn:
            conn.execute("""
                UPDATE document_batches
                SET status = ?
                WHERE batch_id = ?
            """, (status.value, str(batch_id)))
        
        batch_status = document_service.get_batch_status(batch_id)
        assert batch_status.status == status.value


if __name__ == "__main__":
    # Run tests
    print("Testing Batch Document Upload...")
    
    async def run_tests():
        service = DocumentService(
            upload_dir="test_uploads",
            db_path="test_documents.db"
        )
        
        print("\n1. Testing batch creation...")
        await test_batch_creation(service)
        print("✓ Batch creation test passed")
        
        print("\n2. Testing batch document upload...")
        docs = [
            {
                "filename": f"test{i}.txt",
                "content": f"Test content {i}".encode(),
                "type": DocumentType.TXT
            }
            for i in range(3)
        ]
        await test_batch_document_upload(service, docs)
        print("✓ Batch upload test passed")
        
        print("\n3. Testing progress tracking...")
        await test_batch_progress_tracking(service, docs)
        print("✓ Progress tracking test passed")
        
        print("\n4. Testing results aggregation...")
        await test_batch_results_aggregation(service)
        print("✓ Results aggregation test passed")
        
        print("\n5. Testing batch export...")
        await test_batch_export(service, docs)
        print("✓ Batch export test passed")
        
        print("\nAll tests completed successfully!")
    
    asyncio.run(run_tests())