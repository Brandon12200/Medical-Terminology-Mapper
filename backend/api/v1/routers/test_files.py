from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Define the test files directory - use absolute path
TEST_FILES_DIR = Path("/app/data/test_files")

# Define which files to expose - including comprehensive sample files
AVAILABLE_TEST_FILES = {
    "hospital_discharge_summary.csv": {
        "name": "Hospital Discharge Summary",
        "description": "120+ comprehensive medical conditions across all specialties",
        "size": "large"
    },
    "comprehensive_lab_tests.csv": {
        "name": "Comprehensive Lab Tests", 
        "description": "150+ laboratory tests with clinical significance",
        "size": "large"
    },
    "comprehensive_medications.csv": {
        "name": "Pharmaceutical Database",
        "description": "200+ medications covering all major drug classes",
        "size": "large"
    },
    "emergency_department_cases.csv": {
        "name": "Emergency Department Cases",
        "description": "100+ emergency scenarios with triage complexity",
        "size": "large"
    },
    "surgical_procedures.csv": {
        "name": "Surgical Procedures",
        "description": "130+ surgical procedures with complexity ratings",
        "size": "large"
    },
    "rare_diseases_comprehensive.csv": {
        "name": "Rare Diseases",
        "description": "200+ rare genetic conditions with inheritance patterns",
        "size": "large"
    },
    "simple_terms.csv": {
        "name": "Simple Terms",
        "description": "Basic medical terms for quick testing",
        "size": "small"
    },
    "medical_conditions.csv": {
        "name": "Medical Conditions",
        "description": "Common medical conditions and diagnoses",
        "size": "medium"
    },
    "medications.csv": {
        "name": "Medications",
        "description": "Common medication names",
        "size": "medium"
    },
    "lab_tests.csv": {
        "name": "Lab Tests",
        "description": "Laboratory test names and codes",
        "size": "medium"
    }
}

@router.get("/test-files", response_model=List[Dict])
async def list_test_files():
    """List available test files for download"""
    files_info = []
    
    for filename, info in AVAILABLE_TEST_FILES.items():
        file_path = TEST_FILES_DIR / filename
        if file_path.exists():
            file_size = file_path.stat().st_size
            files_info.append({
                "filename": filename,
                "name": info["name"],
                "description": info["description"],
                "size": file_size,
                "size_category": info["size"]
            })
    
    return files_info

@router.get("/test-files/{filename}")
async def download_test_file(filename: str):
    """Download a specific test file"""
    if filename not in AVAILABLE_TEST_FILES:
        raise HTTPException(status_code=404, detail="Test file not found")
    
    file_path = TEST_FILES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Test file not found on server")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="text/csv"
    )
