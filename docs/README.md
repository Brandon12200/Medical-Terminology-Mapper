# Medical Terminology Mapper Documentation

Simple, concise documentation for the Medical Terminology Mapper.

## Core Documentation

- [Usage Guide](usage.md) - How to use the application, including CLI and API
- [Fuzzy Matching](fuzzy_matching.md) - How the fuzzy matching system works
- [LOINC Integration](loinc_integration.md) - Detailed guide for LOINC terminology support

## Weekly Summaries

- [Week 5: LOINC Integration](week5_summary.md) - Implementation of LOINC terminology support

## Quick Start

```bash
# Map a term to SNOMED CT
python map_terms.py --term "hypertension" --system snomed

# Use fuzzy matching for misspelled terms
python map_terms.py --term "diabets type 2" --fuzzy-algorithm token

# Process a batch of terms with context
python map_terms.py --batch terms.csv --match-abbreviations --output mapped.json
```

See the [Usage Guide](usage.md) for detailed instructions.