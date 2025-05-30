#!/usr/bin/env python3
"""
Download sample medical terminology test files for testing the Medical Terminology Mapper.
This script creates sample CSV files with medical terms for testing batch processing.
"""

import os
import csv
import json
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent

def create_sample_csv_files():
    """Create sample CSV files with medical terms for testing."""
    
    # Sample medical terms for different categories
    general_medical_terms = [
        ["term", "context"],
        ["diabetes mellitus type 2", "endocrine disorder"],
        ["hypertension", "cardiovascular condition"],
        ["asthma", "respiratory disease"],
        ["pneumonia", "infectious disease"],
        ["myocardial infarction", "cardiac event"],
        ["chronic obstructive pulmonary disease", "respiratory"],
        ["acute kidney injury", "renal condition"],
        ["major depressive disorder", "mental health"],
        ["osteoarthritis", "musculoskeletal"],
        ["gastroesophageal reflux disease", "gastrointestinal"]
    ]
    
    lab_test_terms = [
        ["term", "context"],
        ["glucose", "laboratory test"],
        ["hemoglobin A1c", "diabetes monitoring"],
        ["complete blood count", "hematology"],
        ["basic metabolic panel", "chemistry"],
        ["lipid panel", "cardiovascular risk"],
        ["thyroid stimulating hormone", "endocrine test"],
        ["prothrombin time", "coagulation"],
        ["urinalysis", "urine test"],
        ["liver function tests", "hepatic panel"],
        ["creatinine", "kidney function"]
    ]
    
    medication_terms = [
        ["term", "context"],
        ["metformin", "diabetes medication"],
        ["lisinopril", "antihypertensive"],
        ["albuterol", "bronchodilator"],
        ["atorvastatin", "lipid lowering"],
        ["levothyroxine", "thyroid hormone"],
        ["omeprazole", "proton pump inhibitor"],
        ["amlodipine", "calcium channel blocker"],
        ["sertraline", "antidepressant"],
        ["gabapentin", "neuropathic pain"],
        ["prednisone", "corticosteroid"]
    ]
    
    # Terms with typos and variations for fuzzy matching testing
    fuzzy_test_terms = [
        ["term", "context"],
        ["diabetis", "misspelling test"],
        ["hypertention", "misspelling test"],
        ["asthma attack", "variation test"],
        ["heart attack", "lay term test"],
        ["sugar disease", "colloquial term"],
        ["high blood pressure", "lay term test"],
        ["shortness of breath", "symptom"],
        ["chest pain", "symptom"],
        ["covid-19", "infectious disease"],
        ["coronavirus disease", "infectious disease"]
    ]
    
    # Create CSV files
    files_created = []
    
    # General medical terms
    general_file = SCRIPT_DIR / "medical_conditions.csv"
    with open(general_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(general_medical_terms)
    files_created.append(general_file)
    print(f"✅ Created: {general_file}")
    
    # Lab test terms
    lab_file = SCRIPT_DIR / "lab_tests.csv"
    with open(lab_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(lab_test_terms)
    files_created.append(lab_file)
    print(f"✅ Created: {lab_file}")
    
    # Medication terms
    med_file = SCRIPT_DIR / "medications.csv"
    with open(med_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(medication_terms)
    files_created.append(med_file)
    print(f"✅ Created: {med_file}")
    
    # Fuzzy matching test terms
    fuzzy_file = SCRIPT_DIR / "fuzzy_test_terms.csv"
    with open(fuzzy_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(fuzzy_test_terms)
    files_created.append(fuzzy_file)
    print(f"✅ Created: {fuzzy_file}")
    
    # Large batch test file
    large_batch_terms = [["term", "context"]]
    # Combine all terms into one large file
    all_terms = (general_medical_terms[1:] + lab_test_terms[1:] + 
                 medication_terms[1:] + fuzzy_test_terms[1:])
    # Duplicate to create a larger dataset
    large_batch_terms.extend(all_terms * 3)
    
    large_file = SCRIPT_DIR / "large_batch_test.csv"
    with open(large_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(large_batch_terms)
    files_created.append(large_file)
    print(f"✅ Created: {large_file} ({len(large_batch_terms)-1} terms)")
    
    # Create a simple terms list (no header, single column)
    simple_terms = [
        ["diabetes"],
        ["hypertension"],
        ["asthma"],
        ["pneumonia"],
        ["covid-19"],
        ["heart failure"],
        ["kidney disease"],
        ["liver cirrhosis"],
        ["depression"],
        ["anxiety"]
    ]
    
    simple_file = SCRIPT_DIR / "simple_terms.csv"
    with open(simple_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(simple_terms)
    files_created.append(simple_file)
    print(f"✅ Created: {simple_file}")
    
    return files_created

def create_json_test_files():
    """Create JSON format test files."""
    
    # Sample data for JSON format
    json_test_data = {
        "terms": [
            {"term": "diabetes mellitus", "context": "diagnosis"},
            {"term": "insulin", "context": "medication"},
            {"term": "glucose test", "context": "laboratory"},
            {"term": "hypertension", "context": "diagnosis"},
            {"term": "blood pressure", "context": "vital sign"}
        ],
        "metadata": {
            "source": "test_data",
            "date": "2024-05-25",
            "purpose": "testing batch processing"
        }
    }
    
    json_file = SCRIPT_DIR / "test_terms.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_test_data, f, indent=2)
    print(f"✅ Created: {json_file}")
    
    return json_file

def create_txt_test_files():
    """Create plain text test files."""
    
    # Clinical note example
    clinical_note = """Patient presents with uncontrolled diabetes mellitus type 2 and hypertension.
Current medications include metformin 1000mg twice daily and lisinopril 10mg daily.
Lab results show elevated glucose levels and hemoglobin A1c of 8.5%.
Patient also reports symptoms of gastroesophageal reflux disease.
Recommend starting omeprazole and adjusting diabetes medication regimen.
Follow up in 3 months with repeat HbA1c and basic metabolic panel."""
    
    txt_file = SCRIPT_DIR / "clinical_note.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(clinical_note)
    print(f"✅ Created: {txt_file}")
    
    # Simple term list
    term_list = """diabetes
hypertension
asthma
COPD
pneumonia
COVID-19
heart failure
chronic kidney disease
depression
anxiety disorder"""
    
    list_file = SCRIPT_DIR / "term_list.txt"
    with open(list_file, 'w', encoding='utf-8') as f:
        f.write(term_list)
    print(f"✅ Created: {list_file}")
    
    return [txt_file, list_file]

def create_readme():
    """Create a README file explaining the test files."""
    
    readme_content = """# Test Data Files

This directory contains sample medical terminology files for testing the Medical Terminology Mapper.

## File Descriptions

### CSV Files
- **medical_conditions.csv**: Common medical conditions and diagnoses
- **lab_tests.csv**: Laboratory test names and related terms
- **medications.csv**: Common medication names
- **fuzzy_test_terms.csv**: Terms with typos and variations for testing fuzzy matching
- **large_batch_test.csv**: Large dataset for performance testing
- **simple_terms.csv**: Simple single-column term list

### JSON Files
- **test_terms.json**: JSON formatted medical terms with metadata

### Text Files
- **clinical_note.txt**: Sample clinical note with embedded medical terms
- **term_list.txt**: Simple list of medical terms

## Usage

These files can be used to test:
1. Single term mapping
2. Batch CSV upload functionality
3. Fuzzy matching capabilities
4. Performance with large datasets
5. Different file format support

## Testing Examples

```bash
# Test with CLI
python -m cli.map_terms --batch medical_conditions.csv --output results.json

# Upload via API
curl -X POST http://localhost:8000/api/v1/batch/upload \
  -F "file=@medical_conditions.csv"
```
"""
    
    readme_file = SCRIPT_DIR / "README_TEST_DATA.txt"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"✅ Created: {readme_file}")

def main():
    """Main function to create all test files."""
    print("🏥 Creating Medical Terminology Test Files...")
    print("=" * 50)
    
    # Create different format files
    csv_files = create_sample_csv_files()
    json_file = create_json_test_files()
    txt_files = create_txt_test_files()
    create_readme()
    
    print("=" * 50)
    print(f"✅ Successfully created {len(csv_files) + 1 + len(txt_files) + 1} test files")
    print(f"📁 Location: {SCRIPT_DIR}")
    print("\n📋 File Summary:")
    print(f"  - CSV files: {len(csv_files)}")
    print(f"  - JSON files: 1")
    print(f"  - Text files: {len(txt_files)}")
    print(f"  - Documentation: 1")
    print("\n🚀 You can now use these files to test the Medical Terminology Mapper!")

if __name__ == "__main__":
    main()