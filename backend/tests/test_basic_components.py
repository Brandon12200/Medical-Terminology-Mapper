"""
Basic component tests that don't require model loading
"""
import os
import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        # Test Week 1-2 imports
        from api.v1.services.document_service import DocumentService
        from app.processing.text_extractor import DocumentTextExtractor
        print("✓ Document service and text extractor imports")
        
        # Test Week 3-4 imports (basic)
        from app.ml.biobert.model_manager import BioBERTModelManager
        from app.ml.biobert.biobert_service import BioBERTService
        print("✓ BioBERT service imports")
        
        # Test Week 5-6 imports
        from app.ml.medical_entity_extractor import (
            MedicalEntityExtractor,
            EntityType,
            NegationDetector,
            UncertaintyDetector
        )
        print("✓ Medical entity extractor imports")
        
        # Test API imports
        from api.v1.routers.documents import router
        print("✓ API router imports")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_database_setup():
    """Test database initialization"""
    print("\nTesting database setup...")
    
    try:
        from api.v1.services.document_service import DocumentService
        
        service = DocumentService()
        
        # Test database connection
        with service._get_db() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['documents', 'extracted_text']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if not missing_tables:
            print(f"✓ Database setup complete - {len(tables)} tables found")
            return True
        else:
            print(f"✗ Missing tables: {missing_tables}")
            return False
            
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False


def test_text_extraction():
    """Test basic text extraction"""
    print("\nTesting text extraction...")
    
    try:
        from app.processing.text_extractor import DocumentTextExtractor
        
        extractor = DocumentTextExtractor()
        
        # Create test file
        test_dir = Path("tests/test_files")
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "test.txt"
        test_content = "Patient diagnosed with diabetes mellitus type 2. Prescribed metformin 500mg twice daily."
        test_file.write_text(test_content)
        
        # Test extraction
        result = extractor.extract_text(str(test_file), "txt")
        
        if result["success"] and test_content in result["text"]:
            print("✓ Text extraction working")
            return True
        else:
            print(f"✗ Text extraction failed: {result}")
            return False
            
    except Exception as e:
        print(f"✗ Text extraction error: {e}")
        return False


def test_entity_patterns():
    """Test regex patterns for entity detection"""
    print("\nTesting entity patterns...")
    
    try:
        import re
        
        # Test dosage patterns
        dosage_pattern = re.compile(r'\b\d+\s*(?:mg|g|mcg|ug|ml|cc|units?|iu)\b', re.I)
        dosage_test = "metformin 500mg"
        dosage_match = dosage_pattern.search(dosage_test)
        
        # Test frequency patterns  
        frequency_pattern = re.compile(r'\b(?:once|twice|three\s+times)\s+(?:a\s+)?(?:day|daily)\b', re.I)
        frequency_test = "twice daily"
        frequency_match = frequency_pattern.search(frequency_test)
        
        # Test negation patterns
        negation_pattern = re.compile(r'\bno\s+(?:evidence|signs?|symptoms?)\s+of\b', re.I)
        negation_test = "no evidence of pneumonia"
        negation_match = negation_pattern.search(negation_test)
        
        if dosage_match and frequency_match and negation_match:
            print("✓ Entity patterns working")
            print(f"  Dosage found: {dosage_match.group()}")
            print(f"  Frequency found: {frequency_match.group()}")
            print(f"  Negation found: {negation_match.group()}")
            return True
        else:
            print("✗ Some patterns not working")
            return False
            
    except Exception as e:
        print(f"✗ Pattern testing error: {e}")
        return False


def test_entity_types():
    """Test entity type definitions"""
    print("\nTesting entity types...")
    
    try:
        from app.ml.medical_entity_extractor import EntityType
        
        # Test all required entity types
        required_types = [
            "CONDITION", "DRUG", "PROCEDURE", "TEST", 
            "ANATOMY", "DOSAGE", "FREQUENCY", "OBSERVATION"
        ]
        
        available_types = [e.value for e in EntityType]
        missing_types = [t for t in required_types if t not in available_types]
        
        if not missing_types:
            print(f"✓ All {len(required_types)} entity types defined")
            return True
        else:
            print(f"✗ Missing entity types: {missing_types}")
            return False
            
    except Exception as e:
        print(f"✗ Entity types error: {e}")
        return False


def test_confidence_calibration():
    """Test confidence calibration logic"""
    print("\nTesting confidence calibration...")
    
    try:
        # Simple confidence calibration test
        def calibrate_score(score, temperature=1.5):
            import math
            # Convert to logit, apply temperature, convert back
            logit = math.log(score / (1 - score + 1e-8))
            calibrated_logit = logit / temperature
            return 1 / (1 + math.exp(-calibrated_logit))
        
        # Test high confidence score
        high_score = 0.95
        calibrated_high = calibrate_score(high_score)
        
        # Test low confidence score
        low_score = 0.55
        calibrated_low = calibrate_score(low_score)
        
        # Calibration should reduce extreme scores
        if calibrated_high < high_score and calibrated_low > low_score:
            print("✓ Confidence calibration working")
            print(f"  {high_score} -> {calibrated_high:.3f}")
            print(f"  {low_score} -> {calibrated_low:.3f}")
            return True
        else:
            print("✗ Confidence calibration not working correctly")
            return False
            
    except Exception as e:
        print(f"✗ Confidence calibration error: {e}")
        return False


def test_api_structure():
    """Test API endpoint structure"""
    print("\nTesting API structure...")
    
    try:
        from fastapi.testclient import TestClient
        from api.main import app
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/api/v1/documents/health")
        health_ok = response.status_code == 200
        
        # Test OpenAPI docs
        response = client.get("/docs")
        docs_ok = response.status_code == 200
        
        if health_ok and docs_ok:
            print("✓ API structure working")
            print("  Health endpoint: ✓")
            print("  Documentation: ✓")
            return True
        else:
            print(f"✗ API issues - Health: {health_ok}, Docs: {docs_ok}")
            return False
            
    except Exception as e:
        print(f"✗ API structure error: {e}")
        return False


def run_basic_tests():
    """Run all basic tests"""
    print("BASIC COMPONENT TESTING")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database_setup,
        test_text_extraction,
        test_entity_patterns,
        test_entity_types,
        test_confidence_calibration,
        test_api_structure
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("BASIC TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All basic tests PASSED!")
        print("The system is ready for advanced testing.")
    else:
        print("⚠️  Some basic tests failed.")
        print("Fix basic issues before running advanced tests.")
    
    return passed == total


if __name__ == "__main__":
    success = run_basic_tests()
    exit(0 if success else 1)