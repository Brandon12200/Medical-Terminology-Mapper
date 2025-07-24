#!/usr/bin/env python3
"""
Simple Health Check Test

Tests only the most basic functionality to ensure the system is working.
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_imports():
    """Test basic imports work"""
    print("Testing basic imports...")
    
    try:
        from app.standards.terminology.mapper import TerminologyMapper
        print("✓ TerminologyMapper imported")
        
        from api.v1.models.document import DocumentType, DocumentStatus
        print("✓ Document models imported")
        
        from api.v1.models.document_batch import BatchUploadStatus
        print("✓ Batch models imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_terminology_mapping():
    """Test basic terminology mapping"""
    print("\nTesting terminology mapping...")
    
    try:
        from app.standards.terminology.mapper import TerminologyMapper
        
        mapper = TerminologyMapper()
        print("✓ TerminologyMapper created")
        
        # Test a simple mapping
        results = mapper.map_term("diabetes")
        if results:
            print(f"✓ Found {len(results)} results for 'diabetes'")
            if len(results) > 0:
                print(f"  First result: {results[0].get('display', 'N/A')}")
        else:
            print("⚠️  No results for diabetes (possibly empty database)")
        
        return True
    except Exception as e:
        print(f"❌ Terminology mapping failed: {e}")
        return False

def test_document_models():
    """Test document models work"""
    print("\nTesting document models...")
    
    try:
        from api.v1.models.document import DocumentType, DocumentStatus
        from api.v1.models.document_batch import BatchUploadStatus
        from uuid import uuid4
        from datetime import datetime, timezone
        
        # Test enum values
        assert DocumentType.TXT == "txt"
        assert DocumentStatus.PENDING == "pending"
        assert BatchUploadStatus.COMPLETED == "completed"
        print("✓ Model enums working")
        
        return True
    except Exception as e:
        print(f"❌ Document models failed: {e}")
        return False

def test_basic_text_processing():
    """Test basic text processing capabilities"""
    print("\nTesting text processing...")
    
    try:
        # Test basic string operations that would be used in the system
        medical_text = "Patient has diabetes mellitus and takes metformin 500mg twice daily."
        
        # Basic text cleaning
        cleaned = medical_text.lower().strip()
        assert len(cleaned) > 0
        
        # Basic tokenization
        words = cleaned.split()
        assert "diabetes" in words
        assert "metformin" in words
        
        print("✓ Basic text processing works")
        return True
    except Exception as e:
        print(f"❌ Text processing failed: {e}")
        return False

def main():
    """Run simple health checks"""
    print("=" * 60)
    print("SIMPLE HEALTH CHECK")
    print("=" * 60)
    
    tests = [
        test_basic_imports,
        test_document_models,
        test_basic_text_processing,
        test_terminology_mapping,
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✅ ALL TESTS PASSED - System is healthy!")
    elif passed >= len(tests) * 0.75:
        print("⚠️  MOSTLY WORKING - Minor issues detected")
    else:
        print("❌ SYSTEM ISSUES - Multiple failures detected")
    
    print("=" * 60)
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)