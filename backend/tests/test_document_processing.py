"""
Tests for document processing pipeline
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
import pytest

from api.v1.models.document import DocumentStatus, DocumentType
from app.processing.document_processor import (
    DocumentProcessingTask, process_document, extract_document_text,
    queue_document_processing
)


class TestDocumentProcessor:
    """Test document processing tasks"""
    
    @pytest.fixture
    def mock_document_service(self):
        """Mock document service"""
        service = Mock()
        service._get_db = Mock()
        return service
    
    @pytest.fixture
    def mock_text_extractor(self):
        """Mock text extractor"""
        extractor = Mock()
        extractor.extract_text = Mock(return_value=(
            "Extracted text content",
            "test_method",
            {"page_count": 1}
        ))
        extractor.get_text_preview = Mock(return_value="Preview text...")
        return extractor
    
    @pytest.fixture
    def processing_task(self, mock_document_service, mock_text_extractor):
        """Create a document processing task with mocks"""
        task = DocumentProcessingTask()
        task._document_service = mock_document_service
        task._text_extractor = mock_text_extractor
        return task
    
    def test_process_document_success(self, processing_task, mock_document_service):
        """Test successful document processing"""
        document_id = str(uuid4())
        
        # Mock database responses
        mock_conn = MagicMock()
        mock_document_service._get_db.return_value.__enter__.return_value = mock_conn
        
        # Mock document info
        mock_conn.execute.return_value.fetchone.return_value = {
            'document_id': document_id,
            'filename': 'test.txt',
            'document_type': 'txt',
            'file_path': '/tmp/test.txt',
            'status': 'pending'
        }
        
        # Create the task instance and bind it
        task = process_document
        task._document_service = processing_task._document_service
        task._text_extractor = processing_task._text_extractor
        
        # Run the task
        result = task.run(document_id)
        
        # Verify result
        assert result['status'] == 'completed'
        assert result['document_id'] == document_id
        assert result['extraction_method'] == 'test_method'
        assert result['word_count'] == 3
        assert 'preview' in result
    
    def test_process_document_extraction_failure(self, processing_task, mock_document_service):
        """Test document processing when extraction fails"""
        document_id = str(uuid4())
        
        # Mock database responses
        mock_conn = MagicMock()
        mock_document_service._get_db.return_value.__enter__.return_value = mock_conn
        
        # Mock document info
        mock_conn.execute.return_value.fetchone.return_value = {
            'document_id': document_id,
            'filename': 'test.pdf',
            'document_type': 'pdf',
            'file_path': '/tmp/test.pdf',
            'status': 'pending'
        }
        
        # Make extraction fail
        processing_task._text_extractor.extract_text.return_value = (
            None,
            "error",
            {"error": "Extraction failed"}
        )
        
        # Create the task instance
        task = process_document
        task._document_service = processing_task._document_service
        task._text_extractor = processing_task._text_extractor
        task.retry = Mock(side_effect=Exception("Retry called"))
        
        # Run the task and expect retry
        with pytest.raises(Exception, match="Retry called"):
            task.run(document_id)
    
    def test_process_document_not_found(self, processing_task, mock_document_service):
        """Test processing non-existent document"""
        document_id = str(uuid4())
        
        # Mock database to return None
        mock_conn = MagicMock()
        mock_document_service._get_db.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = None
        
        # Create the task instance
        task = process_document
        task._document_service = processing_task._document_service
        task.retry = Mock(side_effect=Exception("Retry called"))
        
        # Run the task and expect retry
        with pytest.raises(Exception, match="Retry called"):
            task.run(document_id)
    
    def test_update_document_status(self, processing_task, mock_document_service):
        """Test updating document status"""
        document_id = str(uuid4())
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_document_service._get_db.return_value.__enter__.return_value = mock_conn
        
        # Update status
        processing_task._update_document_status(
            document_id,
            DocumentStatus.PROCESSING,
            started_at=datetime.utcnow()
        )
        
        # Verify SQL was executed
        mock_conn.execute.assert_called_once()
        sql_query = mock_conn.execute.call_args[0][0]
        assert "UPDATE documents SET" in sql_query
        assert "status = ?" in sql_query
        assert "started_at = ?" in sql_query
    
    def test_store_extracted_text(self, processing_task, mock_document_service):
        """Test storing extracted text"""
        document_id = str(uuid4())
        extracted_text = "This is the extracted text content."
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_document_service._get_db.return_value.__enter__.return_value = mock_conn
        
        # Mock existing metadata
        mock_conn.execute.return_value.fetchone.return_value = {
            'metadata': '{"existing": "data"}'
        }
        
        # Store text
        result = processing_task._store_extracted_text(
            document_id,
            extracted_text,
            "test_method",
            {"page_count": 5}
        )
        
        assert result is True
        # Verify two SQL executions (update text and update metadata)
        assert mock_conn.execute.call_count >= 2
    
    def test_extract_document_text_task(self, processing_task, mock_document_service):
        """Test simple text extraction task"""
        document_id = str(uuid4())
        
        # Mock database response
        mock_conn = MagicMock()
        mock_document_service._get_db.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = {
            'document_id': document_id,
            'filename': 'test.txt',
            'document_type': 'txt',
            'file_path': '/tmp/test.txt',
            'status': 'completed'
        }
        
        # Create task and run
        task = extract_document_text
        task._document_service = processing_task._document_service
        task._text_extractor = processing_task._text_extractor
        
        result = task.run(document_id)
        
        assert result == "Extracted text content"
    
    @patch('app.processing.document_processor.process_document.apply_async')
    def test_queue_document_processing(self, mock_apply_async):
        """Test queueing document for processing"""
        document_id = str(uuid4())
        mock_apply_async.return_value.id = "task-123"
        
        # Queue without delay
        task_id = queue_document_processing(document_id)
        
        assert task_id == "task-123"
        mock_apply_async.assert_called_once_with(args=[document_id])
        
        # Queue with delay
        mock_apply_async.reset_mock()
        task_id = queue_document_processing(document_id, delay=60)
        
        mock_apply_async.assert_called_once_with(args=[document_id], countdown=60)


class TestDocumentProcessingIntegration:
    """Integration tests for document processing"""
    
    @pytest.mark.integration
    def test_celery_app_configuration(self):
        """Test Celery app is properly configured"""
        from celery_config import celery_app
        
        # Check task routes
        assert 'app.processing.document_processor.process_document' in celery_app.conf.task_routes
        
        # Check queues
        queue_names = [q.name for q in celery_app.conf.task_queues]
        assert 'document_processing' in queue_names
        assert 'default' in queue_names
        
        # Check serialization settings
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.result_serializer == 'json'
    
    @pytest.mark.integration
    def test_task_registration(self):
        """Test that tasks are properly registered"""
        from celery_config import celery_app
        
        # Check tasks are registered
        assert 'app.processing.document_processor.process_document' in celery_app.tasks
        assert 'app.processing.document_processor.extract_document_text' in celery_app.tasks
        assert 'app.processing.document_processor.cleanup_old_results' in celery_app.tasks