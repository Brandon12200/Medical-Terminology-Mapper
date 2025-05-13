# Medical Terminology Mapper

A comprehensive platform that maps medical terminology across healthcare standards including SNOMED CT, ICD-10, RxNorm, and LOINC.

## Overview

Medical Terminology Mapper addresses the critical healthcare interoperability challenge of inconsistent terminology usage across different systems and standards. The platform intelligently identifies medical terms and maps them to standardized terminologies while providing a robust API for seamless integration.

## Key Features

- **Comprehensive Terminology Support**: Maps between SNOMED CT, ICD-10, LOINC, and RxNorm
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

## Project Structure

```
medical-terminology-mapper/
├── app/                      # Application code
│   ├── api/                  # API routes and controllers
│   ├── services/             # Business logic and services
│   ├── models/               # Data models and model loader
│   ├── utils/                # Utility functions
│   ├── standards/            # Standards implementation (FHIR, OMOP)
│   │   └── terminology/      # Terminology-specific modules
│   └── __init__.py           # Application initialization
├── data/                     # Data files
│   └── terminology/          # Terminology databases and sample data
├── tests/                    # Test files
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── logs/                     # Log files
├── .gitignore                # Git ignore file
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup
└── pytest.ini                # Pytest configuration
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

# Run specific test modules
pytest tests/unit/
```

## API Usage

### Get all terminology systems

```
GET /api/v1/terminology
```

### Get term details

```
GET /api/v1/terminology/:system/code/:code
```

### Map a term from one system to another

```
POST /api/v1/mapping/translate
{
  "sourceSystem": "snomed",
  "sourceCode": "73211009",
  "targetSystem": "icd10"
}
```

### Get relationship between terms

```
GET /api/v1/mapping/relationship?sourceSystem=snomed&sourceCode=73211009&targetSystem=icd10&targetCode=E11
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
