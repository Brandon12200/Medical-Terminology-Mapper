# Medical Terminology Mapper

A powerful web application for mapping medical terms to standardized healthcare terminologies (SNOMED CT, LOINC, RxNorm). Built with FastAPI and React, this tool helps healthcare professionals and developers standardize medical vocabulary for better interoperability.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![React](https://img.shields.io/badge/React-19-61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)

## Overview

The Medical Terminology Mapper provides an intuitive interface for mapping medical terms to standardized terminologies:

- **Single Term Mapping**: Look up individual medical terms with optional clinical context
- **Batch Processing**: Process hundreds or thousands of terms from CSV files
- **Multiple Terminologies**: Maps to SNOMED CT, LOINC, and RxNorm simultaneously
- **Smart Matching**: Uses exact, synonym, fuzzy, and pattern-based matching algorithms
- **Confidence Scoring**: Visual indicators showing mapping quality and reliability

## Key Features

### Intelligent Mapping Engine
- **Multi-Stage Matching Pipeline**: Exact → Synonym → Fuzzy → Pattern matching
- **Context-Aware Enhancement**: Clinical context improves mapping accuracy
- **Multiple Algorithms**: Phonetic (Soundex, Metaphone), token-based, and character-based matching
- **Confidence Scoring**: Each mapping includes a confidence score based on match quality

### Batch Processing
- **CSV Upload**: Process files with thousands of medical terms
- **Pre-built Samples**: 8 comprehensive sample files for testing:
  - Emergency Department Conditions
  - Surgical Procedures
  - Laboratory Tests
  - Hospital Medications
  - Rare Diseases
  - Comprehensive Lab Tests
  - Pediatric Conditions
  - Hospital Discharge Summary
- **Granular Progress**: Real-time progress updates every 10% with visual indicator
- **Export Options**: Download results as CSV or JSON

### Technical Architecture
- **RESTful API**: Comprehensive endpoints with OpenAPI documentation
- **External API Integration**: Comprehensive results from NIH RxNorm, Clinical Tables, and LOINC APIs
- **Optimized Local Database**: SQLite with indexed terminology data for fallback
- **Memory-Only Caching**: Fast in-memory API response caching
- **Asynchronous Processing**: Background job queue for batch operations
- **Docker Support**: Simplified one-command deployment

## Quick Start

### One-Command Startup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/medical-terminology-mapper.git
cd medical-terminology-mapper

# Start the entire application
./start.sh

# Access the application at http://localhost:5173
# API docs available at http://localhost:8000/docs

# Stop the application
./stop.sh

# Stop with cleanup options
./stop.sh basic    # Remove containers only
./stop.sh volumes  # Remove containers and data volumes
./stop.sh full     # Remove everything including images
```

### Manual Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Development Setup

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start backend API (databases auto-initialize)
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev

# Access the application
open http://localhost:5173
```

## 📖 Usage Guide

### 1. Single Term Mapping

1. Navigate to **Single Term** page
2. Enter a medical term (e.g., "diabetes", "chest pain", "amoxicillin")
3. Optionally add clinical context for better results
4. Select target systems (SNOMED, LOINC, RxNorm, or All)
5. View mapped results with confidence scores

### 2. Batch Processing

1. Click **Batch Processing** in the navigation
2. Either:
   - Upload your own CSV file (must have a "term" column)
   - Try one of the pre-built sample files
3. Monitor granular real-time progress (updates every 10% completion)
4. View results in a comprehensive table showing:
   - Original terms
   - Number of matches found
   - All terminology mappings with confidence scores
   - API sources (NIH RxNorm, Clinical Tables) or local database fallback
5. Export results as CSV or JSON

### 3. Understanding Results

- **Confidence Scores**: 
  - 🟢 High (>80%): Excellent match
  - 🟡 Medium (60-80%): Good match, review recommended
  - 🔴 Low (<60%): Weak match, manual validation needed

- **Match Types**:
  - API: Results from external terminology APIs (high quality)
  - Exact: Perfect string match in local database
  - Synonym: Matches known synonyms
  - Fuzzy: Similar terms using various algorithms
  - Pattern: Matches common medical patterns

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   React UI  │───▶│  FastAPI    │───▶│  Mapping     │───▶│ External    │
│  (TypeScript)│    │   REST API  │    │   Engine     │    │ APIs        │
└─────────────┘    └─────────────┘    └──────────────┘    │ (RxNorm,    │
                                              │            │ LOINC, etc) │
                                              │            └─────────────┘
                                              ▼                    │
                                    ┌──────────────────┐           │
                                    │ Fallback:        │◄──────────┘
                                    │ - Local SQLite   │
                                    │ - Fuzzy Match    │
                                    │ - Pattern Match  │
                                    └──────────────────┘
```

### Technology Stack

**Backend**:
- FastAPI for high-performance REST API
- External API integration (NIH RxNorm, Clinical Tables, LOINC)
- SQLite for local terminology storage (600+ medical terms for fallback)
- Pydantic for data validation
- Multiple fuzzy matching algorithms (RapidFuzz, TF-IDF, cosine similarity)

**Frontend**:
- React 19 with TypeScript
- Vite for fast development and building
- React Router for navigation
- Native fetch API for data fetching

**Infrastructure**:
- Docker & Docker Compose (simplified architecture)
- No external dependencies (Redis/Celery removed)
- GitHub Actions for CI/CD

## API Documentation

### Key Endpoints

```bash
# Health check
GET /health

# Map single term
POST /api/v1/map
Body: {
  "term": "diabetes",
  "context": "type 2",
  "systems": ["snomed", "loinc", "rxnorm"]
}

# Upload batch file
POST /api/v1/batch/upload
Body: FormData with CSV file

# Check batch status
GET /api/v1/batch/status/{job_id}

# Get batch results
GET /api/v1/batch/results/{job_id}

# Download sample files
GET /api/v1/test-files/{filename}
```

### Interactive API Documentation

Once running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

### Run Tests

```bash
# Backend tests
cd backend
pytest

# Run with coverage
pytest --cov=app

# Run specific test files
pytest tests/test_fuzzy_matching.py
pytest tests/test_terminology_lookup.py
```

### Linting and Formatting

```bash
# Format code
black .

# Sort imports
isort .

# Run linting
flake8
```

## Configuration

### Database Setup

The application uses both external APIs and local databases:

**External APIs** (primary source):
- **NIH RxNorm API**: Comprehensive medication terminology
- **Clinical Tables API**: LOINC lab tests, SNOMED concepts
- **LOINC FHIR API**: Laboratory observations

**Local SQLite Databases** (fallback):
- **SNOMED CT**: 600+ common medical concepts
- **LOINC**: Laboratory and clinical observations  
- **RxNorm**: Medication terminology

Databases auto-initialize on first startup. No manual setup required.

### Adding Custom Mappings

Create custom mapping rules by editing:
```python
# backend/app/standards/terminology/custom_mapping_rules.py
CUSTOM_MAPPINGS = {
    "your_term": {
        "snomed": {"code": "123456", "display": "Your Concept"},
        "confidence": 0.95
    }
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.