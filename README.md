# Medical Terminology Mapper

A comprehensive platform that maps medical terminology across healthcare standards including SNOMED CT, ICD-10, RxNorm, and LOINC.

## Overview

Medical Terminology Mapper addresses the critical healthcare interoperability challenge of inconsistent terminology usage across different systems and standards. The platform intelligently identifies medical terms and maps them to standardized terminologies while providing a robust API for seamless integration.

## Key Features

- **Comprehensive Terminology Support**: Maps between SNOMED CT, ICD-10, LOINC, and RxNorm
- **Advanced Fuzzy Matching**: Handles variations, abbreviations, and misspellings using multiple fuzzy matching algorithms
- **Context-Aware Mapping**: Improves matching accuracy by considering the clinical context
- **Relationship Awareness**: Understands relationships between terms (equivalent, broader, narrower)
- **Confidence Scoring**: Provides match confidence metrics for all mappings
- **Robust API**: Well-documented REST API for integration into clinical workflows
- **Comprehensive Audit Trail**: Tracks all mapping decisions and changes

## Technical Stack

- **Backend**: Python with Flask framework
- **Database**: SQLite for terminology storage with option to scale to PostgreSQL
- **BioBERT**: For NLP-based terminology recognition
- **Pytest**: For comprehensive testing
- **Logging**: Python's built-in logging module for structured logging

## Documentation

All documentation is available in the `docs` directory:

- [Usage Guide](docs/usage.md) - How to use the application
- [Fuzzy Matching](docs/fuzzy_matching.md) - How the fuzzy matching system works

## Project Structure

```
medical-terminology-mapper/
├── app/                      # Application code
│   ├── api/                  # API routes and controllers
│   ├── models/               # Data models and model loader
│   ├── extractors/           # Term extraction and NLP components
│   ├── standards/            # Standards implementation
│   │   └── terminology/      # Terminology-specific modules
│   └── utils/                # Utility functions
├── data/                     # Data files
│   └── terminology/          # Terminology databases and sample data
├── docs/                     # Documentation
│   ├── usage.md              # Usage documentation
│   └── fuzzy_matching.md     # Fuzzy matching explanation
├── scripts/                  # Utility scripts
├── tests/                    # Test files
├── logs/                     # Log files
├── map_terms.py              # CLI entry point
├── requirements.txt          # Python dependencies
└── README.md                 # Project overview
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/medical-terminology-mapper.git
cd medical-terminology-mapper

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python -m app.main

# Start the production server with gunicorn
gunicorn app.main:app
```

## Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific tests
pytest tests/test_fuzzy_matching.py
```

## Usage

### Command Line Interface

The project includes a comprehensive command-line interface for terminology mapping:

```bash
# Map a single term
python map_terms.py --term "diabetes mellitus type 2" --system snomed

# Use fuzzy matching for misspelled terms
python map_terms.py --term "hypertenshun" --fuzzy-algorithm token

# Map a term with context
python map_terms.py --term "glucose" --context "diabetes monitoring" --system loinc

# Process a batch of terms
python map_terms.py --batch sample_terms.csv --output mappings.json

# Enable medical abbreviation expansion
python map_terms.py --term "HTN" --match-abbreviations
```

For more CLI options and examples, see the [CLI Usage Guide](docs/cli_usage.md).

### API Usage

The REST API provides programmatic access to the terminology mapping capabilities:

#### Get all terminology systems

```
GET /api/v1/terminology
```

#### Get term details

```
GET /api/v1/terminology/:system/code/:code
```

#### Map a term from one system to another

```
POST /api/v1/mapping/translate
{
  "sourceSystem": "snomed",
  "sourceCode": "73211009",
  "targetSystem": "icd10"
}
```

#### Map a term with fuzzy matching

```
POST /api/v1/mapping/search
{
  "term": "diabetes type 2",
  "system": "snomed",
  "fuzzyMatch": true,
  "context": "patient history",
  "threshold": 0.7
}
```

#### Get relationship between terms

```
GET /api/v1/mapping/relationship?sourceSystem=snomed&sourceCode=73211009&targetSystem=icd10&targetCode=E11
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
