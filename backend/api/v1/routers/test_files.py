from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Define the test files directory
TEST_FILES_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "test_files"

# Define which files to expose
AVAILABLE_TEST_FILES = {
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
    },
    "fuzzy_test_terms.csv": {
        "name": "Fuzzy Test Terms",
        "description": "Terms with misspellings and variations",
        "size": "small"
    },
    "edge_cases.csv": {
        "name": "Edge Cases",
        "description": "Challenging terms and edge cases",
        "size": "small"
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