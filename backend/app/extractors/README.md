# Term Recognition Engine

This directory will contain the term recognition engine components for Week 2 implementation.

## Planned Components

The following components will be developed during Week 2:

1. **term_extractor.py**
   - Adapted from entity_extractor.py in the original project
   - Focus on medical terminology recognition
   - Enhanced with confidence scoring and context awareness

2. **term_cache.py**
   - Caching mechanism for recognized medical terms
   - Adapted from entity_cache.py in the original project

3. **regex_patterns.py**
   - Regular expression patterns specific to medical terminology
   - Fallback mechanism when BioBERT model is unavailable

## Integration Points

The term recognition engine will integrate with:

- **BioBERT Model**: Using the model_loader.py from Week 1
- **Terminology Databases**: Using the embedded_db.py from Week 1

## Implementation Plan

1. First, adapt entity_extractor.py to focus on terminology recognition
2. Then implement the BioBERT processing pipeline
3. Finally, add the testing framework

## Testing Strategy

- Unit tests for individual extractors
- Integration tests for the complete recognition pipeline
- Performance benchmarks for recognition accuracy

## Usage Example (Future Implementation)

```python
from app.extractors.term_extractor import TermExtractor
from app.models.model_loader import ModelManager

# Initialize components
model_manager = ModelManager()
model_manager.initialize()

# Create term extractor
extractor = TermExtractor(
    model=model_manager.get_model(),
    tokenizer=model_manager.get_tokenizer(),
    entity_labels=model_manager.get_entity_labels()
)

# Extract medical terms from text
text = "Patient has hypertension and diabetes mellitus type 2."
terms = extractor.extract_terms(text)

# Process the extracted terms
for term in terms:
    print(f"Term: {term.text}")
    print(f"Type: {term.type}")
    print(f"Confidence: {term.confidence}")
    print(f"Position: {term.start}-{term.end}")
    print()
```