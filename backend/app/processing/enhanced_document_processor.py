"""
Enhanced document processing with BioBERT entity extraction

This module extends the document processing pipeline to include medical entity
extraction using BioBERT after text extraction.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from celery import Task
from celery.utils.log import get_task_logger

from celery_config import celery_app
from app.processing.text_extractor import TextExtractor
from app.extractors.term_extractor import EnhancedTermExtractor
from api.v1.services.document_service import DocumentService
from api.v1.models.document import DocumentStatus

logger = get_task_logger(__name__)


class EnhancedDocumentProcessingTask(Task):
    """Enhanced task class with AI capabilities"""
    _document_service = None
    _text_extractor = None
    _term_extractor = None
    
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
    
    @property
    def term_extractor(self):
        if self._term_extractor is None:
            self._term_extractor = EnhancedTermExtractor(
                use_cache=True,
                confidence_threshold=0.7,
                use_terminology_mapping=True
            )
        return self._term_extractor


@celery_app.task(
    bind=True, 
    base=EnhancedDocumentProcessingTask,
    name='app.processing.enhanced_document_processor.process_document_with_ai'
)
def process_document_with_ai(
    self, 
    document_id: str, 
    extract_entities: bool = True,
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Process a document with text extraction and AI entity extraction
    
    Args:
        document_id: UUID of the document to process
        extract_entities: Whether to extract medical entities
        confidence_threshold: Minimum confidence for entity extraction
        
    Returns:
        Dict with processing results including entities
    """
    logger.info(f"Starting enhanced document processing for {document_id}")
    
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
        
        # Step 1: Extract text
        logger.info(f"Extracting text from {document_info['filename']} ({document_info['document_type']})")
        
        extracted_text, extraction_method, metadata = self.text_extractor.extract_text(
            file_path=document_info['file_path'],
            document_type=document_info['document_type']
        )
        
        if extracted_text is None:
            error_msg = metadata.get('error', 'Unknown error during text extraction')
            raise Exception(f"Text extraction failed: {error_msg}")
        
        # Step 2: Extract medical entities if requested
        entities = []
        entity_statistics = {}
        
        if extract_entities and extracted_text.strip():
            logger.info(f"Extracting medical entities with confidence >= {confidence_threshold}")
            
            try:
                # Perform document analysis with entity extraction
                analysis_result = self.term_extractor.analyze_document(extracted_text)
                
                entities = analysis_result.get('entities', [])
                entity_statistics = analysis_result.get('statistics', {})
                
                logger.info(f"Extracted {len(entities)} medical entities")
                
            except Exception as e:
                logger.warning(f"Entity extraction failed: {e}")
                entities = []
                entity_statistics = {"error": str(e)}
        
        # Step 3: Store results
        success = self._store_processed_document(
            document_id,
            extracted_text,
            extraction_method,
            metadata,
            entities,
            entity_statistics
        )
        
        if not success:
            raise Exception("Failed to store processed document")
        
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
            'entity_count': len(entities),
            'entity_types': entity_statistics.get('entity_summary', {}),
            'processing_time': entity_statistics.get('processing_time', 0),
            'extraction_methods': entity_statistics.get('extraction_methods', []),
            'metadata': metadata,
            'preview': self.text_extractor.get_text_preview(extracted_text, 200),
            'entities_preview': entities[:10] if entities else []  # First 10 entities
        }
        
        logger.info(
            f"Enhanced document processing completed for {document_id}: "
            f"{word_count} words, {len(entities)} entities extracted"
        )
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


@celery_app.task(
    bind=True,
    base=EnhancedDocumentProcessingTask,
    name='app.processing.enhanced_document_processor.extract_entities_from_document'
)
def extract_entities_from_document(
    self,
    document_id: str,
    confidence_threshold: float = 0.7,
    force_reextraction: bool = False
) -> Dict[str, Any]:
    """
    Extract entities from an already processed document
    
    Args:
        document_id: UUID of the document
        confidence_threshold: Minimum confidence for entities
        force_reextraction: Force re-extraction even if entities exist
        
    Returns:
        Dict with entity extraction results
    """
    logger.info(f"Extracting entities from document {document_id}")
    
    try:
        # Get document with extracted text
        document_info = self._get_document_with_text(document_id)
        if not document_info:
            raise ValueError(f"Document {document_id} not found or has no extracted text")
        
        extracted_text = document_info.get('extracted_text')
        if not extracted_text:
            raise ValueError(f"Document {document_id} has no extracted text")
        
        # Check if entities already exist and force_reextraction is False
        if not force_reextraction:
            existing_entities = self._get_existing_entities(document_id)
            if existing_entities:
                logger.info(f"Found {len(existing_entities)} existing entities")
                return {
                    'status': 'completed',
                    'document_id': document_id,
                    'entity_count': len(existing_entities),
                    'entities': existing_entities,
                    'reextracted': False
                }
        
        # Extract entities
        logger.info(f"Analyzing document text ({len(extracted_text)} characters)")
        analysis_result = self.term_extractor.analyze_document(extracted_text)
        
        entities = analysis_result.get('entities', [])
        entity_statistics = analysis_result.get('statistics', {})
        
        # Store entities
        self._store_entities(document_id, entities, entity_statistics)
        
        logger.info(f"Extracted and stored {len(entities)} entities for document {document_id}")
        
        return {
            'status': 'completed',
            'document_id': document_id,
            'entity_count': len(entities),
            'entity_types': entity_statistics.get('entity_summary', {}),
            'processing_time': entity_statistics.get('processing_time', 0),
            'extraction_methods': entity_statistics.get('extraction_methods', []),
            'confidence_stats': entity_statistics.get('confidence_stats', {}),
            'entities': entities,
            'reextracted': True
        }
        
    except Exception as e:
        logger.error(f"Error extracting entities from document {document_id}: {e}")
        raise


@celery_app.task(
    bind=True,
    base=EnhancedDocumentProcessingTask,
    name='app.processing.enhanced_document_processor.batch_extract_entities'
)
def batch_extract_entities(
    self,
    document_ids: List[str],
    confidence_threshold: float = 0.7,
    batch_size: int = 8
) -> Dict[str, Any]:
    """
    Extract entities from multiple documents in batch
    
    Args:
        document_ids: List of document IDs
        confidence_threshold: Minimum confidence for entities
        batch_size: Processing batch size
        
    Returns:
        Dict with batch processing results
    """
    logger.info(f"Starting batch entity extraction for {len(document_ids)} documents")
    
    results = []
    total_entities = 0
    
    for document_id in document_ids:
        try:
            result = extract_entities_from_document.apply(
                args=[document_id, confidence_threshold, False]
            ).get()
            
            results.append({
                'document_id': document_id,
                'status': 'success',
                'entity_count': result.get('entity_count', 0),
                'entity_types': result.get('entity_types', {})
            })
            
            total_entities += result.get('entity_count', 0)
            
        except Exception as e:
            logger.error(f"Failed to extract entities from document {document_id}: {e}")
            results.append({
                'document_id': document_id,
                'status': 'failed',
                'error': str(e)
            })
    
    logger.info(f"Batch extraction completed: {total_entities} total entities extracted")
    
    return {
        'batch_size': len(document_ids),
        'total_entities': total_entities,
        'successful': len([r for r in results if r['status'] == 'success']),
        'failed': len([r for r in results if r['status'] == 'failed']),
        'results': results
    }


# Helper methods for the task class
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


def _get_document_with_text(self, document_id: str) -> Optional[Dict[str, Any]]:
    """Get document with extracted text"""
    try:
        with self.document_service._get_db() as conn:
            row = conn.execute(
                """
                SELECT document_id, filename, extracted_text, extraction_method
                FROM documents WHERE document_id = ? AND extracted_text IS NOT NULL
                """,
                (document_id,)
            ).fetchone()
            
            if row:
                return dict(row)
            return None
    except Exception as e:
        logger.error(f"Error getting document with text: {e}")
        return None


def _get_existing_entities(self, document_id: str) -> List[Dict[str, Any]]:
    """Get existing entities for a document"""
    try:
        with self.document_service._get_db() as conn:
            rows = conn.execute(
                """
                SELECT entity_data FROM document_entities 
                WHERE document_id = ?
                """,
                (document_id,)
            ).fetchall()
            
            if rows:
                # Assuming entity_data is stored as JSON
                entities = []
                for row in rows:
                    entity_data = json.loads(row['entity_data'])
                    entities.append(entity_data)
                return entities
            return []
    except Exception as e:
        logger.error(f"Error getting existing entities: {e}")
        return []


def _store_processed_document(
    self,
    document_id: str,
    extracted_text: str,
    extraction_method: str,
    metadata: Dict[str, Any],
    entities: List[Dict[str, Any]],
    entity_statistics: Dict[str, Any]
) -> bool:
    """Store processed document with text and entities"""
    try:
        with self.document_service._get_db() as conn:
            # Update document with extracted text
            conn.execute(
                """
                UPDATE documents 
                SET extracted_text = ?, 
                    extraction_method = ?,
                    page_count = ?,
                    entity_count = ?,
                    entity_statistics = ?,
                    updated_at = ?
                WHERE document_id = ?
                """,
                (
                    extracted_text,
                    extraction_method,
                    metadata.get('page_count', 1),
                    len(entities),
                    json.dumps(entity_statistics),
                    datetime.utcnow().isoformat(),
                    document_id
                )
            )
            
            # Store entities if any
            if entities:
                self._store_entities(document_id, entities, entity_statistics)
            
            return True
            
    except Exception as e:
        logger.error(f"Error storing processed document: {e}")
        return False


def _store_entities(
    self,
    document_id: str,
    entities: List[Dict[str, Any]],
    entity_statistics: Dict[str, Any]
) -> bool:
    """Store extracted entities"""
    try:
        with self.document_service._get_db() as conn:
            # Create entities table if it doesn't exist
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    entity_text TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    start_position INTEGER,
                    end_position INTEGER,
                    confidence REAL,
                    source TEXT,
                    entity_data TEXT,
                    created_at TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents (document_id)
                )
                """
            )
            
            # Delete existing entities for this document
            conn.execute(
                "DELETE FROM document_entities WHERE document_id = ?",
                (document_id,)
            )
            
            # Insert new entities
            for entity in entities:
                conn.execute(
                    """
                    INSERT INTO document_entities (
                        document_id, entity_text, entity_type, start_position,
                        end_position, confidence, source, entity_data, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        entity.get('text', ''),
                        entity.get('type', ''),
                        entity.get('start', 0),
                        entity.get('end', 0),
                        entity.get('confidence', 0.0),
                        entity.get('source', ''),
                        json.dumps(entity),
                        datetime.utcnow().isoformat()
                    )
                )
            
            return True
            
    except Exception as e:
        logger.error(f"Error storing entities: {e}")
        return False


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


# Bind methods to task class
EnhancedDocumentProcessingTask._get_document_info = _get_document_info
EnhancedDocumentProcessingTask._get_document_with_text = _get_document_with_text
EnhancedDocumentProcessingTask._get_existing_entities = _get_existing_entities
EnhancedDocumentProcessingTask._store_processed_document = _store_processed_document
EnhancedDocumentProcessingTask._store_entities = _store_entities
EnhancedDocumentProcessingTask._update_document_status = _update_document_status