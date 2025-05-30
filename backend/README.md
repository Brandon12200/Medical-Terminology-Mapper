# Medical Terminology Mapper - Backend

The backend service provides the REST API and core terminology mapping functionality.

## Structure

```
backend/
├── api/                   # FastAPI application
│   ├── v1/               # API version 1
│   │   ├── models/       # Pydantic data models
│   │   ├── routers/      # API endpoint definitions
│   │   └── services/     # Business logic services
│   ├── config.py         # Configuration settings
│   └── main.py           # FastAPI app initialization
├── app/                   # Core application logic
│   ├── extractors/       # Term extraction and NLP
│   ├── models/           # ML models and loaders
│   ├── standards/        # Healthcare standards
│   │   └── terminology/  # Terminology mapping engines
│   └── utils/            # Utility functions
├── cli/                   # Command-line interface
├── tests/                 # Test suite
├── scripts/               # Utility scripts
└── requirements.txt       # Python dependencies
```

## Setup

### Prerequisites
- Python 3.12+
- pip

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up terminology databases
python scripts/setup_terminology_db.py
```

## Running the API

### Development Server

```bash
python run_api.py
```

The API will be available at http://localhost:8000

### Production Server

```bash
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## API Documentation

Interactive API documentation is automatically available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov=api

# Run specific test file
pytest tests/test_terminology_lookup.py

# Run integration tests
pytest tests/integration/
```

## CLI Usage

The backend includes a CLI for direct term mapping:

```bash
# Map a single term
python -m cli.map_terms --term "diabetes" --system snomed

# Map with context
python -m cli.map_terms --term "glucose" --context "lab test" --system loinc

# Batch process from file
python -m cli.map_terms --batch terms.csv --output results.json
```

## Configuration

Configuration is managed through environment variables or the `api/config.py` file:

- `API_ENV`: Environment (development/production)
- `LOG_LEVEL`: Logging level (INFO/DEBUG/ERROR)
- `DB_PATH`: Path to terminology databases
- `HOST`: API host (default: 0.0.0.0)
- `PORT`: API port (default: 8000)

## Key Components

### Terminology Mapper
The core mapping engine that handles:
- Exact matching
- Fuzzy matching with multiple algorithms
- Synonym resolution
- Context-aware scoring

### Fuzzy Matcher
Implements multiple fuzzy matching algorithms:
- Levenshtein distance
- Jaro-Winkler similarity
- Metaphone phonetic matching
- Token-based matching

### Database Manager
Manages SQLite databases for each terminology system:
- SNOMED CT
- LOINC
- RxNorm
- ICD-10

## Performance Optimization

- Database indexing on code and display fields
- In-memory caching of frequent queries
- Lazy loading of terminology data
- Connection pooling for concurrent requests