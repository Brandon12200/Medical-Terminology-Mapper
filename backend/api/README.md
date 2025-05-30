# Medical Terminology Mapper API

This is the REST API for the Medical Terminology Mapper, providing endpoints to map medical terms to standardized terminologies (SNOMED CT, LOINC, RxNorm).

## Features

- Single term mapping with fuzzy matching
- Batch term processing
- File upload support (CSV, JSON, Excel, TXT)
- Multiple fuzzy matching algorithms
- Context-aware mapping
- Async processing for better performance
- Comprehensive API documentation

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python run_api.py
```

The API will be available at `http://localhost:8000`

### 3. Access API Documentation

- Interactive docs (Swagger UI): `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI schema: `http://localhost:8000/api/openapi.json`

## API Endpoints

### Health Check
- `GET /api/v1/health` - Check if the API is running

### Term Mapping
- `POST /api/v1/map` - Map a single medical term
- `GET /api/v1/map` - Map a term using query parameters

### Batch Processing
- `POST /api/v1/batch` - Map multiple terms in one request
- `POST /api/v1/batch/upload` - Upload a file for batch processing
- `GET /api/v1/batch/status/{job_id}` - Check batch job status
- `GET /api/v1/batch/result/{job_id}` - Get batch job results
- `GET /api/v1/batch/download/{job_id}.{format}` - Download results (csv/json)

### System Information
- `GET /api/v1/systems` - List available terminology systems
- `GET /api/v1/fuzzy-algorithms` - List available fuzzy matching algorithms
- `GET /api/v1/statistics` - Get system statistics

## Example Usage

### Map a Single Term

```bash
curl -X POST "http://localhost:8000/api/v1/map" \
  -H "Content-Type: application/json" \
  -d '{
    "term": "diabetes type 2",
    "systems": ["snomed"],
    "fuzzy_threshold": 0.8,
    "max_results": 5
  }'
```

### Batch Map Terms

```bash
curl -X POST "http://localhost:8000/api/v1/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "terms": ["diabetes", "hypertension", "aspirin"],
    "systems": ["snomed", "rxnorm"],
    "max_results_per_term": 3
  }'
```

### Upload File for Batch Processing

```bash
curl -X POST "http://localhost:8000/api/v1/batch/upload" \
  -F "file=@medical_terms.csv" \
  -F "file_format=csv" \
  -F "column_name=term" \
  -F "systems=snomed" \
  -F "systems=loinc"
```

## Configuration

The API can be configured using environment variables or by creating a `.env` file:

```env
# Server settings
HOST=0.0.0.0
PORT=8000
RELOAD=true

# CORS settings
CORS_ORIGINS=["http://localhost:3000"]

# File upload settings
MAX_UPLOAD_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads
RESULTS_DIR=results

# Batch processing
BATCH_SIZE=50
MAX_BATCH_TERMS=1000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/api.log
```

## Testing

Run the test script to verify all endpoints are working:

```bash
python test_api.py
```

## Production Deployment

For production deployment:

1. Set `RELOAD=false` in environment
2. Use multiple workers: `uvicorn api.main:app --workers 4`
3. Use a production ASGI server like Gunicorn:
   ```bash
   gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
4. Configure proper CORS origins
5. Set up SSL/TLS
6. Use a reverse proxy (nginx, Apache)

## Architecture

The API is built with:
- **FastAPI** - Modern, fast web framework
- **Pydantic** - Data validation and serialization
- **Uvicorn** - ASGI server
- **AsyncIO** - Asynchronous processing

It integrates with the existing terminology mapping system, reusing all the core functionality from the CLI version.