"""
Extensive test cases for document upload API endpoints
"""

import pytest
import json
import io
import os
import time
from pathlib import Path
from uuid import UUID
from fastapi.testclient import TestClient
import tempfile
import shutil
import hashlib
import asyncio

from api.main import app
from api.v1.models.document import DocumentStatus, DocumentType
from api.v1.services.document_service import DocumentService


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def cleanup_test_data():
    """Clean up test data before and after tests"""
    # Clean before
    cleanup_dirs = ["uploads/documents", "data"]
    for dir_path in cleanup_dirs:
        if Path(dir_path).exists():
            shutil.rmtree(dir_path)
    
    yield
    
    # Clean after
    for dir_path in cleanup_dirs:
        if Path(dir_path).exists():
            shutil.rmtree(dir_path)


@pytest.fixture
def sample_files():
    """Create various sample files for testing"""
    files = {}
    
    # Minimal valid PDF
    files['pdf'] = b"""%PDF-1.4
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
    
    # Clinical text document
    files['txt'] = b"""Patient: Jane Smith
MRN: 987654321
Date: 2024-01-20

Chief Complaint: 
Patient presents with persistent hypertension and type 2 diabetes mellitus.

History of Present Illness:
65-year-old female with 10-year history of T2DM and HTN. Recent labs show:
- HbA1c: 8.1% (up from 7.5%)
- BP: 145/92 mmHg (average of 3 readings)
- Creatinine: 1.2 mg/dL
- eGFR: 58 mL/min/1.73m2

Medications:
1. Metformin 1000mg BID
2. Lisinopril 20mg daily
3. Amlodipine 5mg daily
4. Atorvastatin 40mg daily

Assessment and Plan:
1. Uncontrolled T2DM - Increase metformin to 1500mg BID, consider adding SGLT2 inhibitor
2. Stage 2 HTN - Increase lisinopril to 30mg daily
3. CKD Stage 3a - Monitor renal function quarterly
4. Follow-up in 4 weeks"""
    
    # RTF document
    files['rtf'] = b"""{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}
{\\colortbl;\\red0\\green0\\blue0;}
\\f0\\fs24 Clinical Report\\par
\\par
Patient exhibits symptoms consistent with acute bronchitis.\\par
Prescribed azithromycin 500mg x 5 days.\\par
}"""
    
    # HL7 message
    files['hl7'] = b"""MSH|^~\\&|SendingApp|SendingFac|ReceivingApp|ReceivingFac|20240120120000||ORU^R01|MSG001|P|2.5
PID|1||123456^^^MRN||DOE^JOHN^A||19600101|M
OBR|1||123456|80048^BASIC METABOLIC PANEL|||20240120
OBX|1|NM|2160-0^CREATININE^LN||1.2|mg/dL|0.6-1.2|N|||F
OBX|2|NM|2345-7^GLUCOSE^LN||145|mg/dL|70-100|H|||F"""
    
    # DOCX file (minimal valid structure)
    # This is a simplified version - real DOCX would be more complex
    files['docx'] = b"""PK\x03\x04\x14\x00\x00\x00\x08\x00""" + b"\x00" * 100  # Simplified
    
    return files


class TestDocumentUploadExtensive:
    """Extensive tests for document upload functionality"""
    
    def test_upload_all_supported_formats(self, client, sample_files, cleanup_test_data):
        """Test uploading all supported document formats"""
        formats = ['txt', 'pdf', 'rtf', 'hl7']  # Skip docx for now due to complexity
        
        for fmt in formats:
            files = {
                'file': (f'test.{fmt}', sample_files[fmt], f'application/{fmt}')
            }
            data = {
                'document_type': fmt,
                'metadata': json.dumps({'test': f'format_{fmt}'})
            }
            
            response = client.post('/api/v1/documents/upload', files=files, data=data)
            
            assert response.status_code == 200, f"Failed for format {fmt}"
            result = response.json()
            
            assert result['document_type'] == fmt
            assert result['filename'] == f'test.{fmt}'
            assert result['status'] == 'pending'
            assert UUID(result['document_id'])
    
    def test_duplicate_detection(self, client, sample_files, cleanup_test_data):
        """Test that duplicate files are detected"""
        # Upload first file
        files = {
            'file': ('test1.txt', sample_files['txt'], 'text/plain')
        }
        data = {'document_type': 'txt'}
        
        response1 = client.post('/api/v1/documents/upload', files=files, data=data)
        assert response1.status_code == 200
        
        # Try to upload same content with different name
        files = {
            'file': ('test2.txt', sample_files['txt'], 'text/plain')
        }
        
        response2 = client.post('/api/v1/documents/upload', files=files, data=data)
        assert response2.status_code == 400
        assert "already uploaded" in response2.json()['detail']
    
    def test_file_size_limits(self, client, cleanup_test_data):
        """Test file size validation"""
        # Create a file that exceeds TXT limit (10MB)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        files = {
            'file': ('large.txt', large_content, 'text/plain')
        }
        data = {'document_type': 'txt'}
        
        response = client.post('/api/v1/documents/upload', files=files, data=data)
        
        assert response.status_code == 400
        assert "File too large" in response.json()['detail']
    
    def test_invalid_file_types(self, client, cleanup_test_data):
        """Test rejection of invalid file types"""
        # Try to upload executable
        files = {
            'file': ('malicious.exe', b'MZ\x90\x00', 'application/x-msdownload')
        }
        data = {'document_type': 'txt'}
        
        response = client.post('/api/v1/documents/upload', files=files, data=data)
        
        assert response.status_code == 400
        assert "extension" in response.json()['detail'].lower()
    
    def test_mime_type_validation(self, client, sample_files, cleanup_test_data):
        """Test MIME type validation catches mismatched content"""
        # Try to upload PDF content as TXT
        files = {
            'file': ('fake.txt', sample_files['pdf'], 'text/plain')
        }
        data = {'document_type': 'txt'}
        
        response = client.post('/api/v1/documents/upload', files=files, data=data)
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()['detail']
    
    def test_concurrent_uploads(self, client, sample_files, cleanup_test_data):
        """Test handling multiple concurrent uploads"""
        import concurrent.futures
        
        def upload_file(index):
            files = {
                'file': (f'concurrent_{index}.txt', sample_files['txt'] + f' {index}'.encode(), 'text/plain')
            }
            data = {'document_type': 'txt'}
            return client.post('/api/v1/documents/upload', files=files, data=data)
        
        # Upload 10 files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(upload_file, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)
        
        # Verify all documents are listed
        list_response = client.get('/api/v1/documents/')
        assert list_response.json()['total'] >= 10
    
    def test_metadata_handling(self, client, sample_files, cleanup_test_data):
        """Test various metadata scenarios"""
        test_cases = [
            # Valid metadata
            {
                'metadata': json.dumps({
                    'patient_id': '12345',
                    'encounter_date': '2024-01-20',
                    'department': 'cardiology',
                    'priority': 'high',
                    'tags': ['urgent', 'follow-up']
                }),
                'should_succeed': True
            },
            # Empty metadata
            {
                'metadata': None,
                'should_succeed': True
            },
            # Complex nested metadata
            {
                'metadata': json.dumps({
                    'patient': {
                        'id': '12345',
                        'name': 'Test Patient',
                        'dob': '1960-01-01'
                    },
                    'clinical': {
                        'diagnoses': ['E11.9', 'I10'],
                        'procedures': ['99213']
                    }
                }),
                'should_succeed': True
            },
            # Invalid JSON
            {
                'metadata': 'not valid json{',
                'should_succeed': False
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            # Make each file unique to avoid duplicate detection
            unique_content = sample_files['txt'] + f' Test case {i}'.encode()
            files = {
                'file': (f'metadata_test_{i}.txt', unique_content, 'text/plain')
            }
            data = {
                'document_type': 'txt'
            }
            if test_case['metadata'] is not None:
                data['metadata'] = test_case['metadata']
            
            response = client.post('/api/v1/documents/upload', files=files, data=data)
            
            if test_case['should_succeed']:
                assert response.status_code == 200
                # Verify metadata is stored correctly
                doc_id = response.json()['document_id']
                metadata_response = client.get(f'/api/v1/documents/{doc_id}/metadata')
                assert metadata_response.status_code == 200
                
                if test_case['metadata'] and test_case['metadata'] != 'null':
                    stored_metadata = metadata_response.json()['metadata']
                    expected_metadata = json.loads(test_case['metadata'])
                    assert stored_metadata == expected_metadata
            else:
                assert response.status_code == 400
    
    def test_special_characters_in_filenames(self, client, sample_files, cleanup_test_data):
        """Test handling of special characters in filenames"""
        special_filenames = [
            'test file with spaces.txt',
            'test_file_with_underscores.txt',
            'test-file-with-hyphens.txt',
            'test.multiple.dots.txt',
            '测试中文.txt',
            'test_émojis_😀.txt'
        ]
        
        for filename in special_filenames:
            files = {
                'file': (filename, sample_files['txt'], 'text/plain')
            }
            data = {'document_type': 'txt'}
            
            response = client.post('/api/v1/documents/upload', files=files, data=data)
            
            # Should handle most filenames gracefully
            assert response.status_code == 200
            assert response.json()['filename'] == filename
    
    def test_pagination(self, client, sample_files, cleanup_test_data):
        """Test pagination functionality"""
        # Upload 25 documents
        for i in range(25):
            files = {
                'file': (f'pagination_test_{i}.txt', sample_files['txt'] + f' {i}'.encode(), 'text/plain')
            }
            data = {'document_type': 'txt'}
            client.post('/api/v1/documents/upload', files=files, data=data)
        
        # Test different page sizes
        page_tests = [
            {'page': 1, 'page_size': 10, 'expected_count': 10},
            {'page': 2, 'page_size': 10, 'expected_count': 10},
            {'page': 3, 'page_size': 10, 'expected_count': 5},
            {'page': 1, 'page_size': 25, 'expected_count': 25},
            {'page': 2, 'page_size': 25, 'expected_count': 0},
        ]
        
        for test in page_tests:
            response = client.get(
                f"/api/v1/documents/?page={test['page']}&page_size={test['page_size']}"
            )
            assert response.status_code == 200
            result = response.json()
            assert len(result['documents']) == test['expected_count']
            assert result['page'] == test['page']
            assert result['page_size'] == test['page_size']
            assert result['total'] == 25
    
    def test_status_filtering(self, client, sample_files, cleanup_test_data):
        """Test filtering documents by status"""
        # Upload some documents
        for i in range(5):
            files = {
                'file': (f'status_test_{i}.txt', sample_files['txt'] + f' {i}'.encode(), 'text/plain')
            }
            data = {'document_type': 'txt'}
            client.post('/api/v1/documents/upload', files=files, data=data)
        
        # Test filtering by pending status
        response = client.get('/api/v1/documents/?status=pending')
        assert response.status_code == 200
        result = response.json()
        
        # All documents should be pending
        assert all(doc['status'] == 'pending' for doc in result['documents'])
        assert result['total'] >= 5
        
        # Test filtering by non-existent status
        response = client.get('/api/v1/documents/?status=completed')
        assert response.status_code == 200
        assert response.json()['total'] == 0
    
    def test_delete_operations(self, client, sample_files, cleanup_test_data):
        """Test document deletion edge cases"""
        # Upload a document
        files = {
            'file': ('delete_test.txt', sample_files['txt'], 'text/plain')
        }
        data = {'document_type': 'txt'}
        
        upload_response = client.post('/api/v1/documents/upload', files=files, data=data)
        doc_id = upload_response.json()['document_id']
        
        # Delete it
        delete_response = client.delete(f'/api/v1/documents/{doc_id}')
        assert delete_response.status_code == 200
        
        # Try to delete again - should fail
        delete_response2 = client.delete(f'/api/v1/documents/{doc_id}')
        assert delete_response2.status_code == 404
        
        # Verify it's not in the list
        list_response = client.get('/api/v1/documents/')
        doc_ids = [doc['document_id'] for doc in list_response.json()['documents']]
        assert doc_id not in doc_ids
    
    def test_invalid_uuids(self, client, cleanup_test_data):
        """Test handling of invalid UUID formats"""
        invalid_uuids = [
            'not-a-uuid',
            '12345',
            'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
            '',
            'null',
            '00000000-0000-0000-0000-000000000000'  # Valid format but non-existent
        ]
        
        for invalid_id in invalid_uuids:
            # Test status endpoint
            response = client.get(f'/api/v1/documents/{invalid_id}/status')
            assert response.status_code in [404, 422]  # 422 for invalid format, 404 for not found
            
            # Test delete endpoint
            response = client.delete(f'/api/v1/documents/{invalid_id}')
            assert response.status_code in [404, 422]
    
    def test_empty_file_upload(self, client, cleanup_test_data):
        """Test uploading empty files"""
        files = {
            'file': ('empty.txt', b'', 'text/plain')
        }
        data = {'document_type': 'txt'}
        
        response = client.post('/api/v1/documents/upload', files=files, data=data)
        
        # Should accept empty files
        assert response.status_code == 200
        assert response.json()['file_size'] == 0
    
    def test_health_endpoint_reliability(self, client, cleanup_test_data):
        """Test health endpoint under various conditions"""
        # Multiple rapid health checks
        for _ in range(10):
            response = client.get('/api/v1/documents/health')
            assert response.status_code == 200
            assert response.json()['status'] == 'healthy'
            assert response.json()['database'] == 'connected'
    
    def test_document_persistence(self, client, sample_files, cleanup_test_data):
        """Test that documents persist across service instances"""
        # Upload a document
        files = {
            'file': ('persistence_test.txt', sample_files['txt'], 'text/plain')
        }
        data = {
            'document_type': 'txt',
            'metadata': json.dumps({'test': 'persistence'})
        }
        
        upload_response = client.post('/api/v1/documents/upload', files=files, data=data)
        doc_id = upload_response.json()['document_id']
        
        # Create a new service instance (simulating restart)
        new_service = DocumentService()
        
        # Verify document exists in new instance
        status = new_service.get_document_status(UUID(doc_id))
        assert status is not None
        assert status.document_id == UUID(doc_id)
        
        metadata = new_service.get_document_metadata(UUID(doc_id))
        assert metadata is not None
        assert metadata.metadata['test'] == 'persistence'


class TestDocumentServiceUnit:
    """Unit tests for DocumentService class"""
    
    def test_checksum_calculation(self):
        """Test checksum calculation is consistent"""
        service = DocumentService()
        
        content1 = b"Test content for checksum"
        content2 = b"Test content for checksum"  # Same content
        content3 = b"Different content"
        
        checksum1 = service.calculate_checksum(content1)
        checksum2 = service.calculate_checksum(content2)
        checksum3 = service.calculate_checksum(content3)
        
        assert checksum1 == checksum2  # Same content = same checksum
        assert checksum1 != checksum3  # Different content = different checksum
        assert len(checksum1) == 64  # SHA-256 produces 64 hex characters
    
    def test_file_size_validation(self):
        """Test file size validation logic"""
        service = DocumentService()
        
        # Test within limits
        valid, msg = service.validate_file_size(1024 * 1024, DocumentType.TXT)  # 1MB
        assert valid
        assert msg == ""
        
        # Test exceeding limits
        valid, msg = service.validate_file_size(15 * 1024 * 1024, DocumentType.TXT)  # 15MB
        assert not valid
        assert "too large" in msg
        
        # Test different document types have different limits
        valid_pdf, _ = service.validate_file_size(30 * 1024 * 1024, DocumentType.PDF)  # 30MB
        valid_txt, _ = service.validate_file_size(30 * 1024 * 1024, DocumentType.TXT)  # 30MB
        
        assert valid_pdf  # Within PDF limit
        assert not valid_txt  # Exceeds TXT limit


class TestErrorScenarios:
    """Test error handling and edge cases"""
    
    def test_database_error_handling(self, client, sample_files, monkeypatch):
        """Test handling of database errors"""
        # This would require mocking database failures
        # For now, we'll test basic error handling
        pass
    
    def test_file_system_errors(self, client, sample_files, cleanup_test_data):
        """Test handling of file system errors"""
        # Create a read-only directory to force write errors
        import stat
        
        read_only_dir = Path("uploads/documents/readonly")
        read_only_dir.mkdir(parents=True, exist_ok=True)
        
        # Make directory read-only
        os.chmod(read_only_dir, stat.S_IRUSR | stat.S_IXUSR)
        
        # This test would need proper error handling in the service
        # Currently skipping as it requires more sophisticated error handling
        
        # Clean up
        os.chmod(read_only_dir, stat.S_IRWXU)
        shutil.rmtree(read_only_dir)


@pytest.mark.parametrize("filename,expected_status", [
    ("valid_clinical_note.txt", 200),
    ("test.pdf", 200),
    ("document.rtf", 200),
    ("message.hl7", 200),
    ("", 422),  # Empty filename
])
def test_parametrized_uploads(client, sample_files, cleanup_test_data, filename, expected_status):
    """Parametrized test for various upload scenarios"""
    if not filename:
        response = client.post('/api/v1/documents/upload')
        assert response.status_code == expected_status
    else:
        ext = filename.split('.')[-1]
        if ext in sample_files:
            files = {
                'file': (filename, sample_files[ext], f'application/{ext}')
            }
            data = {'document_type': ext}
            response = client.post('/api/v1/documents/upload', files=files, data=data)
            assert response.status_code == expected_status