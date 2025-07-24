"""
Document processing service for handling uploads and text extraction
"""

import os
import hashlib
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, BinaryIO
from uuid import UUID, uuid4
import magic
import sqlite3
import json
from contextlib import contextmanager

from ..models.document import (
    DocumentType, DocumentStatus, DocumentMetadata,
    DocumentUploadResponse, DocumentProcessingStatus,
    ExtractedText
)
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


class DocumentService:
    """Service for handling document uploads and processing"""
    
    def __init__(self, upload_dir: str = "uploads/documents", db_path: str = "data/documents.db"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_database()
        
        # File type validation
        self.allowed_mime_types = {
            DocumentType.PDF: ["application/pdf"],
            DocumentType.DOCX: [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ],
            DocumentType.TXT: ["text/plain"],
            DocumentType.RTF: ["application/rtf", "text/rtf"],
            DocumentType.HL7: ["text/plain", "application/hl7-v2+er7"]
        }
        
        # Maximum file sizes (in bytes)
        self.max_file_sizes = {
            DocumentType.PDF: 50 * 1024 * 1024,  # 50MB
            DocumentType.DOCX: 25 * 1024 * 1024,  # 25MB
            DocumentType.TXT: 10 * 1024 * 1024,   # 10MB
            DocumentType.RTF: 25 * 1024 * 1024,   # 25MB
            DocumentType.HL7: 5 * 1024 * 1024     # 5MB
        }
    
    def _init_database(self):
        """Initialize the document storage database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self._get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_timestamp TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    page_count INTEGER,
                    encoding TEXT,
                    checksum TEXT NOT NULL,
                    metadata TEXT,
                    status TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    error_message TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    extracted_text TEXT,
                    extraction_method TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_status 
                ON documents(status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_upload_timestamp 
                ON documents(upload_timestamp)
            """)
            
            # Create batch tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_batches (
                    batch_id TEXT PRIMARY KEY,
                    batch_name TEXT,
                    status TEXT NOT NULL,
                    total_documents INTEGER NOT NULL,
                    processed_documents INTEGER DEFAULT 0,
                    successful_documents INTEGER DEFAULT 0,
                    failed_documents INTEGER DEFAULT 0,
                    progress_percentage REAL DEFAULT 0.0,
                    current_document TEXT,
                    metadata TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Add batch_id column to documents table if it doesn't exist
            try:
                conn.execute("ALTER TABLE documents ADD COLUMN batch_id TEXT")
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            # Create index for batch lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_batch_id 
                ON documents(batch_id)
            """)
    
    @contextmanager
    def _get_db(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def validate_file_type(self, content: bytes, document_type: DocumentType) -> tuple[bool, str]:
        """Validate file type using magic bytes"""
        try:
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_buffer(content[:2048])  # Check first 2KB
            
            allowed_mimes = self.allowed_mime_types.get(document_type, [])
            if detected_mime not in allowed_mimes:
                return False, f"Invalid file type. Expected {document_type}, got {detected_mime}"
            
            return True, detected_mime
        except Exception as e:
            logger.error(f"Error validating file type: {e}")
            return False, "Could not validate file type"
    
    def validate_file_size(self, file_size: int, document_type: DocumentType) -> tuple[bool, str]:
        """Validate file size"""
        max_size = self.max_file_sizes.get(document_type, 10 * 1024 * 1024)
        if file_size > max_size:
            return False, f"File too large. Maximum size for {document_type} is {max_size / (1024*1024):.1f}MB"
        return True, ""
    
    def calculate_checksum(self, content: bytes) -> str:
        """Calculate SHA-256 checksum of file content"""
        return hashlib.sha256(content).hexdigest()
    
    async def save_document(
        self,
        content: bytes,
        filename: str,
        document_type: DocumentType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentUploadResponse:
        """Save document to storage and create database entry"""
        
        # Generate document ID
        document_id = uuid4()
        
        # Validate file type
        is_valid, mime_or_error = self.validate_file_type(content, document_type)
        if not is_valid:
            raise ValueError(mime_or_error)
        
        mime_type = mime_or_error
        
        # Validate file size
        file_size = len(content)
        is_valid, error = self.validate_file_size(file_size, document_type)
        if not is_valid:
            raise ValueError(error)
        
        # Calculate checksum
        checksum = self.calculate_checksum(content)
        
        # Check for duplicate uploads
        with self._get_db() as conn:
            existing = conn.execute(
                "SELECT document_id FROM documents WHERE checksum = ?",
                (checksum,)
            ).fetchone()
            
            if existing:
                raise ValueError(f"Document already uploaded with ID: {existing['document_id']}")
        
        # Save file to disk
        file_path = self.upload_dir / str(document_id) / filename
        file_path.parent.mkdir(exist_ok=True)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create database entry
        timestamp = datetime.utcnow()
        
        with self._get_db() as conn:
            conn.execute("""
                INSERT INTO documents (
                    document_id, filename, document_type, file_size,
                    upload_timestamp, mime_type, checksum, metadata,
                    status, file_path, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(document_id), filename, document_type.value, file_size,
                timestamp.isoformat(), mime_type, checksum,
                json.dumps(metadata) if metadata else None,
                DocumentStatus.PENDING.value, str(file_path),
                timestamp.isoformat(), timestamp.isoformat()
            ))
        
        return DocumentUploadResponse(
            document_id=document_id,
            status=DocumentStatus.PENDING,
            filename=filename,
            document_type=document_type,
            file_size=file_size,
            upload_timestamp=timestamp,
            processing_url=f"/api/v1/documents/{document_id}/status"
        )
    
    def get_document_status(self, document_id: UUID) -> Optional[DocumentProcessingStatus]:
        """Get document processing status"""
        with self._get_db() as conn:
            row = conn.execute(
                """
                SELECT document_id, status, started_at, completed_at, error_message
                FROM documents WHERE document_id = ?
                """,
                (str(document_id),)
            ).fetchone()
            
            if not row:
                return None
            
            # Calculate progress based on status
            progress = 0.0
            current_step = None
            
            if row['status'] == DocumentStatus.PENDING.value:
                progress = 0.0
                current_step = "Waiting in queue"
            elif row['status'] == DocumentStatus.PROCESSING.value:
                progress = 50.0  # This would be more dynamic with real extraction
                current_step = "Extracting text from document"
            elif row['status'] == DocumentStatus.COMPLETED.value:
                progress = 100.0
                current_step = "Processing complete"
            elif row['status'] == DocumentStatus.FAILED.value:
                progress = 0.0
                current_step = "Processing failed"
            
            return DocumentProcessingStatus(
                document_id=document_id,
                status=DocumentStatus(row['status']),
                progress=progress,
                current_step=current_step,
                error_message=row['error_message'],
                started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
                completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None
            )
    
    def list_documents(
        self, 
        page: int = 1, 
        page_size: int = 10,
        status: Optional[DocumentStatus] = None
    ) -> tuple[List[DocumentUploadResponse], int]:
        """List uploaded documents with pagination"""
        offset = (page - 1) * page_size
        
        with self._get_db() as conn:
            # Build query
            query = "SELECT * FROM documents"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status.value)
            
            query += " ORDER BY upload_timestamp DESC LIMIT ? OFFSET ?"
            params.extend([page_size, offset])
            
            # Get documents
            rows = conn.execute(query, params).fetchall()
            
            # Get total count
            count_query = "SELECT COUNT(*) as total FROM documents"
            if status:
                count_query += " WHERE status = ?"
                total = conn.execute(count_query, [status.value]).fetchone()['total']
            else:
                total = conn.execute(count_query).fetchone()['total']
            
            # Convert to response models
            documents = []
            for row in rows:
                documents.append(DocumentUploadResponse(
                    document_id=UUID(row['document_id']),
                    status=DocumentStatus(row['status']),
                    filename=row['filename'],
                    document_type=DocumentType(row['document_type']),
                    file_size=row['file_size'],
                    upload_timestamp=datetime.fromisoformat(row['upload_timestamp']),
                    processing_url=f"/api/v1/documents/{row['document_id']}/status"
                ))
            
            return documents, total
    
    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document and its files"""
        with self._get_db() as conn:
            row = conn.execute(
                "SELECT file_path FROM documents WHERE document_id = ?",
                (str(document_id),)
            ).fetchone()
            
            if not row:
                return False
            
            # Delete file from disk
            file_path = Path(row['file_path'])
            if file_path.exists():
                file_path.unlink()
                # Remove parent directory if empty
                if file_path.parent.exists() and not list(file_path.parent.iterdir()):
                    file_path.parent.rmdir()
            
            # Delete from database
            conn.execute(
                "DELETE FROM documents WHERE document_id = ?",
                (str(document_id),)
            )
            
            return True
    
    def get_document_metadata(self, document_id: UUID) -> Optional[DocumentMetadata]:
        """Get document metadata"""
        with self._get_db() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?",
                (str(document_id),)
            ).fetchone()
            
            if not row:
                return None
            
            return DocumentMetadata(
                filename=row['filename'],
                document_type=DocumentType(row['document_type']),
                file_size=row['file_size'],
                upload_timestamp=datetime.fromisoformat(row['upload_timestamp']),
                mime_type=row['mime_type'],
                page_count=row['page_count'],
                encoding=row['encoding'],
                checksum=row['checksum'],
                metadata=json.loads(row['metadata']) if row['metadata'] else None
            )
    
    def get_extracted_text(self, document_id: UUID) -> Optional[ExtractedText]:
        """Get extracted text for a document"""
        with self._get_db() as conn:
            row = conn.execute(
                """
                SELECT document_id, extracted_text, extraction_method, 
                       filename, document_type, file_size, upload_timestamp,
                       mime_type, page_count, encoding, checksum, metadata
                FROM documents 
                WHERE document_id = ? AND extracted_text IS NOT NULL
                """,
                (str(document_id),)
            ).fetchone()
            
            if not row or not row['extracted_text']:
                return None
            
            # Build metadata
            metadata = DocumentMetadata(
                filename=row['filename'],
                document_type=DocumentType(row['document_type']),
                file_size=row['file_size'],
                upload_timestamp=datetime.fromisoformat(row['upload_timestamp']),
                mime_type=row['mime_type'],
                page_count=row['page_count'],
                encoding=row['encoding'],
                checksum=row['checksum'],
                metadata=json.loads(row['metadata']) if row['metadata'] else None
            )
            
            # Parse sections if available
            sections = None
            if row['metadata']:
                metadata_dict = json.loads(row['metadata'])
                if 'sections' in metadata_dict:
                    sections = metadata_dict['sections']
            
            return ExtractedText(
                document_id=UUID(row['document_id']),
                text_content=row['extracted_text'],
                sections=sections,
                metadata=metadata,
                extraction_timestamp=datetime.utcnow(),  # Could store this separately
                extraction_method=row['extraction_method']
            )
    
    def update_extraction_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ) -> bool:
        """Update document extraction status"""
        with self._get_db() as conn:
            try:
                # Build update query
                updates = ["status = ?", "updated_at = ?"]
                params = [status.value, datetime.utcnow().isoformat()]
                
                if error_message is not None:
                    updates.append("error_message = ?")
                    params.append(error_message)
                
                if started_at is not None:
                    updates.append("started_at = ?")
                    params.append(started_at.isoformat())
                
                if completed_at is not None:
                    updates.append("completed_at = ?")
                    params.append(completed_at.isoformat())
                
                params.append(str(document_id))
                
                query = f"UPDATE documents SET {', '.join(updates)} WHERE document_id = ?"
                conn.execute(query, params)
                
                return True
            except Exception as e:
                logger.error(f"Error updating extraction status: {e}")
                return False
    
    # Batch processing methods
    def create_document_batch(self, 
                            batch_name: Optional[str], 
                            metadata: Optional[Dict[str, Any]],
                            total_documents: int) -> UUID:
        """Create a new document batch"""
        batch_id = uuid4()
        now = datetime.utcnow()
        
        try:
            with self._get_db() as conn:
                conn.execute("""
                    INSERT INTO document_batches (
                        batch_id, batch_name, status, total_documents,
                        metadata, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(batch_id),
                    batch_name,
                    "pending",
                    total_documents,
                    json.dumps(metadata) if metadata else None,
                    now.isoformat(),
                    now.isoformat()
                ))
                
            logger.info(f"Created batch {batch_id} with {total_documents} documents")
            return batch_id
            
        except Exception as e:
            logger.error(f"Error creating batch: {e}")
            raise
    
    async def save_document(self,
                          content: bytes,
                          filename: str,
                          document_type: DocumentType,
                          metadata: Optional[Dict[str, Any]] = None,
                          batch_id: Optional[UUID] = None) -> DocumentUploadResponse:
        """Save a document to storage with optional batch association"""
        try:
            # Validate file type
            if document_type not in self.allowed_mime_types:
                raise ValueError(f"Unsupported document type: {document_type}")
            
            # Check file size
            file_size = len(content)
            if file_size > self.max_file_sizes.get(document_type, 0):
                raise ValueError(
                    f"File size ({file_size} bytes) exceeds maximum "
                    f"({self.max_file_sizes[document_type]} bytes) for {document_type}"
                )
            
            # Detect MIME type
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_buffer(content)
            
            # Validate MIME type matches document type
            if detected_mime not in self.allowed_mime_types[document_type]:
                logger.warning(
                    f"MIME type mismatch: expected {self.allowed_mime_types[document_type]}, "
                    f"got {detected_mime}"
                )
            
            # Calculate checksum
            checksum = hashlib.sha256(content).hexdigest()
            
            # Generate document ID
            document_id = uuid4()
            
            # Save file to disk
            file_path = self.upload_dir / str(document_id) / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Save metadata to database
            now = datetime.utcnow()
            
            # Add batch_id to metadata if provided
            if batch_id and metadata:
                metadata['batch_id'] = str(batch_id)
            elif batch_id:
                metadata = {'batch_id': str(batch_id)}
            
            with self._get_db() as conn:
                conn.execute("""
                    INSERT INTO documents (
                        document_id, filename, document_type, file_size,
                        upload_timestamp, mime_type, checksum, metadata,
                        status, file_path, created_at, updated_at, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(document_id),
                    filename,
                    document_type.value,
                    file_size,
                    now.isoformat(),
                    detected_mime,
                    checksum,
                    json.dumps(metadata) if metadata else None,
                    DocumentStatus.PENDING.value,
                    str(file_path),
                    now.isoformat(),
                    now.isoformat(),
                    str(batch_id) if batch_id else None
                ))
            
            logger.info(f"Document {document_id} saved successfully")
            
            return DocumentUploadResponse(
                document_id=document_id,
                status=DocumentStatus.PENDING,
                filename=filename,
                document_type=document_type,
                file_size=file_size,
                upload_timestamp=now,
                processing_url=f"/api/v1/documents/{document_id}/status"
            )
            
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            raise
    
    def get_batch_status(self, batch_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the status of a document batch"""
        from ..models.document_batch import BatchProcessingStatus, BatchDocumentItem
        
        try:
            with self._get_db() as conn:
                # Get batch info
                batch = conn.execute("""
                    SELECT * FROM document_batches WHERE batch_id = ?
                """, (str(batch_id),)).fetchone()
                
                if not batch:
                    return None
                
                # Get documents in batch
                documents = conn.execute("""
                    SELECT document_id, filename, document_type, status, 
                           file_size, error_message, started_at, completed_at
                    FROM documents 
                    WHERE batch_id = ?
                    ORDER BY upload_timestamp
                """, (str(batch_id),)).fetchall()
                
                # Calculate processed documents
                processed = sum(1 for doc in documents if doc['status'] not in ['pending', 'processing'])
                successful = sum(1 for doc in documents if doc['status'] == 'completed')
                failed = sum(1 for doc in documents if doc['status'] == 'failed')
                
                # Create document items
                doc_items = []
                for doc in documents:
                    processing_time = None
                    if doc['started_at'] and doc['completed_at']:
                        start = datetime.fromisoformat(doc['started_at'])
                        end = datetime.fromisoformat(doc['completed_at'])
                        processing_time = (end - start).total_seconds()
                    
                    doc_items.append(BatchDocumentItem(
                        document_id=UUID(doc['document_id']),
                        filename=doc['filename'],
                        document_type=DocumentType(doc['document_type']),
                        status=DocumentStatus(doc['status']),
                        file_size=doc['file_size'],
                        error_message=doc['error_message'],
                        processing_time=processing_time
                    ))
                
                # Update progress in database
                progress = (processed / batch['total_documents'] * 100) if batch['total_documents'] > 0 else 0
                conn.execute("""
                    UPDATE document_batches 
                    SET processed_documents = ?, successful_documents = ?, 
                        failed_documents = ?, progress_percentage = ?, updated_at = ?
                    WHERE batch_id = ?
                """, (processed, successful, failed, progress, datetime.utcnow().isoformat(), str(batch_id)))
                
                return BatchProcessingStatus(
                    batch_id=UUID(batch['batch_id']),
                    status=batch['status'],
                    total_documents=batch['total_documents'],
                    processed_documents=processed,
                    successful_documents=successful,
                    failed_documents=failed,
                    progress_percentage=progress,
                    current_document=batch['current_document'],
                    documents=doc_items,
                    started_at=datetime.fromisoformat(batch['started_at']) if batch['started_at'] else None,
                    completed_at=datetime.fromisoformat(batch['completed_at']) if batch['completed_at'] else None
                )
                
        except Exception as e:
            logger.error(f"Error getting batch status: {e}")
            return None
    
    def get_batch_results_summary(self, batch_id: UUID) -> Optional[Dict[str, Any]]:
        """Get aggregated results for a completed batch"""
        from ..models.document_batch import BatchResultsSummary, BatchUploadStatus
        
        try:
            with self._get_db() as conn:
                # Get batch info
                batch = conn.execute("""
                    SELECT * FROM document_batches WHERE batch_id = ?
                """, (str(batch_id),)).fetchone()
                
                if not batch:
                    return None
                
                # Get all documents with extracted entities
                documents = conn.execute("""
                    SELECT d.document_id, d.extracted_text, d.status
                    FROM documents d
                    WHERE d.batch_id = ?
                """, (str(batch_id),)).fetchall()
                
                # Initialize counters
                total_entities = 0
                entities_by_type = {}
                terminology_mappings = {}
                
                # Process each document to extract entity statistics
                for doc in documents:
                    if doc['status'] == 'completed' and doc['extracted_text']:
                        # Here we would normally parse the entities from the extracted_text
                        # or from a separate entities table
                        # For now, we'll return placeholder data
                        pass
                
                # Calculate processing time
                processing_time = 0.0
                if batch['started_at'] and batch['completed_at']:
                    start = datetime.fromisoformat(batch['started_at'])
                    end = datetime.fromisoformat(batch['completed_at'])
                    processing_time = (end - start).total_seconds()
                
                return BatchResultsSummary(
                    batch_id=UUID(batch['batch_id']),
                    batch_name=batch['batch_name'],
                    status=BatchUploadStatus(batch['status']),
                    total_documents=batch['total_documents'],
                    successful_documents=batch['successful_documents'],
                    failed_documents=batch['failed_documents'],
                    total_entities_extracted=total_entities,
                    entities_by_type=entities_by_type,
                    terminology_mappings=terminology_mappings,
                    processing_time=processing_time,
                    started_at=datetime.fromisoformat(batch['started_at']) if batch['started_at'] else datetime.utcnow(),
                    completed_at=datetime.fromisoformat(batch['completed_at']) if batch['completed_at'] else datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Error getting batch results: {e}")
            return None
    
    def export_batch_results(self,
                           batch_id: UUID,
                           format: str,
                           include_failed: bool = False,
                           include_raw_text: bool = False,
                           include_terminology_mappings: bool = True) -> Optional[str]:
        """Export batch results to file"""
        from ..models.document_batch import BatchExportFormat
        import csv
        import pandas as pd
        
        try:
            # Get batch documents
            with self._get_db() as conn:
                query = """
                    SELECT * FROM documents 
                    WHERE batch_id = ?
                """
                if not include_failed:
                    query += " AND status = 'completed'"
                    
                documents = conn.execute(query, (str(batch_id),)).fetchall()
                
                if not documents:
                    return None
            
            # Create export directory
            export_dir = Path("exports") / str(batch_id)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate export file
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            if format == BatchExportFormat.JSON:
                export_file = export_dir / f"batch_export_{timestamp}.json"
                
                # Prepare data for export
                export_data = {
                    "batch_id": str(batch_id),
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "documents": []
                }
                
                for doc in documents:
                    doc_data = {
                        "document_id": doc['document_id'],
                        "filename": doc['filename'],
                        "status": doc['status']
                    }
                    
                    if include_raw_text and doc['extracted_text']:
                        doc_data['extracted_text'] = doc['extracted_text']
                    
                    export_data['documents'].append(doc_data)
                
                with open(export_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
                    
            elif format == BatchExportFormat.CSV:
                export_file = export_dir / f"batch_export_{timestamp}.csv"
                
                # Prepare CSV data
                rows = []
                for doc in documents:
                    row = {
                        'document_id': doc['document_id'],
                        'filename': doc['filename'],
                        'status': doc['status'],
                        'file_size': doc['file_size'],
                        'document_type': doc['document_type']
                    }
                    
                    if include_raw_text:
                        row['extracted_text'] = doc['extracted_text'][:1000] if doc['extracted_text'] else ''
                    
                    rows.append(row)
                
                # Write CSV
                if rows:
                    with open(export_file, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)
                        
            elif format == BatchExportFormat.EXCEL:
                export_file = export_dir / f"batch_export_{timestamp}.xlsx"
                
                # Create Excel workbook with multiple sheets
                with pd.ExcelWriter(export_file, engine='openpyxl') as writer:
                    # Documents sheet
                    doc_data = []
                    for doc in documents:
                        doc_data.append({
                            'Document ID': doc['document_id'],
                            'Filename': doc['filename'],
                            'Type': doc['document_type'],
                            'Status': doc['status'],
                            'Size (bytes)': doc['file_size']
                        })
                    
                    df_docs = pd.DataFrame(doc_data)
                    df_docs.to_excel(writer, sheet_name='Documents', index=False)
                    
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
            
            return str(export_file)
            
        except Exception as e:
            logger.error(f"Error exporting batch results: {e}")
            return None