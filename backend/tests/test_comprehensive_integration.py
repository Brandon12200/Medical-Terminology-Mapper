#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite

This test suite validates all components of the medical terminology mapper system:
1. Document upload and processing
2. Text extraction from various formats
3. BioBERT entity extraction
4. Terminology mapping integration
5. Batch processing
6. API endpoints
"""

import pytest
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from uuid import UUID
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.v1.models.document import DocumentType, DocumentStatus
from api.v1.models.document_batch import BatchUploadStatus
from api.v1.services.document_service import DocumentService
from app.ml.biobert.biobert_service import BioBERTService
from app.standards.terminology.mapper import TerminologyMapper
from app.processing.text_extractor import TextExtractor
from app.processing.document_processor import process_document, process_batch


class TestComprehensiveIntegration:
    """Comprehensive integration tests for the entire system"""
    
    @pytest.fixture(scope="class")
    def test_dir(self):
        """Create a temporary test directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture(scope="class")
    def document_service(self, test_dir):
        """Create document service instance"""
        return DocumentService(
            upload_dir=f"{test_dir}/uploads",
            db_path=f"{test_dir}/documents.db"
        )
    
    @pytest.fixture(scope="class")
    def terminology_mapper(self):
        """Create terminology mapper instance"""
        return TerminologyMapper()
    
    @pytest.fixture(scope="class")
    def biobert_service(self, terminology_mapper):
        """Create BioBERT service with terminology mapper"""
        return BioBERTService(
            use_advanced_extractor=True,
            confidence_threshold=0.7,
            terminology_mapper=terminology_mapper
        )
    
    @pytest.fixture(scope="class")
    def text_extractor(self):
        """Create text extractor instance"""
        return TextExtractor()
    
    @pytest.fixture
    def sample_medical_text(self):
        """Sample medical text for testing"""
        return """
        PATIENT HISTORY:
        The patient is a 65-year-old male presenting with type 2 diabetes mellitus 
        and hypertension. Current medications include metformin 500mg twice daily 
        and lisinopril 10mg once daily. Recent lab tests show:
        - Fasting glucose: 180 mg/dL (elevated)
        - HbA1c: 8.5% (poorly controlled)
        - Blood pressure: 145/90 mmHg
        
        ASSESSMENT:
        1. Diabetes mellitus type 2 - poorly controlled
        2. Essential hypertension - stage 2
        3. Recommend increasing metformin to 1000mg twice daily
        4. Consider adding insulin therapy if no improvement
        
        PLAN:
        - Increase metformin dosage
        - Schedule follow-up in 3 months
        - Order comprehensive metabolic panel
        - Refer to diabetes educator
        """
    
    def test_01_document_service_initialization(self, document_service):
        """Test document service is properly initialized"""
        print("\n=== Test 1: Document Service Initialization ===")
        
        assert document_service is not None
        assert document_service.upload_dir.exists()
        assert os.path.exists(document_service.db_path)
        
        # Test database tables exist
        with document_service._get_db() as conn:
            # Check documents table
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='documents'"
            )
            assert cursor.fetchone() is not None
            
            # Check document_batches table
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='document_batches'"
            )
            assert cursor.fetchone() is not None
        
        print("✓ Document service initialized successfully")
    
    def test_02_terminology_mapper_initialization(self, terminology_mapper):
        """Test terminology mapper is properly initialized"""
        print("\n=== Test 2: Terminology Mapper Initialization ===")
        
        assert terminology_mapper is not None
        assert terminology_mapper.db_manager is not None
        
        # Test mapping a simple term
        results = terminology_mapper.map_term("diabetes", system="snomed")
        assert results is not None
        assert len(results) > 0
        assert any("diabetes" in r.get("display", "").lower() for r in results)
        
        print("✓ Terminology mapper initialized successfully")
    
    def test_03_biobert_service_initialization(self, biobert_service):
        """Test BioBERT service is properly initialized"""
        print("\n=== Test 3: BioBERT Service Initialization ===")
        
        assert biobert_service is not None
        assert biobert_service.model_manager is not None
        assert biobert_service.terminology_mapper is not None
        
        # Test basic entity extraction
        entities = biobert_service.extract_entities("Patient has diabetes")
        assert isinstance(entities, list)
        
        print("✓ BioBERT service initialized successfully")
    
    async def test_04_single_document_upload(self, document_service, sample_medical_text):
        """Test single document upload and processing"""
        print("\n=== Test 4: Single Document Upload ===")
        
        # Upload document
        response = await document_service.save_document(
            content=sample_medical_text.encode(),
            filename="test_medical_report.txt",
            document_type=DocumentType.TXT
        )
        
        assert response.document_id is not None
        assert response.status == DocumentStatus.PENDING
        assert response.file_size == len(sample_medical_text.encode())
        
        # Verify document in database
        doc_status = document_service.get_document_status(response.document_id)
        assert doc_status is not None
        assert doc_status.status == DocumentStatus.PENDING
        
        print(f"✓ Document uploaded successfully: {response.document_id}")
        return response.document_id
    
    def test_05_text_extraction(self, text_extractor, document_service, test_dir):
        """Test text extraction from various formats"""
        print("\n=== Test 5: Text Extraction ===")
        
        # Create test files
        test_files = {
            "test.txt": b"Simple text content with diabetes mention",
            "test.pdf": None,  # Would need actual PDF bytes
            "test.docx": None  # Would need actual DOCX bytes
        }
        
        for filename, content in test_files.items():
            if content is None:
                continue  # Skip formats we can't easily create
                
            filepath = Path(test_dir) / filename
            with open(filepath, 'wb') as f:
                f.write(content)
            
            # Extract text
            extracted, method, metadata = text_extractor.extract_text(
                str(filepath),
                filename.split('.')[-1]
            )
            
            assert extracted is not None
            assert len(extracted) > 0
            assert method is not None
            
            print(f"✓ Successfully extracted text from {filename} using {method}")
    
    def test_06_biobert_entity_extraction(self, biobert_service, sample_medical_text):
        """Test BioBERT entity extraction"""
        print("\n=== Test 6: BioBERT Entity Extraction ===")
        
        # Extract entities without terminology mapping
        entities = biobert_service.extract_entities(
            sample_medical_text,
            extract_context=True,
            map_to_terminologies=False
        )
        
        assert len(entities) > 0
        
        # Check for expected entity types
        entity_types = {e.entity_type for e in entities}
        expected_types = {"CONDITION", "MEDICATION", "LAB_TEST"}
        
        print(f"Found entity types: {entity_types}")
        assert len(entity_types.intersection(expected_types)) > 0
        
        # Check for specific entities
        entity_texts = {e.text.lower() for e in entities}
        expected_entities = {"diabetes", "metformin", "lisinopril", "glucose", "hba1c"}
        found_entities = entity_texts.intersection(expected_entities)
        
        print(f"Found expected entities: {found_entities}")
        assert len(found_entities) >= 3  # Should find at least 3 of the expected entities
        
        print(f"✓ Extracted {len(entities)} entities successfully")
    
    def test_07_terminology_mapping_integration(self, biobert_service, sample_medical_text):
        """Test BioBERT with terminology mapping"""
        print("\n=== Test 7: Terminology Mapping Integration ===")
        
        # Extract entities with terminology mapping
        entities = biobert_service.extract_entities(
            sample_medical_text,
            extract_context=True,
            map_to_terminologies=True
        )
        
        assert len(entities) > 0
        
        # Check that entities have terminology mappings
        mapped_entities = [e for e in entities if e.terminology_mappings]
        assert len(mapped_entities) > 0
        
        print(f"Found {len(mapped_entities)} entities with terminology mappings")
        
        # Verify correct terminology system routing
        for entity in mapped_entities:
            if entity.entity_type == "MEDICATION":
                assert "rxnorm" in entity.terminology_mappings
                print(f"✓ Medication '{entity.text}' mapped to RxNorm")
            elif entity.entity_type == "LAB_TEST":
                assert "loinc" in entity.terminology_mappings
                print(f"✓ Lab test '{entity.text}' mapped to LOINC")
            elif entity.entity_type in ["CONDITION", "PROCEDURE"]:
                assert "snomed" in entity.terminology_mappings
                print(f"✓ Condition/Procedure '{entity.text}' mapped to SNOMED")
    
    async def test_08_batch_document_upload(self, document_service):
        """Test batch document upload"""
        print("\n=== Test 8: Batch Document Upload ===")
        
        # Create batch
        batch_id = document_service.create_document_batch(
            batch_name="Test Batch",
            metadata={"test": True},
            total_documents=3
        )
        
        assert isinstance(batch_id, UUID)
        
        # Upload multiple documents
        document_ids = []
        for i in range(3):
            content = f"Test document {i}: Patient has diabetes and takes metformin"
            response = await document_service.save_document(
                content=content.encode(),
                filename=f"batch_doc_{i}.txt",
                document_type=DocumentType.TXT,
                batch_id=batch_id
            )
            document_ids.append(response.document_id)
        
        # Check batch status
        batch_status = document_service.get_batch_status(batch_id)
        assert batch_status is not None
        assert batch_status.total_documents == 3
        assert len(batch_status.documents) == 3
        
        print(f"✓ Batch created with {len(document_ids)} documents")
        return batch_id, document_ids
    
    def test_09_batch_processing_progress(self, document_service):
        """Test batch processing progress tracking"""
        print("\n=== Test 9: Batch Processing Progress ===")
        
        # Create a test batch
        batch_id = document_service.create_document_batch(
            batch_name="Progress Test",
            metadata={},
            total_documents=2
        )
        
        # Simulate processing progress
        with document_service._get_db() as conn:
            # Update batch to processing
            conn.execute(
                "UPDATE document_batches SET status = ?, started_at = ? WHERE batch_id = ?",
                (BatchUploadStatus.PROCESSING.value, datetime.utcnow().isoformat(), str(batch_id))
            )
        
        # Check status
        batch_status = document_service.get_batch_status(batch_id)
        assert batch_status.status == BatchUploadStatus.PROCESSING.value
        
        print("✓ Batch progress tracking works correctly")
    
    def test_10_comprehensive_pipeline(self, document_service, biobert_service, sample_medical_text):
        """Test complete pipeline: upload → extract → BioBERT → terminology mapping"""
        print("\n=== Test 10: Comprehensive Pipeline Test ===")
        
        async def run_pipeline():
            # Step 1: Upload document
            print("Step 1: Uploading document...")
            response = await document_service.save_document(
                content=sample_medical_text.encode(),
                filename="pipeline_test.txt",
                document_type=DocumentType.TXT
            )
            doc_id = response.document_id
            print(f"✓ Document uploaded: {doc_id}")
            
            # Step 2: Simulate text extraction (normally done by Celery)
            print("Step 2: Extracting text...")
            with document_service._get_db() as conn:
                conn.execute(
                    """UPDATE documents 
                    SET extracted_text = ?, extraction_method = ?, status = ? 
                    WHERE document_id = ?""",
                    (sample_medical_text, "direct", DocumentStatus.COMPLETED.value, str(doc_id))
                )
            print("✓ Text extracted")
            
            # Step 3: Get extracted text
            extracted = document_service.get_extracted_text(doc_id)
            assert extracted is not None
            assert extracted.text_content == sample_medical_text
            
            # Step 4: Extract entities with BioBERT
            print("Step 3: Extracting entities with BioBERT...")
            entities = biobert_service.extract_entities(
                extracted.text_content,
                extract_context=True,
                map_to_terminologies=True
            )
            print(f"✓ Extracted {len(entities)} entities")
            
            # Step 5: Verify terminology mappings
            print("Step 4: Verifying terminology mappings...")
            mapped_count = sum(1 for e in entities if e.terminology_mappings)
            print(f"✓ {mapped_count} entities have terminology mappings")
            
            # Print summary
            print("\n=== Pipeline Summary ===")
            print(f"Document ID: {doc_id}")
            print(f"Text length: {len(sample_medical_text)} characters")
            print(f"Entities found: {len(entities)}")
            print(f"Entities with mappings: {mapped_count}")
            
            # Print entity details
            print("\n=== Entity Details ===")
            for entity in entities[:5]:  # Show first 5 entities
                print(f"- {entity.entity_type}: '{entity.text}' (confidence: {entity.confidence:.2f})")
                if entity.terminology_mappings:
                    for system, mappings in entity.terminology_mappings.items():
                        if mappings:
                            print(f"  → {system}: {mappings[0].get('display', 'N/A')}")
        
        # Run the async pipeline
        asyncio.run(run_pipeline())
        print("\n✓ Complete pipeline test passed")
    
    def test_11_error_handling(self, document_service):
        """Test error handling across components"""
        print("\n=== Test 11: Error Handling ===")
        
        # Test invalid document type
        async def test_invalid_upload():
            try:
                await document_service.save_document(
                    content=b"test",
                    filename="test.invalid",
                    document_type=DocumentType.PDF  # Mismatch
                )
                assert False, "Should have raised an error"
            except ValueError:
                print("✓ Correctly rejected invalid document type")
        
        asyncio.run(test_invalid_upload())
        
        # Test non-existent document
        status = document_service.get_document_status(UUID("00000000-0000-0000-0000-000000000000"))
        assert status is None
        print("✓ Correctly handled non-existent document")
        
        # Test non-existent batch
        batch_status = document_service.get_batch_status(UUID("00000000-0000-0000-0000-000000000000"))
        assert batch_status is None
        print("✓ Correctly handled non-existent batch")
    
    def test_12_performance_check(self, biobert_service):
        """Basic performance check"""
        print("\n=== Test 12: Performance Check ===")
        
        # Test entity extraction performance
        test_text = "Patient has diabetes. " * 50  # Repeat to create longer text
        
        start_time = time.time()
        entities = biobert_service.extract_entities(test_text, map_to_terminologies=False)
        extraction_time = time.time() - start_time
        
        print(f"Extracted {len(entities)} entities from {len(test_text)} chars in {extraction_time:.2f}s")
        print(f"Performance: {len(test_text) / extraction_time:.0f} chars/second")
        
        # Basic performance assertion (should process at least 100 chars/second)
        assert len(test_text) / extraction_time > 100
        print("✓ Performance is acceptable")


def main():
    """Run all tests"""
    print("=" * 80)
    print("COMPREHENSIVE INTEGRATION TEST SUITE")
    print("=" * 80)
    
    # Create test instance
    test_suite = TestComprehensiveIntegration()
    
    # Create fixtures
    with tempfile.TemporaryDirectory() as test_dir:
        document_service = DocumentService(
            upload_dir=f"{test_dir}/uploads",
            db_path=f"{test_dir}/documents.db"
        )
        terminology_mapper = TerminologyMapper()
        biobert_service = BioBERTService(
            use_advanced_extractor=True,
            confidence_threshold=0.7,
            terminology_mapper=terminology_mapper
        )
        text_extractor = TextExtractor()
        
        sample_medical_text = test_suite.sample_medical_text(None)
        
        # Run tests in order
        try:
            test_suite.test_01_document_service_initialization(document_service)
            test_suite.test_02_terminology_mapper_initialization(terminology_mapper)
            test_suite.test_03_biobert_service_initialization(biobert_service)
            
            # Async tests
            doc_id = asyncio.run(test_suite.test_04_single_document_upload(document_service, sample_medical_text))
            
            test_suite.test_05_text_extraction(text_extractor, document_service, test_dir)
            test_suite.test_06_biobert_entity_extraction(biobert_service, sample_medical_text)
            test_suite.test_07_terminology_mapping_integration(biobert_service, sample_medical_text)
            
            batch_id, doc_ids = asyncio.run(test_suite.test_08_batch_document_upload(document_service))
            
            test_suite.test_09_batch_processing_progress(document_service)
            test_suite.test_10_comprehensive_pipeline(document_service, biobert_service, sample_medical_text)
            test_suite.test_11_error_handling(document_service)
            test_suite.test_12_performance_check(biobert_service)
            
            print("\n" + "=" * 80)
            print("✅ ALL TESTS PASSED!")
            print("=" * 80)
            
        except Exception as e:
            print("\n" + "=" * 80)
            print(f"❌ TEST FAILED: {str(e)}")
            print("=" * 80)
            raise


if __name__ == "__main__":
    main()