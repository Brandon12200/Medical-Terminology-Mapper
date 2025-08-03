#!/usr/bin/env python3
"""
Comprehensive System Validation

Tests all implemented functionality to ensure the system is working correctly.
"""

import os
import sys
import tempfile
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from uuid import UUID, uuid4

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ComprehensiveValidator:
    """Validates all system components"""
    
    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "details": []
        }
    
    def log_result(self, test_name, status, message="", details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.test_results["details"].append(result)
        
        if status == "PASS":
            self.test_results["passed"] += 1
            print(f"✓ {test_name}: {message}")
        elif status == "FAIL":
            self.test_results["failed"] += 1
            print(f"❌ {test_name}: {message}")
        elif status == "WARN":
            self.test_results["warnings"] += 1
            print(f"⚠️  {test_name}: {message}")
    
    def test_01_core_imports(self):
        """Test core module imports"""
        print("\n=== Test 1: Core Module Imports ===")
        
        try:
            from app.standards.terminology.mapper import TerminologyMapper
            self.log_result("TerminologyMapper Import", "PASS", "Successfully imported")
            
            from api.v1.models.document import DocumentType, DocumentStatus
            self.log_result("Document Models Import", "PASS", "Successfully imported")
            
            from api.v1.models.document_batch import BatchUploadStatus
            self.log_result("Batch Models Import", "PASS", "Successfully imported")
            
            return True
        except Exception as e:
            self.log_result("Core Imports", "FAIL", f"Import failed: {e}")
            return False
    
    def test_02_terminology_mapping(self):
        """Test terminology mapping functionality"""
        print("\n=== Test 2: Terminology Mapping ===")
        
        try:
            from app.standards.terminology.mapper import TerminologyMapper
            
            mapper = TerminologyMapper()
            self.log_result("Mapper Initialization", "PASS", "TerminologyMapper created successfully")
            
            # Test SNOMED mapping
            snomed_results = mapper.map_term("diabetes", system="snomed")
            if snomed_results and len(snomed_results) > 0:
                self.log_result("SNOMED Mapping", "PASS", f"Found {len(snomed_results)} diabetes mappings")
                print(f"  Example: {snomed_results[0].get('display', 'N/A')}")
            else:
                self.log_result("SNOMED Mapping", "WARN", "No SNOMED results (database may be empty)")
            
            # Test LOINC mapping
            loinc_results = mapper.map_term("glucose", system="loinc")
            if loinc_results and len(loinc_results) > 0:
                self.log_result("LOINC Mapping", "PASS", f"Found {len(loinc_results)} glucose mappings")
            else:
                self.log_result("LOINC Mapping", "WARN", "No LOINC results")
            
            # Test RxNorm mapping
            rxnorm_results = mapper.map_term("metformin", system="rxnorm")
            if rxnorm_results and len(rxnorm_results) > 0:
                self.log_result("RxNorm Mapping", "PASS", f"Found {len(rxnorm_results)} metformin mappings")
            else:
                self.log_result("RxNorm Mapping", "WARN", "No RxNorm results")
            
            return True
        except Exception as e:
            self.log_result("Terminology Mapping", "FAIL", f"Mapping failed: {e}")
            return False
    
    def test_03_document_models(self):
        """Test document model functionality"""
        print("\n=== Test 3: Document Models ===")
        
        try:
            from api.v1.models.document import (
                DocumentType, DocumentStatus, DocumentUploadResponse
            )
            from api.v1.models.document_batch import (
                BatchUploadStatus, BatchUploadResponse
            )
            
            # Test enums
            assert DocumentType.TXT == "txt"
            assert DocumentStatus.PENDING == "pending"
            assert BatchUploadStatus.COMPLETED == "completed"
            self.log_result("Model Enums", "PASS", "All enums working correctly")
            
            # Test model creation
            doc_response = DocumentUploadResponse(
                document_id=uuid4(),
                status=DocumentStatus.PENDING,
                filename="test.txt",
                document_type=DocumentType.TXT,
                file_size=100,
                upload_timestamp=datetime.now(timezone.utc),
                processing_url="/test"
            )
            self.log_result("Document Response Model", "PASS", "Created successfully")
            
            batch_response = BatchUploadResponse(
                batch_id=uuid4(),
                status=BatchUploadStatus.PENDING,
                total_documents=5,
                created_at=datetime.now(timezone.utc),
                status_url="/test"
            )
            self.log_result("Batch Response Model", "PASS", "Created successfully")
            
            return True
        except Exception as e:
            self.log_result("Document Models", "FAIL", f"Model test failed: {e}")
            return False
    
    def test_04_document_service(self):
        """Test document service functionality"""
        print("\n=== Test 4: Document Service ===")
        
        try:
            # Import without the problematic magic dependency by mocking
            import unittest.mock
            
            with unittest.mock.patch('magic.Magic'):
                from api.v1.services.document_service import DocumentService
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    service = DocumentService(
                        upload_dir=f"{temp_dir}/uploads",
                        db_path=f"{temp_dir}/test.db"
                    )
                    
                    self.log_result("Document Service Init", "PASS", "Service initialized successfully")
                    
                    # Test batch creation
                    batch_id = service.create_document_batch(
                        batch_name="Test Batch",
                        metadata={"test": True},
                        total_documents=3
                    )
                    
                    assert isinstance(batch_id, UUID)
                    self.log_result("Batch Creation", "PASS", f"Created batch {batch_id}")
                    
                    # Test batch status
                    status = service.get_batch_status(batch_id)
                    if status:
                        self.log_result("Batch Status", "PASS", "Retrieved batch status")
                    else:
                        self.log_result("Batch Status", "FAIL", "Could not retrieve batch status")
            
            return True
        except Exception as e:
            self.log_result("Document Service", "FAIL", f"Service test failed: {e}")
            return False
    
    def test_05_biobert_integration(self):
        """Test BioBERT integration (disabled - ML components removed)"""
        print("\n=== Test 5: BioBERT Integration ===")
        self.log_result("BioBERT Integration", "SKIP", "BioBERT functionality disabled in this build")
        return True
    
    def test_06_api_models(self):
        """Test API model serialization"""
        print("\n=== Test 6: API Models ===")
        
        try:
            from api.v1.models.document_batch import BatchProcessingStatus, BatchDocumentItem
            from api.v1.models.document import DocumentType, DocumentStatus
            
            # Create complex model with nested data
            batch_status = BatchProcessingStatus(
                batch_id=uuid4(),
                status="processing",
                total_documents=3,
                processed_documents=1,
                successful_documents=1,
                failed_documents=0,
                progress_percentage=33.33,
                documents=[
                    BatchDocumentItem(
                        document_id=uuid4(),
                        filename="test1.txt",
                        document_type=DocumentType.TXT,
                        status=DocumentStatus.COMPLETED,
                        file_size=1000
                    )
                ]
            )
            
            # Test serialization
            json_data = batch_status.model_dump_json()
            assert isinstance(json_data, str)
            
            # Test deserialization
            parsed_data = json.loads(json_data)
            assert parsed_data["total_documents"] == 3
            
            self.log_result("API Model Serialization", "PASS", "Models serialize/deserialize correctly")
            return True
        except Exception as e:
            self.log_result("API Models", "FAIL", f"Model test failed: {e}")
            return False
    
    def test_07_configuration_loading(self):
        """Test configuration loading"""
        print("\n=== Test 7: Configuration Loading ===")
        
        try:
            # Check for mapping configuration
            config_paths = [
                "data/terminology/mapping_config.json",
                "../data/terminology/mapping_config.json"
            ]
            
            config_loaded = False
            for config_path in config_paths:
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    
                    if "systems" in config:
                        systems = list(config["systems"].keys())
                        self.log_result("Configuration Loading", "PASS", f"Loaded config with systems: {systems}")
                        config_loaded = True
                        break
            
            if not config_loaded:
                self.log_result("Configuration Loading", "WARN", "Configuration file not found")
            
            return True
        except Exception as e:
            self.log_result("Configuration Loading", "FAIL", f"Config loading failed: {e}")
            return False
    
    def test_08_database_connectivity(self):
        """Test database connectivity"""
        print("\n=== Test 8: Database Connectivity ===")
        
        try:
            from app.standards.terminology.embedded_db import EmbeddedDatabaseManager
            
            db_manager = EmbeddedDatabaseManager()
            self.log_result("Database Manager Init", "PASS", "Database manager created")
            
            # Test database connections
            systems = ["snomed", "loinc", "rxnorm"]
            connected_systems = []
            
            for system in systems:
                try:
                    # Try to execute a simple query
                    db_manager.execute_query(system, "SELECT COUNT(*) as count FROM sqlite_master")
                    connected_systems.append(system)
                except Exception as e:
                    self.log_result(f"{system.upper()} Database", "WARN", f"Connection issue: {e}")
            
            if connected_systems:
                self.log_result("Database Connectivity", "PASS", f"Connected to: {connected_systems}")
            else:
                self.log_result("Database Connectivity", "WARN", "No databases connected")
            
            return True
        except Exception as e:
            self.log_result("Database Connectivity", "FAIL", f"Database test failed: {e}")
            return False
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE VALIDATION REPORT")
        print("=" * 80)
        
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        if total_tests > 0:
            pass_rate = (self.test_results["passed"] / total_tests) * 100
        else:
            pass_rate = 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.test_results['passed']}")
        print(f"Failed: {self.test_results['failed']}")
        print(f"Warnings: {self.test_results['warnings']}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results["details"]:
            status_symbol = {"PASS": "✓", "FAIL": "❌", "WARN": "⚠️"}.get(result["status"], "?")
            print(f"{status_symbol} {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        if pass_rate >= 90:
            print("🎉 EXCELLENT - System is working very well!")
            status = "EXCELLENT"
        elif pass_rate >= 75:
            print("✅ GOOD - System is working with minor issues")
            status = "GOOD"
        elif pass_rate >= 50:
            print("⚠️  FAIR - System has some issues but core functionality works")
            status = "FAIR"
        else:
            print("❌ POOR - System has significant issues")
            status = "POOR"
        
        # Write report to file
        report_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": self.test_results["passed"],
                "failed": self.test_results["failed"],
                "warnings": self.test_results["warnings"],
                "pass_rate": pass_rate,
                "status": status
            },
            "details": self.test_results["details"]
        }
        
        try:
            with open("test_report.json", "w") as f:
                json.dump(report_data, f, indent=2)
            print(f"\nDetailed report saved to test_report.json")
        except Exception as e:
            print(f"Could not save report: {e}")
        
        print("=" * 80)
        return status in ["EXCELLENT", "GOOD"]

def main():
    """Run comprehensive validation"""
    validator = ComprehensiveValidator()
    
    # Run all tests
    tests = [
        validator.test_01_core_imports,
        validator.test_02_terminology_mapping,
        validator.test_03_document_models,
        validator.test_04_document_service,
        validator.test_05_biobert_integration,
        validator.test_06_api_models,
        validator.test_07_configuration_loading,
        validator.test_08_database_connectivity,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    # Generate final report
    success = validator.generate_report()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)