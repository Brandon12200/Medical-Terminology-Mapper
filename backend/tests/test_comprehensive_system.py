"""
Comprehensive system test for Medical Terminology Mapper
Tests all features from Weeks 1-6 of implementation
"""
import pytest
import os
import json
import time
from pathlib import Path
from datetime import datetime
import asyncio
from typing import Dict, List, Any

# Test configuration
TEST_DIR = Path(__file__).parent
SAMPLE_FILES_DIR = TEST_DIR / "test_files"
BACKEND_DIR = TEST_DIR.parent
os.chdir(BACKEND_DIR)

# Add backend to path
import sys
sys.path.insert(0, str(BACKEND_DIR))

from app.utils.logger import setup_logger

logger = setup_logger("comprehensive_test")


class TestReport:
    """Collects and formats test results"""
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
    
    def add_test(self, name: str, status: str, details: Dict = None, error: str = None):
        self.results["tests"][name] = {
            "status": status,
            "details": details or {},
            "error": error
        }
        self.results["summary"]["total"] += 1
        self.results["summary"][status] += 1
    
    def print_report(self):
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST REPORT")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"\nSummary:")
        print(f"  Total Tests: {self.results['summary']['total']}")
        print(f"  Passed: {self.results['summary']['passed']} ✓")
        print(f"  Failed: {self.results['summary']['failed']} ✗")
        print(f"  Skipped: {self.results['summary']['skipped']} ⚠")
        
        print("\nDetailed Results:")
        for test_name, result in self.results["tests"].items():
            status_symbol = "✓" if result["status"] == "passed" else "✗" if result["status"] == "failed" else "⚠"
            print(f"\n{status_symbol} {test_name}")
            if result["details"]:
                for key, value in result["details"].items():
                    print(f"    {key}: {value}")
            if result["error"]:
                print(f"    ERROR: {result['error']}")
        print("\n" + "="*80)


# Initialize test report
report = TestReport()


def test_document_service():
    """Test Week 1-2: Document Service and Database"""
    test_name = "Document Service Initialization"
    try:
        from api.v1.services.document_service import DocumentService
        
        service = DocumentService()
        
        # Test database connection
        with service._get_db() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
        
        # Check required tables exist
        required_tables = ['documents', 'extracted_text']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            report.add_test(test_name, "failed", 
                          {"missing_tables": missing_tables},
                          f"Missing required tables: {missing_tables}")
        else:
            report.add_test(test_name, "passed", 
                          {"tables_found": len(tables),
                           "upload_dir": str(service.upload_dir)})
        
    except Exception as e:
        report.add_test(test_name, "failed", error=str(e))


def test_text_extractor():
    """Test Week 1-2: Text Extraction"""
    test_name = "Text Extractor Service"
    try:
        from app.processing.text_extractor import DocumentTextExtractor
        
        extractor = DocumentTextExtractor()
        
        # Test simple text extraction
        test_text = "This is a test medical document with diabetes and hypertension."
        test_file = SAMPLE_FILES_DIR / "test.txt"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text(test_text)
        
        result = extractor.extract_text(str(test_file), "txt")
        
        if result["success"] and test_text in result["text"]:
            report.add_test(test_name, "passed", 
                          {"extraction_method": result["extraction_method"],
                           "text_length": len(result["text"])})
        else:
            report.add_test(test_name, "failed", 
                          {"success": result["success"]},
                          result.get("error"))
        
    except Exception as e:
        report.add_test(test_name, "failed", error=str(e))


def test_biobert_model_manager():
    """Test Week 3-4: BioBERT Model Manager"""
    test_name = "BioBERT Model Manager"
    try:
        from app.ml.biobert.model_manager import get_biobert_manager
        
        manager = get_biobert_manager()
        info = manager.get_model_info()
        
        # Test model loading
        test_text = "Patient has diabetes mellitus type 2"
        entities = manager.extract_entities(test_text)
        
        report.add_test(test_name, "passed", 
                      {"model_name": info["model_name"],
                       "device": info["device"],
                       "entities_found": len(entities),
                       "ready": info["ready"]})
        
    except Exception as e:
        report.add_test(test_name, "failed", error=str(e))


def test_biobert_service():
    """Test Week 3-4: BioBERT Service"""
    test_name = "BioBERT Service"
    try:
        from app.ml.biobert.biobert_service import BioBERTService
        
        service = BioBERTService(use_advanced_extractor=False)
        
        test_text = """
        The patient is a 65-year-old male with diabetes and hypertension.
        Current medications include metformin 500mg twice daily.
        Lab results show glucose 180 mg/dL.
        """
        
        entities = service.extract_entities(test_text)
        
        # Check entity types
        entity_types = {e.entity_type for e in entities}
        expected_types = {"CONDITION", "MEDICATION", "LAB_TEST"}
        
        if expected_types.issubset(entity_types):
            report.add_test(test_name, "passed", 
                          {"total_entities": len(entities),
                           "entity_types": list(entity_types),
                           "confidence_threshold": service.confidence_threshold})
        else:
            report.add_test(test_name, "failed",
                          {"found_types": list(entity_types),
                           "expected_types": list(expected_types)})
        
    except Exception as e:
        report.add_test(test_name, "failed", error=str(e))


def test_medical_entity_extractor():
    """Test Week 5-6: Advanced Medical Entity Extractor"""
    test_name = "Medical Entity Extractor"
    try:
        from app.ml.medical_entity_extractor import (
            MedicalEntityExtractor, 
            NegationDetector,
            UncertaintyDetector,
            EntityLinker
        )
        
        # Test components individually first
        negation_detector = NegationDetector()
        uncertainty_detector = UncertaintyDetector()
        entity_linker = EntityLinker()
        
        # Test full extractor
        extractor = MedicalEntityExtractor(use_crf=False)  # Disable CRF for testing
        
        test_text = """
        Patient denies chest pain but reports shortness of breath.
        Possible pneumonia on chest x-ray.
        Started on aspirin 81mg daily and metformin 500mg twice daily.
        Physical exam shows swelling in left knee.
        """
        
        entities = extractor.extract_entities(test_text)
        
        # Check for various features
        negated_entities = [e for e in entities if e.negated]
        uncertain_entities = [e for e in entities if e.uncertain]
        linked_entities = [e for e in entities if e.linked_id]
        dosage_entities = [e for e in entities if e.type.value == "DOSAGE"]
        frequency_entities = [e for e in entities if e.type.value == "FREQUENCY"]
        anatomy_entities = [e for e in entities if e.type.value == "ANATOMY"]
        
        details = {
            "total_entities": len(entities),
            "negated": len(negated_entities),
            "uncertain": len(uncertain_entities),
            "linked": len(linked_entities),
            "dosages": len(dosage_entities),
            "frequencies": len(frequency_entities),
            "anatomy": len(anatomy_entities)
        }
        
        # Check if key features are working
        if (negated_entities and uncertain_entities and 
            dosage_entities and frequency_entities and anatomy_entities):
            report.add_test(test_name, "passed", details)
        else:
            report.add_test(test_name, "failed", details,
                          "Some entity types or features not detected")
        
    except Exception as e:
        report.add_test(test_name, "failed", error=str(e))


def test_advanced_biobert_integration():
    """Test Week 5-6: Advanced BioBERT Service Integration"""
    test_name = "Advanced BioBERT Integration"
    try:
        from app.ml.biobert.biobert_service import BioBERTService
        
        service = BioBERTService(use_advanced_extractor=True)
        
        test_text = """
        Patient presents with severe headache and fever.
        No evidence of meningitis.
        Started on acetaminophen 650mg every 6 hours for fever control.
        MRI shows possible tumor in brain.
        """
        
        entities = service.extract_entities(test_text)
        
        # Check for advanced features
        negated = [e for e in entities if e.attributes and e.attributes.get("negated")]
        uncertain = [e for e in entities if e.attributes and e.attributes.get("uncertain")]
        dosages = [e for e in entities if e.entity_type == "DOSAGE"]
        frequencies = [e for e in entities if e.entity_type == "FREQUENCY"]
        
        details = {
            "total_entities": len(entities),
            "negated": len(negated),
            "uncertain": len(uncertain),
            "dosages": len(dosages),
            "frequencies": len(frequencies),
            "source": entities[0].source if entities else "none"
        }
        
        if negated and uncertain:
            report.add_test(test_name, "passed", details)
        else:
            report.add_test(test_name, "failed", details,
                          "Advanced features not working properly")
        
    except Exception as e:
        report.add_test(test_name, "failed", error=str(e))


async def test_api_endpoints():
    """Test API endpoints"""
    test_name = "API Endpoints"
    try:
        from fastapi.testclient import TestClient
        from api.main import app
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/api/v1/documents/health")
        health_ok = response.status_code == 200
        
        # Test document upload
        test_content = b"Patient has diabetes and takes metformin 500mg twice daily."
        files = {"file": ("test.txt", test_content, "text/plain")}
        data = {"document_type": "txt"}
        
        response = client.post("/api/v1/documents/upload", files=files, data=data)
        upload_ok = response.status_code == 200
        
        if upload_ok:
            doc_id = response.json()["document_id"]
            
            # Wait for processing
            time.sleep(2)
            
            # Test status endpoint
            response = client.get(f"/api/v1/documents/{doc_id}/status")
            status_ok = response.status_code == 200
            
            # Test text extraction endpoint
            response = client.get(f"/api/v1/documents/{doc_id}/text")
            text_ok = response.status_code in [200, 202]  # 202 if still processing
            
            # Test entity extraction endpoint
            response = client.get(f"/api/v1/documents/{doc_id}/extract-entities")
            entities_ok = response.status_code in [200, 202, 422]  # 422 if not processed yet
            
            details = {
                "health_check": health_ok,
                "upload": upload_ok,
                "status_check": status_ok,
                "text_extraction": text_ok,
                "entity_extraction": entities_ok
            }
            
            if all(details.values()):
                report.add_test(test_name, "passed", details)
            else:
                report.add_test(test_name, "failed", details,
                              "Some endpoints failed")
        else:
            report.add_test(test_name, "failed", 
                          {"upload_status": response.status_code},
                          "Document upload failed")
        
    except Exception as e:
        report.add_test(test_name, "failed", error=str(e))


def test_comprehensive_document_processing():
    """Test complete document processing pipeline"""
    test_name = "Complete Document Processing Pipeline"
    try:
        from api.v1.services.document_service import DocumentService
        from app.processing.text_extractor import DocumentTextExtractor
        from app.ml.biobert.biobert_service import BioBERTService
        
        # Create services
        doc_service = DocumentService()
        text_extractor = DocumentTextExtractor()
        biobert_service = BioBERTService(use_advanced_extractor=True)
        
        # Create test document
        test_content = """
        CLINICAL NOTES
        
        Chief Complaint: Chest pain and shortness of breath
        
        History of Present Illness:
        The patient is a 68-year-old female with a history of diabetes mellitus type 2,
        hypertension, and hyperlipidemia who presents with acute onset chest pain.
        She denies any recent trauma. No evidence of myocardial infarction on EKG.
        
        Current Medications:
        - Metformin 1000mg twice daily
        - Lisinopril 20mg once daily  
        - Atorvastatin 40mg at bedtime
        - Aspirin 81mg daily
        
        Laboratory Results:
        - Glucose: 156 mg/dL (elevated)
        - HbA1c: 7.8%
        - Troponin: negative
        - BNP: 89 pg/mL
        
        Assessment:
        Possible unstable angina. Rule out coronary artery disease.
        Continue current medications. Add nitroglycerin as needed for chest pain.
        
        Physical Examination:
        Heart: Regular rate and rhythm, no murmurs
        Lungs: Clear to auscultation bilaterally
        Abdomen: Soft, non-tender
        Extremities: No edema in legs or ankles
        """
        
        # Save document
        import uuid
        from api.v1.models.document import DocumentType
        
        test_file = SAMPLE_FILES_DIR / "clinical_notes.txt"
        test_file.write_text(test_content)
        
        response = doc_service.save_document(
            content=test_content.encode(),
            filename="clinical_notes.txt",
            document_type=DocumentType.TXT,
            metadata={"test": True}
        )
        
        doc_id = response.document_id
        
        # Extract text
        extraction_result = text_extractor.extract_text(str(test_file), "txt")
        
        # Extract entities
        entities = biobert_service.extract_entities(extraction_result["text"])
        
        # Analyze results
        entity_summary = {}
        negated_conditions = []
        uncertain_conditions = []
        medications_with_dosage = []
        
        for entity in entities:
            # Count by type
            entity_type = entity.entity_type
            entity_summary[entity_type] = entity_summary.get(entity_type, 0) + 1
            
            # Check negated conditions
            if entity_type == "CONDITION" and entity.attributes and entity.attributes.get("negated"):
                negated_conditions.append(entity.text)
            
            # Check uncertain conditions  
            if entity_type == "CONDITION" and entity.attributes and entity.attributes.get("uncertain"):
                uncertain_conditions.append(entity.text)
            
            # Check medications
            if entity_type == "MEDICATION":
                medications_with_dosage.append(entity.text)
        
        details = {
            "document_id": str(doc_id),
            "text_extracted": len(extraction_result["text"]),
            "total_entities": len(entities),
            "entity_types": entity_summary,
            "negated_conditions": len(negated_conditions),
            "uncertain_conditions": len(uncertain_conditions),
            "medications_found": len(medications_with_dosage)
        }
        
        # Verify key extractions
        expected_medications = ["metformin", "lisinopril", "atorvastatin", "aspirin"]
        found_medications = [e.normalized_text for e in entities if e.entity_type == "MEDICATION"]
        medications_ok = all(med in " ".join(found_medications).lower() for med in expected_medications)
        
        if medications_ok and negated_conditions and uncertain_conditions:
            report.add_test(test_name, "passed", details)
        else:
            report.add_test(test_name, "failed", details,
                          "Not all expected entities were extracted")
        
    except Exception as e:
        report.add_test(test_name, "failed", error=str(e))


def test_performance():
    """Test performance metrics"""
    test_name = "Performance Testing"
    try:
        from app.ml.biobert.biobert_service import BioBERTService
        import time
        
        service = BioBERTService(use_advanced_extractor=True)
        
        # Test different text lengths
        short_text = "Patient has diabetes."
        medium_text = short_text * 50
        long_text = short_text * 200
        
        # Time extraction
        times = {}
        
        start = time.time()
        entities_short = service.extract_entities(short_text)
        times["short"] = time.time() - start
        
        start = time.time()
        entities_medium = service.extract_entities(medium_text)
        times["medium"] = time.time() - start
        
        start = time.time()
        entities_long = service.extract_entities(long_text)
        times["long"] = time.time() - start
        
        details = {
            "short_text_time": f"{times['short']:.3f}s",
            "medium_text_time": f"{times['medium']:.3f}s",
            "long_text_time": f"{times['long']:.3f}s",
            "short_entities": len(entities_short),
            "medium_entities": len(entities_medium),
            "long_entities": len(entities_long)
        }
        
        # Check if performance is reasonable (less than 10s for long text)
        if times["long"] < 10:
            report.add_test(test_name, "passed", details)
        else:
            report.add_test(test_name, "failed", details,
                          "Performance too slow for long texts")
        
    except Exception as e:
        report.add_test(test_name, "failed", error=str(e))


async def run_all_tests():
    """Run all tests in sequence"""
    print("Starting comprehensive system test...")
    print("This may take several minutes as models are loaded...\n")
    
    # Week 1-2 Tests
    print("Testing Week 1-2 features (Document handling)...")
    test_document_service()
    test_text_extractor()
    
    # Week 3-4 Tests
    print("Testing Week 3-4 features (BioBERT setup)...")
    test_biobert_model_manager()
    test_biobert_service()
    
    # Week 5-6 Tests
    print("Testing Week 5-6 features (Advanced NER)...")
    test_medical_entity_extractor()
    test_advanced_biobert_integration()
    
    # Integration Tests
    print("Testing API endpoints...")
    await test_api_endpoints()
    
    print("Testing complete pipeline...")
    await test_comprehensive_document_processing()
    
    print("Testing performance...")
    test_performance()
    
    # Print report
    report.print_report()
    
    # Save report
    report_file = TEST_DIR / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report.results, f, indent=2)
    print(f"\nReport saved to: {report_file}")


if __name__ == "__main__":
    # Create test files directory
    SAMPLE_FILES_DIR.mkdir(exist_ok=True)
    
    # Run tests
    asyncio.run(run_all_tests())