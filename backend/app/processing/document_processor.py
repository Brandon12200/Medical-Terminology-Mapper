"""
Background document processing tasks using Celery
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from celery import Task
from celery.utils.log import get_task_logger

from celery_config import celery_app
from app.processing.text_extractor import TextExtractor
from api.v1.services.document_service import DocumentService
from api.v1.models.document import DocumentStatus

logger = get_task_logger(__name__)


class DocumentProcessingTask(Task):
    """Base task class with document service initialization"""
    _document_service = None
    _text_extractor = None
    
    @property
    def document_service(self):
        if self._document_service is None:
            self._document_service = DocumentService()
        return self._document_service
    
    @property
    def text_extractor(self):
        if self._text_extractor is None:
            self._text_extractor = TextExtractor()
        return self._text_extractor


@celery_app.task(bind=True, base=DocumentProcessingTask, name='app.processing.document_processor.process_document')
def process_document(self, document_id: str) -> Dict[str, Any]:
    """
    Process a document by extracting its text content
    
    Args:
        document_id: UUID of the document to process
        
    Returns:
        Dict with processing results
    """
    logger.info(f"Starting document processing for {document_id}")
    
    try:
        # Update status to processing
        self._update_document_status(
            document_id,
            DocumentStatus.PROCESSING,
            started_at=datetime.utcnow()
        )
        
        # Get document information
        document_info = self._get_document_info(document_id)
        if not document_info:
            raise ValueError(f"Document {document_id} not found")
        
        # Extract text
        logger.info(f"Extracting text from {document_info['filename']} ({document_info['document_type']})")
        
        extracted_text, extraction_method, metadata = self.text_extractor.extract_text(
            file_path=document_info['file_path'],
            document_type=document_info['document_type']
        )
        
        if extracted_text is None:
            error_msg = metadata.get('error', 'Unknown error during text extraction')
            raise Exception(f"Text extraction failed: {error_msg}")
        
        # Store extracted text
        success = self._store_extracted_text(
            document_id,
            extracted_text,
            extraction_method,
            metadata
        )
        
        if not success:
            raise Exception("Failed to store extracted text")
        
        # Update status to completed
        self._update_document_status(
            document_id,
            DocumentStatus.COMPLETED,
            completed_at=datetime.utcnow()
        )
        
        # Calculate processing statistics
        word_count = len(extracted_text.split())
        char_count = len(extracted_text)
        
        result = {
            'status': 'completed',
            'document_id': document_id,
            'extraction_method': extraction_method,
            'text_length': char_count,
            'word_count': word_count,
            'metadata': metadata,
            'preview': self.text_extractor.get_text_preview(extracted_text, 200)
        }
        
        logger.info(f"Document processing completed for {document_id}: {word_count} words extracted")
        return result
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        
        # Update status to failed
        self._update_document_status(
            document_id,
            DocumentStatus.FAILED,
            error_message=str(e),
            completed_at=datetime.utcnow()
        )
        
        # Re-raise for Celery retry mechanism
        raise self.retry(exc=e)
    
    def _get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document information from database"""
        try:
            with self.document_service._get_db() as conn:
                row = conn.execute(
                    """
                    SELECT document_id, filename, document_type, file_path, status
                    FROM documents WHERE document_id = ?
                    """,
                    (document_id,)
                ).fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error getting document info: {e}")
            return None
    
    def _update_document_status(
        self,
        document_id: str,
        status: DocumentStatus,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None
    ):
        """Update document processing status"""
        try:
            with self.document_service._get_db() as conn:
                # Build update query
                updates = ["status = ?", "updated_at = ?"]
                params = [status.value, datetime.utcnow().isoformat()]
                
                if started_at:
                    updates.append("started_at = ?")
                    params.append(started_at.isoformat())
                
                if completed_at:
                    updates.append("completed_at = ?")
                    params.append(completed_at.isoformat())
                
                if error_message:
                    updates.append("error_message = ?")
                    params.append(error_message)
                
                params.append(document_id)
                
                query = f"UPDATE documents SET {', '.join(updates)} WHERE document_id = ?"
                conn.execute(query, params)
                
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
    
    def _store_extracted_text(
        self,
        document_id: str,
        extracted_text: str,
        extraction_method: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Store extracted text in database"""
        try:
            import json
            
            with self.document_service._get_db() as conn:
                # Update document with extracted text
                conn.execute(
                    """
                    UPDATE documents 
                    SET extracted_text = ?, 
                        extraction_method = ?,
                        page_count = ?,
                        updated_at = ?
                    WHERE document_id = ?
                    """,
                    (
                        extracted_text,
                        extraction_method,
                        metadata.get('page_count'),
                        datetime.utcnow().isoformat(),
                        document_id
                    )
                )
                
                # Store additional metadata if present
                if metadata:
                    existing_metadata = conn.execute(
                        "SELECT metadata FROM documents WHERE document_id = ?",
                        (document_id,)
                    ).fetchone()
                    
                    if existing_metadata and existing_metadata['metadata']:
                        current_metadata = json.loads(existing_metadata['metadata'])
                        current_metadata['extraction_metadata'] = metadata
                    else:
                        current_metadata = {'extraction_metadata': metadata}
                    
                    conn.execute(
                        "UPDATE documents SET metadata = ? WHERE document_id = ?",
                        (json.dumps(current_metadata), document_id)
                    )
                
                return True
                
        except Exception as e:
            logger.error(f"Error storing extracted text: {e}")
            return False


@celery_app.task(bind=True, base=DocumentProcessingTask, name='app.processing.document_processor.extract_document_text')
def extract_document_text(self, document_id: str) -> str:
    """
    Extract text from a document (simpler version for direct calls)
    
    Args:
        document_id: UUID of the document
        
    Returns:
        Extracted text content
    """
    try:
        document_info = self._get_document_info(document_id)
        if not document_info:
            raise ValueError(f"Document {document_id} not found")
        
        extracted_text, _, _ = self.text_extractor.extract_text(
            file_path=document_info['file_path'],
            document_type=document_info['document_type']
        )
        
        return extracted_text or ""
        
    except Exception as e:
        logger.error(f"Error extracting text from document {document_id}: {e}")
        raise


@celery_app.task(name='app.processing.document_processor.cleanup_old_results')
def cleanup_old_results():
    """
    Periodic task to clean up old processing results
    """
    try:
        service = DocumentService()
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        with service._get_db() as conn:
            # Find old failed documents
            old_failed = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM documents 
                WHERE status = ? AND updated_at < ?
                """,
                (DocumentStatus.FAILED.value, cutoff_date.isoformat())
            ).fetchone()
            
            if old_failed and old_failed['count'] > 0:
                logger.info(f"Found {old_failed['count']} old failed documents to clean up")
                
                # You could delete or archive these documents
                # For now, just log the information
                
        logger.info("Cleanup task completed")
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")


# Helper function to queue document for processing
def queue_document_processing(document_id: str, delay: Optional[int] = None) -> str:
    """
    Queue a document for processing
    
    Args:
        document_id: UUID of the document
        delay: Optional delay in seconds before processing
        
    Returns:
        Task ID
    """
    if delay:
        task = process_document.apply_async(
            args=[document_id],
            countdown=delay
        )
    else:
        task = process_document.apply_async(args=[document_id])
    
    return task.id


@celery_app.task(bind=True, base=DocumentProcessingTask, name='app.processing.document_processor.process_batch')
def process_batch(self, batch_id: str, document_ids: list[str]) -> Dict[str, Any]:
    """
    Process a batch of documents
    
    Args:
        batch_id: UUID of the batch
        document_ids: List of document UUIDs in the batch
        
    Returns:
        Dict with batch processing results
    """
    logger.info(f"Starting batch processing for {batch_id} with {len(document_ids)} documents")
    
    try:
        # Update batch status to processing
        self._update_batch_status(batch_id, 'processing', started_at=datetime.utcnow())
        
        # Process each document
        successful = 0
        failed = 0
        results = []
        
        for idx, doc_id in enumerate(document_ids):
            try:
                # Update batch progress
                progress = (idx / len(document_ids)) * 100
                self._update_batch_progress(batch_id, progress, current_document=doc_id)
                
                # Process the document
                result = process_document.apply_async(args=[doc_id]).get(timeout=300)  # 5 min timeout
                
                if result.get('status') == 'completed':
                    successful += 1
                else:
                    failed += 1
                    
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to process document {doc_id} in batch {batch_id}: {e}")
                failed += 1
                results.append({
                    'status': 'failed',
                    'document_id': doc_id,
                    'error': str(e)
                })
        
        # Update batch status to completed
        status = 'completed' if failed == 0 else 'partially_completed'
        self._update_batch_status(
            batch_id, 
            status,
            completed_at=datetime.utcnow(),
            successful_documents=successful,
            failed_documents=failed
        )
        
        return {
            'batch_id': batch_id,
            'status': status,
            'total_documents': len(document_ids),
            'successful_documents': successful,
            'failed_documents': failed,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error processing batch {batch_id}: {e}")
        self._update_batch_status(batch_id, 'failed', error_message=str(e))
        raise
        

def _update_batch_status(self, batch_id: str, status: str, **kwargs):
    """Update batch status in database"""
    try:
        with self.document_service._get_db() as conn:
            # Update batch status
            update_fields = ['status = ?']
            update_values = [status]
            
            for field, value in kwargs.items():
                if value is not None:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value.isoformat() if isinstance(value, datetime) else value)
            
            update_fields.append('updated_at = ?')
            update_values.append(datetime.utcnow().isoformat())
            update_values.append(batch_id)
            
            conn.execute(
                f"UPDATE document_batches SET {', '.join(update_fields)} WHERE batch_id = ?",
                update_values
            )
    except Exception as e:
        logger.error(f"Error updating batch status: {e}")


def _update_batch_progress(self, batch_id: str, progress: float, current_document: Optional[str] = None):
    """Update batch processing progress"""
    try:
        with self.document_service._get_db() as conn:
            conn.execute(
                """
                UPDATE document_batches 
                SET progress_percentage = ?, 
                    current_document = ?,
                    updated_at = ?
                WHERE batch_id = ?
                """,
                (progress, current_document, datetime.utcnow().isoformat(), batch_id)
            )
    except Exception as e:
        logger.error(f"Error updating batch progress: {e}")


# Bind the methods to the task class
DocumentProcessingTask._update_batch_status = _update_batch_status
DocumentProcessingTask._update_batch_progress = _update_batch_progress


# Helper function to queue batch for processing
def queue_batch_processing(batch_id: str, document_ids: list[str], delay: Optional[int] = None) -> str:
    """
    Queue a batch of documents for processing
    
    Args:
        batch_id: UUID of the batch
        document_ids: List of document UUIDs
        delay: Optional delay in seconds before processing
        
    Returns:
        Task ID
    """
    if delay:
        task = process_batch.apply_async(
            args=[batch_id, document_ids],
            countdown=delay
        )
    else:
        task = process_batch.apply_async(args=[batch_id, document_ids])
    
    return task.id