#!/usr/bin/env python3
"""
Basic System Health Test

Tests core functionality without external dependencies that might have issues.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that core modules can be imported"""
    print("=== Testing Core Module Imports ===")
    
    try:
        from app.standards.terminology.mapper import TerminologyMapper
        print("✓ TerminologyMapper imported successfully")
    except Exception as e:
        print(f"❌ Failed to import TerminologyMapper: {e}")
        return False
    
    try:
        from app.standards.terminology.embedded_db import EmbeddedDatabaseManager
        print("✓ EmbeddedDatabaseManager imported successfully")
    except Exception as e:
        print(f"❌ Failed to import EmbeddedDatabaseManager: {e}")
        return False
    
    try:
        from api.v1.models.document import DocumentType, DocumentStatus
        print("✓ Document models imported successfully")
    except Exception as e:
        print(f"❌ Failed to import document models: {e}")
        return False
    
    try:
        from api.v1.models.document_batch import BatchUploadStatus
        print("✓ Batch models imported successfully")
    except Exception as e:
        print(f"❌ Failed to import batch models: {e}")
        return False
    
    return True


def test_terminology_mapper():
    """Test basic terminology mapping functionality"""
    print("\n=== Testing Terminology Mapper ===")
    
    try:
        from app.standards.terminology.mapper import TerminologyMapper
        
        # Initialize mapper
        mapper = TerminologyMapper()
        print("✓ TerminologyMapper initialized")
        
        # Test basic mapping
        results = mapper.map_term("diabetes", system="snomed")
        if results and len(results) > 0:
            print(f"✓ Successfully mapped 'diabetes' to {len(results)} SNOMED codes")
            print(f"  Top result: {results[0].get('display', 'N/A')}")
        else:
            print("⚠️  No results for diabetes mapping (database may not be loaded)")
        
        # Test LOINC mapping
        results = mapper.map_term("glucose", system="loinc")
        if results and len(results) > 0:
            print(f"✓ Successfully mapped 'glucose' to {len(results)} LOINC codes")
        else:
            print("⚠️  No results for glucose mapping")
        
        # Test RxNorm mapping
        results = mapper.map_term("metformin", system="rxnorm")
        if results and len(results) > 0:
            print(f"✓ Successfully mapped 'metformin' to {len(results)} RxNorm codes")
        else:
            print("⚠️  No results for metformin mapping")
        
        return True
        
    except Exception as e:
        print(f"❌ Terminology mapper test failed: {e}")
        return False


def test_database_structure():
    """Test that terminology databases are accessible"""
    print("\n=== Testing Database Structure ===")
    
    try:
        from app.standards.terminology.embedded_db import EmbeddedDatabaseManager
        
        # Initialize database manager
        db_manager = EmbeddedDatabaseManager()
        print("✓ Database manager initialized")
        
        # Check available systems
        systems = ['snomed', 'loinc', 'rxnorm']
        available_systems = []
        
        for system in systems:
            try:
                db_path = db_manager._get_db_path(system)
                if os.path.exists(db_path):
                    available_systems.append(system)
                    print(f"✓ {system.upper()} database found at {db_path}")
                else:
                    print(f"⚠️  {system.upper()} database not found")
            except Exception as e:
                print(f"⚠️  Error checking {system}: {e}")
        
        if len(available_systems) > 0:
            print(f"✓ Found {len(available_systems)} terminology databases")
            return True
        else:
            print("❌ No terminology databases found")
            return False
            
    except Exception as e:
        print(f"❌ Database structure test failed: {e}")
        return False


def test_document_models():
    """Test document model functionality"""
    print("\n=== Testing Document Models ===")
    
    try:
        from api.v1.models.document import (
            DocumentType, DocumentStatus, DocumentUploadResponse
        )
        from api.v1.models.document_batch import (
            BatchUploadStatus, BatchUploadResponse
        )
        from uuid import uuid4
        from datetime import datetime
        
        # Test document types
        assert DocumentType.PDF == "pdf"
        assert DocumentType.TXT == "txt"
        print("✓ Document types working")
        
        # Test document status
        assert DocumentStatus.PENDING == "pending"
        assert DocumentStatus.COMPLETED == "completed"
        print("✓ Document status working")
        
        # Test batch status
        assert BatchUploadStatus.PENDING == "pending"
        assert BatchUploadStatus.COMPLETED == "completed"
        print("✓ Batch status working")
        
        # Test model creation
        response = DocumentUploadResponse(
            document_id=uuid4(),
            status=DocumentStatus.PENDING,
            filename="test.txt",
            document_type=DocumentType.TXT,
            file_size=100,
            upload_timestamp=datetime.utcnow(),
            processing_url="/test"
        )
        assert response.document_id is not None
        print("✓ Document response model working")
        
        batch_response = BatchUploadResponse(
            batch_id=uuid4(),
            status=BatchUploadStatus.PENDING,
            total_documents=5,
            created_at=datetime.utcnow(),
            status_url="/test"
        )
        assert batch_response.batch_id is not None
        print("✓ Batch response model working")
        
        return True
        
    except Exception as e:
        print(f"❌ Document models test failed: {e}")
        return False


def test_fuzzy_matching():
    """Test fuzzy matching functionality"""
    print("\n=== Testing Fuzzy Matching ===")
    
    try:
        from app.standards.terminology.fuzzy_matcher import FuzzyMatcher
        from app.standards.terminology.embedded_db import EmbeddedDatabaseManager
        
        db_manager = EmbeddedDatabaseManager()
        fuzzy_matcher = FuzzyMatcher(db_manager, {})
        print("✓ Fuzzy matcher initialized")
        
        # Test basic fuzzy matching
        results = fuzzy_matcher.find_matches(
            "diabetis",  # Misspelled diabetes
            system="snomed",
            threshold=0.6
        )
        
        if results and len(results) > 0:
            print(f"✓ Fuzzy matching found {len(results)} results for misspelled 'diabetis'")
            for result in results[:3]:
                print(f"  - {result.get('display', 'N/A')} (score: {result.get('score', 0):.2f})")
        else:
            print("⚠️  No fuzzy matching results (database may not be loaded)")
        
        return True
        
    except Exception as e:
        print(f"❌ Fuzzy matching test failed: {e}")
        return False


def test_data_directory_structure():
    """Test that data directory has expected structure"""
    print("\n=== Testing Data Directory Structure ===")
    
    try:
        # Check for data directory
        data_dir = Path("data")
        if not data_dir.exists():
            # Try alternative locations
            alt_locations = [
                Path("../data"),
                Path("../../data"),
                Path("backend/data")
            ]
            for loc in alt_locations:
                if loc.exists():
                    data_dir = loc
                    break
        
        if not data_dir.exists():
            print("⚠️  Data directory not found")
            return False
        
        print(f"✓ Data directory found at {data_dir.absolute()}")
        
        # Check subdirectories
        expected_dirs = ["terminology", "samples"]
        for subdir in expected_dirs:
            subdir_path = data_dir / subdir
            if subdir_path.exists():
                print(f"✓ Found {subdir} directory")
            else:
                print(f"⚠️  Missing {subdir} directory")
        
        # Check for database files
        terminology_dir = data_dir / "terminology"
        if terminology_dir.exists():
            db_files = list(terminology_dir.glob("*.db"))
            if db_files:
                print(f"✓ Found {len(db_files)} database files")
                for db_file in db_files:
                    size_mb = db_file.stat().st_size / (1024 * 1024)
                    print(f"  - {db_file.name}: {size_mb:.1f} MB")
            else:
                print("⚠️  No database files found")
        
        return True
        
    except Exception as e:
        print(f"❌ Data directory test failed: {e}")
        return False


def test_configuration_files():
    """Test configuration files"""
    print("\n=== Testing Configuration Files ===")
    
    try:
        # Check for mapping config
        config_paths = [
            "data/terminology/mapping_config.json",
            "../data/terminology/mapping_config.json",
            "backend/data/terminology/mapping_config.json"
        ]
        
        config_found = False
        for config_path in config_paths:
            if os.path.exists(config_path):
                config_found = True
                print(f"✓ Found mapping config at {config_path}")
                
                # Try to load and validate config
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                if "systems" in config:
                    print(f"  - Configured systems: {list(config['systems'].keys())}")
                
                break
        
        if not config_found:
            print("⚠️  Mapping configuration file not found")
        
        return config_found
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def main():
    """Run all basic health tests"""
    print("=" * 80)
    print("BASIC SYSTEM HEALTH TEST")
    print("=" * 80)
    
    tests = [
        ("Core Module Imports", test_imports),
        ("Document Models", test_document_models),
        ("Data Directory Structure", test_data_directory_structure),
        ("Configuration Files", test_configuration_files),
        ("Database Structure", test_database_structure),
        ("Terminology Mapper", test_terminology_mapper),
        ("Fuzzy Matching", test_fuzzy_matching),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            print()
    
    print("=" * 80)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL BASIC HEALTH TESTS PASSED!")
        print("System appears to be functioning correctly.")
    elif passed >= total * 0.7:  # 70% pass rate
        print("⚠️  MOST TESTS PASSED")
        print("System is mostly functional but may have some issues.")
    else:
        print("❌ MULTIPLE TEST FAILURES")
        print("System has significant issues that need to be addressed.")
    
    print("=" * 80)
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)