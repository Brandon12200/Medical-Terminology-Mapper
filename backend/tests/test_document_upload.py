"""
Test cases for document upload API endpoints
"""

import pytest
import json
import io
from pathlib import Path
from uuid import UUID
from fastapi.testclient import TestClient
import tempfile
import shutil

from api.main import app
from api.v1.models.document import DocumentStatus, DocumentType


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_files_dir(tmp_path):
    """Create temporary directory for test files"""
    return tmp_path


@pytest.fixture
def sample_pdf_content():
    """Create sample PDF content (minimal valid PDF)"""
    # Minimal valid PDF structure
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << >> /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
196
%%EOF"""


@pytest.fixture
def sample_txt_content():
    """Create sample text content"""
    return b"""Patient: John Doe
Date: 2024-01-15

Chief Complaint: Type 2 diabetes mellitus follow-up

Assessment:
- Hemoglobin A1c: 7.2%
- Blood glucose: 145 mg/dL
- Blood pressure: 130/85 mmHg

Plan:
- Continue metformin 1000mg twice daily
- Schedule follow-up in 3 months
"""


class TestDocumentUpload:
    """Test document upload functionality"""
    
    def test_upload_pdf_document(self, client, sample_pdf_content):
        """Test uploading a PDF document"""
        files = {
            'file': ('test_clinical_notes.pdf', sample_pdf_content, 'application/pdf')
        }
        data = {
            'document_type': 'pdf',
            'metadata': json.dumps({'patient_id': '12345', 'encounter_date': '2024-01-15'})
        }
        
        response = client.post('/api/v1/documents/upload', files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert 'document_id' in result
        assert UUID(result['document_id'])  # Valid UUID
        assert result['status'] == 'pending'
        assert result['filename'] == 'test_clinical_notes.pdf'
        assert result['document_type'] == 'pdf'
        assert result['file_size'] > 0
        assert 'upload_timestamp' in result
        assert 'processing_url' in result
        assert result['processing_url'].endswith('/status')
    
    def test_upload_txt_document(self, client, sample_txt_content):
        """Test uploading a text document"""
        files = {
            'file': ('clinical_notes.txt', sample_txt_content, 'text/plain')
        }
        data = {
            'document_type': 'txt'
        }
        
        response = client.post('/api/v1/documents/upload', files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['document_type'] == 'txt'
        assert result['filename'] == 'clinical_notes.txt'
        assert result['file_size'] == len(sample_txt_content)
    
    def test_upload_with_invalid_extension(self, client, sample_pdf_content):
        """Test upload fails with mismatched extension"""
        files = {
            'file': ('test.txt', sample_pdf_content, 'application/pdf')
        }
        data = {
            'document_type': 'pdf'
        }
        
        response = client.post('/api/v1/documents/upload', files=files, data=data)
        
        assert response.status_code == 400
        assert "File extension" in response.json()['detail']
    
    def test_upload_with_invalid_metadata(self, client, sample_txt_content):
        """Test upload fails with invalid metadata"""
        files = {
            'file': ('test.txt', sample_txt_content, 'text/plain')
        }
        data = {
            'document_type': 'txt',
            'metadata': 'invalid json'
        }
        
        response = client.post('/api/v1/documents/upload', files=files, data=data)
        
        assert response.status_code == 400
        assert "Invalid metadata format" in response.json()['detail']
    
    def test_get_document_status(self, client, sample_txt_content):
        """Test getting document processing status"""
        # First upload a document
        files = {
            'file': ('test.txt', sample_txt_content, 'text/plain')
        }
        data = {'document_type': 'txt'}
        
        upload_response = client.post('/api/v1/documents/upload', files=files, data=data)
        document_id = upload_response.json()['document_id']
        
        # Get status
        response = client.get(f'/api/v1/documents/{document_id}/status')
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['document_id'] == document_id
        assert result['status'] in ['pending', 'processing', 'completed']
        assert 'progress' in result
        assert 'current_step' in result
    
    def test_get_nonexistent_document_status(self, client):
        """Test getting status for non-existent document"""
        fake_id = '123e4567-e89b-12d3-a456-426614174000'
        response = client.get(f'/api/v1/documents/{fake_id}/status')
        
        assert response.status_code == 404
        assert "not found" in response.json()['detail']
    
    def test_list_documents(self, client, sample_txt_content):
        """Test listing uploaded documents"""
        # Upload a few documents with unique content
        for i in range(3):
            unique_content = sample_txt_content + f' Document {i}'.encode()
            files = {
                'file': (f'test_{i}.txt', unique_content, 'text/plain')
            }
            data = {'document_type': 'txt'}
            client.post('/api/v1/documents/upload', files=files, data=data)
        
        # List documents
        response = client.get('/api/v1/documents/')
        
        assert response.status_code == 200
        result = response.json()
        
        assert 'documents' in result
        assert 'total' in result
        assert 'page' in result
        assert 'page_size' in result
        assert result['total'] >= 3
        assert len(result['documents']) >= 3
    
    def test_list_documents_with_pagination(self, client):
        """Test document listing with pagination"""
        response = client.get('/api/v1/documents/?page=1&page_size=5')
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['page'] == 1
        assert result['page_size'] == 5
        assert len(result['documents']) <= 5
    
    def test_list_documents_by_status(self, client):
        """Test filtering documents by status"""
        response = client.get('/api/v1/documents/?status=pending')
        
        assert response.status_code == 200
        result = response.json()
        
        # All returned documents should have pending status
        for doc in result['documents']:
            assert doc['status'] == 'pending'
    
    def test_delete_document(self, client, sample_txt_content):
        """Test deleting a document"""
        # First upload a document
        files = {
            'file': ('test.txt', sample_txt_content, 'text/plain')
        }
        data = {'document_type': 'txt'}
        
        upload_response = client.post('/api/v1/documents/upload', files=files, data=data)
        document_id = upload_response.json()['document_id']
        
        # Delete it
        response = client.delete(f'/api/v1/documents/{document_id}')
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['document_id'] == document_id
        assert result['message'] == "Document deleted successfully"
        assert 'deleted_at' in result
        
        # Verify it's gone
        status_response = client.get(f'/api/v1/documents/{document_id}/status')
        assert status_response.status_code == 404
    
    def test_delete_nonexistent_document(self, client):
        """Test deleting non-existent document"""
        fake_id = '123e4567-e89b-12d3-a456-426614174000'
        response = client.delete(f'/api/v1/documents/{fake_id}')
        
        assert response.status_code == 404
    
    def test_get_document_metadata(self, client, sample_txt_content):
        """Test getting document metadata"""
        # Upload a document with metadata
        files = {
            'file': ('test.txt', sample_txt_content, 'text/plain')
        }
        data = {
            'document_type': 'txt',
            'metadata': json.dumps({'department': 'cardiology', 'priority': 'high'})
        }
        
        upload_response = client.post('/api/v1/documents/upload', files=files, data=data)
        document_id = upload_response.json()['document_id']
        
        # Get metadata
        response = client.get(f'/api/v1/documents/{document_id}/metadata')
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['filename'] == 'test.txt'
        assert result['document_type'] == 'txt'
        assert result['file_size'] == len(sample_txt_content)
        assert 'checksum' in result
        assert result['metadata']['department'] == 'cardiology'
        assert result['metadata']['priority'] == 'high'
    
    def test_document_service_health(self, client):
        """Test document service health check"""
        response = client.get('/api/v1/documents/health')
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['status'] == 'healthy'
        assert result['service'] == 'document_upload'
        assert 'upload_directory' in result
        assert result['database'] == 'connected'


@pytest.fixture(autouse=True)
def cleanup_uploads():
    """Clean up upload directories after tests"""
    yield
    # Clean up any test upload directories
    uploads_dir = Path("uploads/documents")
    if uploads_dir.exists():
        for item in uploads_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
    
    # Clean up test database
    test_db = Path("data/documents.db")
    if test_db.exists():
        test_db.unlink()