# Test Data Files

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
curl -X POST http://localhost:8000/api/v1/batch/upload   -F "file=@medical_conditions.csv"
```
