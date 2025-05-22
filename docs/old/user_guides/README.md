# User Guides

This directory contains user-oriented documentation for the Medical Terminology Mapper.

## Available Guides

- [CLI Usage Guide](cli_usage.md) - Comprehensive guide to using the command-line interface
- [Fuzzy Matching Guide](fuzzy_matching.md) - Technical details of the fuzzy matching implementation

## Usage Examples

### Basic CLI Examples

```bash
# Map a single term to SNOMED CT
python map_terms.py --term "hypertension" --system snomed

# Map a term with fuzzy matching
python map_terms.py --term "diabets type 2" --fuzzy-algorithm token

# Process a batch of terms
python map_terms.py --batch sample_terms.csv --output mappings.json
```

### Python API Examples

```python
from app.standards.terminology.mapper import TerminologyMapper

# Initialize mapper
config = {"data_dir": "data/terminology"}
mapper = TerminologyMapper(config)
mapper.initialize()

# Map a term
result = mapper.map_term("diabetes mellitus", "snomed")
print(f"Found: {result['display']} (Code: {result['code']})")
```

See individual guides for detailed usage information.