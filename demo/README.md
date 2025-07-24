# Medical Terminology Mapper - Demo & Examples

This directory contains demonstration materials and usage examples for the Medical Terminology Mapper platform.

## 📁 Contents

### Sample Documents (`sample_documents/`)

Realistic medical documents for testing and demonstration:

- **`clinical_note_example.txt`**: Emergency department consultation note with chest pain presentation
- **`discharge_summary_example.txt`**: Hospital discharge summary for acute myocardial infarction
- **`lab_report_example.txt`**: Comprehensive laboratory results with metabolic panel and lipid analysis

These documents contain typical medical terminology, medications, procedures, and lab values that the system can extract and map to standard terminologies.

### Usage Examples (`usage_examples.py`)

Interactive Python script demonstrating key platform features:

1. **Health Check**: Verify API availability
2. **Single Document Processing**: Upload and process individual documents
3. **Batch Processing**: Handle multiple documents simultaneously
4. **Terminology Mapping**: Direct term-to-code mapping
5. **Entity Analysis**: Analyze extraction results and statistics

## 🚀 Quick Start

### Prerequisites

Ensure the Medical Terminology Mapper is running:

```bash
# Option 1: Docker Compose (recommended)
docker-compose up -d

# Option 2: Local development
cd backend
python -m uvicorn api.main:app --reload
```

### Run Examples

```bash
# Navigate to demo directory
cd demo

# Run all examples
python usage_examples.py

# Or run specific examples
python -c "from usage_examples import example_2_single_document_processing; example_2_single_document_processing()"
```

## 📖 Example Walkthrough

### 1. Single Document Processing

```python
from usage_examples import MedicalTerminologyMapperClient

client = MedicalTerminologyMapperClient()

# Upload document
result = client.upload_document(Path("sample_documents/clinical_note_example.txt"))
document_id = result['document_id']

# Extract entities
entities = client.extract_entities(document_id)
print(f"Found {len(entities['entities'])} medical entities")
```

**Expected Results:**
- **Conditions**: acute coronary syndrome, hypertension, diabetes mellitus
- **Medications**: metformin, lisinopril, aspirin
- **Tests**: ECG, troponin I, chest X-ray
- **Anatomy**: heart, chest, arm

### 2. Batch Processing

```python
# Upload multiple documents
batch_result = client.upload_batch_documents([
    Path("sample_documents/clinical_note_example.txt"),
    Path("sample_documents/discharge_summary_example.txt"),
    Path("sample_documents/lab_report_example.txt")
])

batch_id = batch_result['batch_id']

# Monitor progress
status = client.get_batch_status(batch_id)
print(f"Progress: {status['progress_percentage']}%")

# Get results when complete
results = client.get_batch_results(batch_id)
```

**Expected Results:**
- **Total Entities**: ~50-75 medical entities across all documents
- **SNOMED CT Mappings**: Clinical conditions and procedures
- **LOINC Mappings**: Laboratory tests and observations
- **RxNorm Mappings**: Medications and dosages

### 3. Terminology Mapping

```python
# Map individual terms
mapping = client.map_term("diabetes", context="diagnosis")

for result in mapping['mappings']:
    print(f"{result['system']}: {result['code']} - {result['display']}")
```

**Expected Results:**
```
SNOMED: 73211009 - Diabetes mellitus
ICD10: E11 - Type 2 diabetes mellitus
```

## 🔍 Understanding the Results

### Entity Types

The system recognizes these medical entity categories:

| Entity Type | Description | Examples from Demo |
|-------------|-------------|-------------------|
| `CONDITION` | Medical conditions, diseases | diabetes mellitus, hypertension, acute coronary syndrome |
| `DRUG` | Medications, pharmaceuticals | metformin, lisinopril, aspirin, atorvastatin |
| `PROCEDURE` | Medical procedures | cardiac catheterization, echocardiogram, PCI |
| `TEST` | Laboratory tests, diagnostics | troponin I, ECG, chest X-ray, blood glucose |
| `ANATOMY` | Body parts, organs | heart, chest, left arm, kidney |
| `DOSAGE` | Drug dosages | 500mg, 81mg daily, twice daily |
| `OBSERVATION` | Clinical observations | chest pain, shortness of breath, diaphoresis |

### Confidence Scores

Each extracted entity and terminology mapping includes a confidence score:

- **High Confidence (0.8-1.0)**: Exact matches, standard medical terms
- **Medium Confidence (0.6-0.8)**: Good fuzzy matches, common abbreviations
- **Lower Confidence (0.4-0.6)**: Partial matches, contextual mappings

### Terminology Systems

**SNOMED CT**: Clinical terminology
- Conditions: diabetes mellitus → 73211009
- Procedures: cardiac catheterization → 41976001
- Anatomy: heart → 80891009

**LOINC**: Laboratory and observations
- Tests: glucose → 33747-0
- Vital signs: blood pressure → 85354-9
- Clinical documents: discharge summary → 18842-5

**RxNorm**: Medications
- Generic drugs: metformin → 6809
- Brand names: Lipitor → 153165
- Dosage forms: tablet → varies by specific drug

## 📊 Export Formats

The system supports multiple export formats:

### JSON Export
```json
{
  "batch_id": "uuid",
  "documents": [
    {
      "document_id": "uuid",
      "filename": "clinical_note.txt",
      "entities": [...],
      "terminology_mappings": {...},
      "entity_statistics": {...}
    }
  ],
  "batch_statistics": {...}
}
```

### CSV Export
Two files generated:
- `documents_timestamp.csv`: Document-level statistics
- `entities_timestamp.csv`: Individual entity extractions

### Excel Export
Multi-sheet workbook:
- **Documents**: Document metadata and statistics
- **Entities**: Detailed entity extractions
- **Terminology Mappings**: Mapped codes and confidence scores

## 🎯 Use Cases

### Clinical Research
- Extract medication lists from clinical notes
- Identify patient conditions across multiple documents
- Standardize terminology for research databases

### Healthcare Interoperability
- Convert free-text clinical notes to structured data
- Map local terminology to standard vocabularies
- Prepare data for FHIR resource creation

### Quality Improvement
- Analyze documentation quality and completeness
- Identify missing or inconsistent terminology
- Monitor medication adherence and outcomes

### Medical Coding
- Assist with ICD-10 and CPT coding
- Identify billable procedures and diagnoses
- Reduce manual coding time and errors

## 🔧 Customization

### Adding Custom Documents

Add your own medical documents to the `sample_documents/` directory:

```bash
# Supported formats
cp your_document.pdf sample_documents/
cp your_document.docx sample_documents/
cp your_document.txt sample_documents/
```

### Custom Terminology Mappings

Add custom mapping rules for organization-specific terms:

```python
from app.standards.terminology.custom_mapping_rules import add_custom_mapping

add_custom_mapping(
    term="MI",
    target_system="snomed",
    target_code="22298006",
    confidence=0.95
)
```

### Adjusting Confidence Thresholds

Modify entity extraction sensitivity:

```python
# Higher threshold = more precise, fewer results
entities = client.extract_entities(
    document_id, 
    confidence_threshold=0.8
)

# Lower threshold = more comprehensive, potentially more noise
entities = client.extract_entities(
    document_id, 
    confidence_threshold=0.5
)
```

## 🐛 Troubleshooting

### Common Issues

**API Connection Errors**:
```bash
# Check if services are running
docker-compose ps

# View logs
docker-compose logs api
```

**Entity Extraction Timeouts**:
- Large documents may take 2-5 minutes to process
- Monitor progress with batch status endpoints
- Consider splitting very large documents

**Missing Terminology Mappings**:
- Some entities may not have standard code mappings
- Custom mappings can be added for organization-specific terms
- Check confidence thresholds for potential matches

**Low Confidence Scores**:
- Medical abbreviations may have lower confidence
- Spelling variations affect matching accuracy
- Context can improve mapping quality

## 📞 Support

For questions about the demo or examples:

1. **Check the logs**: `docker-compose logs -f`
2. **API Documentation**: http://localhost:8000/docs
3. **Web Interface**: http://localhost:3000
4. **GitHub Issues**: Report bugs or request features

## 🎓 Learning Resources

- **Medical Terminologies**:
  - [SNOMED CT Browser](https://browser.ihtsdotools.org/)
  - [LOINC Database](https://loinc.org/)
  - [RxNorm Browser](https://mor.nlm.nih.gov/RxNav/)

- **Healthcare Standards**:
  - [HL7 FHIR](https://www.hl7.org/fhir/)
  - [ICD-10-CM](https://www.cdc.gov/nchs/icd/icd10cm.htm)
  - [CPT Codes](https://www.ama-assn.org/practice-management/cpt)

---

**Note**: The demo documents contain fictional patient data for demonstration purposes only. Do not use real patient data without proper authorization and compliance with healthcare regulations.