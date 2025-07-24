# Medical AI and BioBERT Integration

This module provides advanced AI-powered medical entity extraction using BioBERT and other state-of-the-art models for the Medical Terminology Mapper.

## Features

### BioBERT Model Management
- **Singleton model manager** for efficient resource utilization
- **GPU/CPU detection** and automatic device selection
- **Model caching** and warm-up for consistent performance
- **Batch processing** for efficient inference on multiple texts
- **Thread-safe operations** for concurrent requests

### Medical Entity Extraction
- **BioBERT-based NER** for medical entities (conditions, medications, procedures, lab tests, observations)
- **Ensemble approach** combining BioBERT with regex patterns
- **Confidence scoring** and filtering
- **Context extraction** for better understanding
- **Post-processing** and normalization of extracted entities

### Terminology Integration
- **Automatic mapping** to standard terminologies (SNOMED CT, LOINC, RxNorm)
- **Semantic similarity** matching using embeddings
- **Multi-system mapping** based on entity types
- **Confidence-based mapping** with top-N results

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  BioBERT        │───▶│  BioBERT        │───▶│  Medical        │
│  Model Manager  │    │  Service        │    │  Entity         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────┐
         │                       │              │  Terminology    │
         │                       │              │  Mapping        │
         │                       │              └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  Model Loading  │    │  Entity Post-   │
│  & Caching      │    │  Processing     │
└─────────────────┘    └─────────────────┘
```

## Usage

### Basic Entity Extraction

```python
from app.ml.biobert import create_biobert_service

# Initialize service
service = create_biobert_service(
    use_regex_patterns=True,
    use_ensemble=True,
    confidence_threshold=0.7
)

# Extract entities
text = "Patient has diabetes mellitus type 2 and takes metformin 500mg twice daily"
entities = service.extract_entities(text)

for entity in entities:
    print(f"{entity.text} ({entity.entity_type}) - {entity.confidence:.2f}")
```

### Document Analysis

```python
# Comprehensive document analysis
analysis = service.analyze_document(medical_text)

print(f"Found {len(analysis.entities)} entities")
print(f"Entity summary: {analysis.entity_summary}")
print(f"Processing time: {analysis.processing_time:.2f}s")
```

### Batch Processing

```python
# Process multiple texts efficiently
texts = ["Patient has hypertension", "Prescribed lisinopril 10mg"]
batch_results = service.extract_entities_batch(texts, batch_size=8)

for i, entities in enumerate(batch_results):
    print(f"Text {i}: {len(entities)} entities found")
```

### Enhanced Term Extractor (Legacy Compatibility)

```python
from app.extractors.term_extractor import EnhancedTermExtractor

# Initialize enhanced extractor
extractor = EnhancedTermExtractor(
    use_cache=True,
    confidence_threshold=0.7,
    use_terminology_mapping=True
)

# Extract terms (legacy format)
terms = extractor.extract_terms(medical_text)
```

## API Endpoints

### Entity Extraction
```bash
POST /api/v1/ai/extract-entities
Content-Type: application/json

{
    "text": "Patient has diabetes mellitus type 2",
    "confidence_threshold": 0.7,
    "extract_context": true,
    "map_to_terminologies": true,
    "use_ensemble": true
}
```

### Document Analysis
```bash
POST /api/v1/ai/analyze-document
Content-Type: application/json

{
    "text": "...",
    "confidence_threshold": 0.7
}
```

### Model Status
```bash
GET /api/v1/ai/models/status
```

### Model Initialization
```bash
POST /api/v1/ai/models/initialize
```

## Configuration

### Environment Variables
```bash
# Model settings
BIOBERT_MODEL_PATH=/path/to/model
BIOBERT_CONFIDENCE_THRESHOLD=0.7
BIOBERT_BATCH_SIZE=8
BIOBERT_MAX_LENGTH=512

# Device settings
CUDA_VISIBLE_DEVICES=0
TORCH_NUM_THREADS=4

# Cache settings
ENABLE_MODEL_CACHE=true
MODEL_CACHE_SIZE=100
```

### Model Configuration
```json
{
    "model_type": "biobert",
    "name": "dmis-lab/biobert-base-cased-v1.2",
    "version": "v1.0",
    "entity_types": [
        "CONDITION",
        "MEDICATION", 
        "PROCEDURE",
        "LAB_TEST",
        "OBSERVATION"
    ],
    "confidence_threshold": 0.7,
    "max_length": 512,
    "batch_size": 8
}
```

## Entity Types

### CONDITION
Medical conditions, diseases, disorders, syndromes
- Examples: "diabetes mellitus", "hypertension", "myocardial infarction"

### MEDICATION
Drugs, medications, chemical substances
- Examples: "metformin", "lisinopril", "insulin"

### PROCEDURE
Medical procedures, surgeries, treatments
- Examples: "CT scan", "appendectomy", "chemotherapy"

### LAB_TEST
Laboratory tests, diagnostic tests
- Examples: "glucose", "HbA1c", "creatinine"

### OBSERVATION
Medical observations, symptoms, findings
- Examples: "chest pain", "shortness of breath", "fever"

## Performance Optimization

### Model Loading
- **Lazy loading**: Models are loaded only when first needed
- **Singleton pattern**: Single model instance shared across requests
- **Warm-up**: Model pre-warmed with sample inputs for consistent latency

### Batch Processing
- **Automatic batching**: Efficient processing of multiple texts
- **GPU utilization**: Optimal batch sizes for GPU memory
- **Parallel processing**: Concurrent entity extraction and post-processing

### Caching
- **Result caching**: Cache extraction results by text hash
- **Model caching**: Keep models in memory between requests
- **Terminology caching**: Cache terminology mappings

## Error Handling

### Model Loading Errors
```python
try:
    service = create_biobert_service()
except Exception as e:
    logger.error(f"Failed to initialize BioBERT service: {e}")
    # Fallback to regex-only extraction
```

### Extraction Errors
```python
try:
    entities = service.extract_entities(text)
except Exception as e:
    logger.warning(f"Entity extraction failed: {e}")
    entities = []  # Return empty list
```

### GPU Memory Errors
- Automatic fallback to CPU processing
- Reduced batch sizes for memory-constrained environments
- Memory cleanup after processing

## Testing

### Unit Tests
```bash
# Run BioBERT integration tests
pytest tests/test_biobert_integration.py -v

# Run with coverage
pytest tests/test_biobert_integration.py --cov=app.ml
```

### Performance Tests
```bash
# Benchmark entity extraction
python tests/benchmark_biobert.py

# Test memory usage
python tests/test_memory_usage.py
```

### Integration Tests
```bash
# Test full pipeline
python tests/test_biobert_pipeline.py
```

## Monitoring and Metrics

### Performance Metrics
- **Latency**: Average processing time per text
- **Throughput**: Entities extracted per second
- **Memory usage**: GPU/CPU memory consumption
- **Cache hit rate**: Percentage of cached results

### Quality Metrics
- **Confidence distribution**: Distribution of entity confidence scores
- **Entity type coverage**: Percentage of each entity type extracted
- **Terminology mapping rate**: Percentage of entities mapped to terminologies

### Logging
```python
import logging

# Configure logging for BioBERT components
logging.getLogger('app.ml.biobert').setLevel(logging.INFO)
```

## Troubleshooting

### Common Issues

#### Model Not Loading
- Check CUDA availability: `torch.cuda.is_available()`
- Verify model path and permissions
- Check available memory (GPU/CPU)

#### Low Extraction Quality
- Adjust confidence threshold
- Enable ensemble mode
- Check input text preprocessing

#### Performance Issues
- Increase batch size for better GPU utilization
- Enable model caching
- Use GPU if available

#### Memory Issues
- Reduce batch size
- Clear CUDA cache: `torch.cuda.empty_cache()`
- Use CPU processing for large documents

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('app.ml.biobert').setLevel(logging.DEBUG)

# Test model initialization
from app.ml.biobert import get_biobert_manager
manager = get_biobert_manager()
success = manager.initialize_model()
print(f"Model initialization: {'success' if success else 'failed'}")
```

## Future Enhancements

### Planned Features
- **Multi-language support** for non-English medical texts
- **Custom model fine-tuning** for specific medical domains
- **Real-time streaming** processing for live data
- **Advanced ensemble methods** with multiple model architectures
- **Integration with FHIR** for healthcare interoperability

### Research Areas
- **Few-shot learning** for rare medical entities
- **Relationship extraction** between medical concepts
- **Clinical reasoning** and decision support
- **Federated learning** for privacy-preserving model updates