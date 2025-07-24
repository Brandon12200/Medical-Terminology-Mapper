"""
Performance tests for document upload API
"""

import pytest
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
import random
import string

from api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_medical_text():
    """Generate sample medical text of various sizes"""
    base_text = """
Patient presents with acute exacerbation of chronic obstructive pulmonary disease.
History significant for 40 pack-year smoking history, diabetes mellitus type 2,
and hypertension. Current medications include albuterol, metformin, and lisinopril.
Physical examination reveals decreased breath sounds bilaterally with expiratory wheezes.
Laboratory results show elevated white blood cell count and C-reactive protein.
Chest X-ray demonstrates hyperinflation consistent with COPD.
Treatment plan includes bronchodilators, corticosteroids, and oxygen therapy.
Patient advised on smoking cessation and pulmonary rehabilitation.
"""
    
    def generate_text(size_kb):
        target_size = size_kb * 1024
        text = base_text
        while len(text.encode()) < target_size:
            text += base_text + f" Additional content {random.randint(1000, 9999)}.\n"
        return text[:target_size].encode()
    
    return generate_text


class TestDocumentUploadPerformance:
    """Performance tests for document upload functionality"""
    
    def test_upload_response_time(self, client, sample_medical_text):
        """Test upload response times for different file sizes"""
        sizes = [1, 5, 10, 50, 100]  # KB
        results = {}
        
        for size in sizes:
            content = sample_medical_text(size)
            
            files = {
                'file': (f'perf_test_{size}kb.txt', content, 'text/plain')
            }
            data = {'document_type': 'txt'}
            
            start_time = time.time()
            response = client.post('/api/v1/documents/upload', files=files, data=data)
            end_time = time.time()
            
            assert response.status_code == 200
            
            upload_time = end_time - start_time
            results[size] = upload_time
            
            print(f"Upload {size}KB: {upload_time:.3f}s")
        
        # Verify response times are reasonable (< 5 seconds for files up to 100KB)
        for size, time_taken in results.items():
            assert time_taken < 5.0, f"{size}KB upload took {time_taken:.3f}s"
    
    def test_concurrent_upload_performance(self, client, sample_medical_text):
        """Test performance under concurrent load"""
        num_concurrent = 10
        file_size = 10  # KB
        
        def upload_file(index):
            content = sample_medical_text(file_size)
            files = {
                'file': (f'concurrent_{index}.txt', content, 'text/plain')
            }
            data = {'document_type': 'txt'}
            
            start_time = time.time()
            response = client.post('/api/v1/documents/upload', files=files, data=data)
            end_time = time.time()
            
            return {
                'index': index,
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'success': response.status_code == 200
            }
        
        # Execute concurrent uploads
        start_total = time.time()
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(upload_file, i) for i in range(num_concurrent)]
            results = [future.result() for future in as_completed(futures)]
        end_total = time.time()
        
        # Analyze results
        total_time = end_total - start_total
        success_count = sum(1 for r in results if r['success'])
        response_times = [r['response_time'] for r in results if r['success']]
        
        print(f"Concurrent uploads: {success_count}/{num_concurrent} successful")
        print(f"Total time: {total_time:.3f}s")
        print(f"Average response time: {statistics.mean(response_times):.3f}s")
        print(f"Max response time: {max(response_times):.3f}s")
        
        # Performance assertions
        assert success_count == num_concurrent, "Not all uploads succeeded"
        assert statistics.mean(response_times) < 10.0, "Average response time too high"
        assert max(response_times) < 30.0, "Max response time too high"
    
    def test_api_endpoint_response_times(self, client, sample_medical_text):
        """Test response times for various API endpoints"""
        # First upload some documents
        doc_ids = []
        for i in range(5):
            content = sample_medical_text(5)
            files = {
                'file': (f'api_test_{i}.txt', content, 'text/plain')
            }
            data = {'document_type': 'txt'}
            
            response = client.post('/api/v1/documents/upload', files=files, data=data)
            if response.status_code == 200:
                doc_ids.append(response.json()['document_id'])
        
        # Test various endpoint response times
        endpoints = [
            ('GET', '/api/v1/documents/health'),
            ('GET', '/api/v1/documents/'),
            ('GET', f'/api/v1/documents/{doc_ids[0]}/status'),
            ('GET', f'/api/v1/documents/{doc_ids[0]}/metadata'),
            ('GET', '/api/v1/documents/?page=1&page_size=10'),
        ]
        
        for method, endpoint in endpoints:
            start_time = time.time()
            if method == 'GET':
                response = client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"{method} {endpoint}: {response_time:.3f}s")
            
            # All read operations should be fast
            assert response_time < 2.0, f"{endpoint} too slow: {response_time:.3f}s"
            assert response.status_code in [200, 404]  # 404 acceptable for some cases
    
    def test_database_performance(self, client, sample_medical_text):
        """Test database operations under load"""
        # Upload many documents
        num_documents = 50
        doc_ids = []
        
        start_time = time.time()
        for i in range(num_documents):
            content = sample_medical_text(2)  # Small files for speed
            files = {
                'file': (f'db_test_{i}.txt', content, 'text/plain')
            }
            data = {
                'document_type': 'txt',
                'metadata': json.dumps({
                    'test_id': i,
                    'batch': 'performance_test',
                    'timestamp': time.time()
                })
            }
            
            response = client.post('/api/v1/documents/upload', files=files, data=data)
            if response.status_code == 200:
                doc_ids.append(response.json()['document_id'])
        
        upload_time = time.time() - start_time
        print(f"Uploaded {len(doc_ids)} documents in {upload_time:.3f}s")
        
        # Test listing performance with many documents
        start_time = time.time()
        response = client.get('/api/v1/documents/?page_size=50')
        list_time = time.time() - start_time
        
        assert response.status_code == 200
        print(f"Listed documents in {list_time:.3f}s")
        
        # Test individual document lookups
        lookup_times = []
        for doc_id in doc_ids[:10]:  # Test first 10
            start_time = time.time()
            response = client.get(f'/api/v1/documents/{doc_id}/status')
            lookup_time = time.time() - start_time
            lookup_times.append(lookup_time)
            assert response.status_code == 200
        
        avg_lookup_time = statistics.mean(lookup_times)
        print(f"Average lookup time: {avg_lookup_time:.3f}s")
        
        # Performance assertions
        assert upload_time < 60.0, "Uploads took too long"
        assert list_time < 5.0, "Listing took too long"
        assert avg_lookup_time < 1.0, "Lookups took too long"
    
    def test_memory_usage_stability(self, client, sample_medical_text):
        """Test that memory usage remains stable during operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Upload many documents to test memory stability
        for i in range(20):
            content = sample_medical_text(10)  # 10KB files
            files = {
                'file': (f'memory_test_{i}.txt', content, 'text/plain')
            }
            data = {'document_type': 'txt'}
            
            response = client.post('/api/v1/documents/upload', files=files, data=data)
            assert response.status_code == 200
            
            # Check memory usage every 5 uploads
            if i % 5 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                print(f"After {i+1} uploads: {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
                
                # Memory increase should be reasonable
                assert memory_increase < 100, f"Memory usage increased by {memory_increase:.1f}MB"
    
    def test_error_handling_performance(self, client):
        """Test that error responses are fast"""
        error_tests = [
            # Missing file
            {'files': {}, 'data': {'document_type': 'txt'}},
            # Invalid document type
            {'files': {'file': ('test.txt', b'content', 'text/plain')}, 
             'data': {'document_type': 'invalid'}},
            # Mismatched extension
            {'files': {'file': ('test.pdf', b'content', 'text/plain')}, 
             'data': {'document_type': 'txt'}},
        ]
        
        for test_case in error_tests:
            start_time = time.time()
            response = client.post('/api/v1/documents/upload', 
                                 files=test_case.get('files', {}), 
                                 data=test_case.get('data', {}))
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Error responses should be fast
            assert response_time < 1.0, f"Error response too slow: {response_time:.3f}s"
            assert response.status_code in [400, 422]


class TestStressTest:
    """Stress tests for extreme scenarios"""
    
    @pytest.mark.slow
    def test_large_file_upload(self, client, sample_medical_text):
        """Test uploading large files (near size limits)"""
        # Test near the TXT limit (10MB)
        large_content = sample_medical_text(9 * 1024)  # 9MB
        
        files = {
            'file': ('large_test.txt', large_content, 'text/plain')
        }
        data = {'document_type': 'txt'}
        
        start_time = time.time()
        response = client.post('/api/v1/documents/upload', files=files, data=data)
        end_time = time.time()
        
        assert response.status_code == 200
        upload_time = end_time - start_time
        print(f"9MB upload time: {upload_time:.3f}s")
        
        # Should complete within reasonable time
        assert upload_time < 30.0, f"Large file upload too slow: {upload_time:.3f}s"
    
    @pytest.mark.slow 
    def test_rapid_sequential_uploads(self, client, sample_medical_text):
        """Test rapid sequential uploads"""
        num_uploads = 100
        content = sample_medical_text(1)  # 1KB files for speed
        
        start_time = time.time()
        successful_uploads = 0
        
        for i in range(num_uploads):
            files = {
                'file': (f'rapid_{i}.txt', content + f' {i}'.encode(), 'text/plain')
            }
            data = {'document_type': 'txt'}
            
            response = client.post('/api/v1/documents/upload', files=files, data=data)
            if response.status_code == 200:
                successful_uploads += 1
        
        total_time = time.time() - start_time
        throughput = successful_uploads / total_time
        
        print(f"Rapid uploads: {successful_uploads}/{num_uploads} successful")
        print(f"Throughput: {throughput:.2f} uploads/second")
        print(f"Total time: {total_time:.3f}s")
        
        # Should handle at least 80% successfully
        assert successful_uploads >= num_uploads * 0.8
        # Should achieve reasonable throughput
        assert throughput >= 5.0, f"Throughput too low: {throughput:.2f} uploads/sec"


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-s"])