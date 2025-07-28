# Medical Terminology Mapper

A comprehensive healthcare AI platform that combines BioBERT-powered medical entity extraction with intelligent terminology mapping to standardized medical vocabularies (SNOMED CT, LOINC, RxNorm).

![Python](https://img.shields.io/badge/Python-3.11-blue)
![React](https://img.shields.io/badge/React-19-61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)
![BioBERT](https://img.shields.io/badge/BioBERT-AI-brightgreen)

## 🚀 Overview

This project provides an end-to-end solution for medical document processing and terminology standardization:

1. **Document Processing**: Upload medical documents (PDF, DOCX, TXT, RTF)
2. **AI Entity Extraction**: BioBERT-powered extraction of medical entities
3. **Terminology Mapping**: Intelligent mapping to SNOMED CT, LOINC, and RxNorm
4. **Interactive Results**: Visual highlighting and confidence scoring
5. **Batch Processing**: Multi-document workflows with progress monitoring
6. **Export Options**: JSON, CSV, and Excel export formats

## 🌟 Key Features

### 📄 Document Processing
- **Multi-format Support**: PDF, DOCX, DOC, TXT, RTF, HL7
- **Text Extraction**: Apache Tika with fallbacks for robust extraction
- **Batch Upload**: Process multiple documents simultaneously
- **Progress Monitoring**: Real-time progress tracking with document-level status

### 🤖 AI-Powered Entity Extraction
- **BioBERT Integration**: State-of-the-art medical NLP model
- **Entity Types**: Conditions, medications, procedures, tests, anatomy, dosages
- **Confidence Scoring**: AI confidence calibration with temperature scaling
- **Context Preservation**: Sliding window processing for large documents
- **Negation Detection**: Identifies negated and uncertain entities

### 🎯 Intelligent Terminology Mapping
- **Multi-Standard Support**: SNOMED CT, LOINC, RxNorm
- **Fuzzy Matching**: Multiple algorithms (phonetic, token-based, character-based)
- **Context-Aware Enhancement**: Clinical context improves mapping accuracy
- **Confidence Scoring**: Visual confidence indicators for all mappings
- **Custom Mappings**: User-defined mapping rules

### 🖥️ Modern Web Interface
- **Interactive Entity Highlighting**: Color-coded entities with hover tooltips
- **Real-time Progress Monitoring**: Live updates during batch processing
- **Export Capabilities**: Download results in multiple formats
- **Responsive Design**: Works on desktop and mobile devices

### 🔧 Developer-Friendly
- **REST API**: Comprehensive API with OpenAPI documentation
- **Docker Compose**: One-command deployment
- **Background Processing**: Celery + Redis for scalable processing
- **Health Monitoring**: Built-in health checks and monitoring

## 🚀 Quick Start

### One-Command Startup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/medical-terminology-mapper.git
cd medical-terminology-mapper

# Start the entire application
./start.sh

# Access the application at http://localhost:3000
# API docs available at http://localhost:8000/docs

# Initialize/reinitialize database (if needed)
./start.sh --init-db

# Stop the application
./stop.sh

# Stop with cleanup options
./stop.sh basic    # Remove containers only
./stop.sh volumes  # Remove containers and data volumes
./stop.sh full     # Remove everything including images
```

### Manual Docker Compose

```bash
# Alternative: Manual Docker Compose control
docker-compose up -d

# Wait for services to be healthy (~2-3 minutes)
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Development Setup

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start Redis (required for background processing)
redis-server

# Start Celery worker
celery -A celery_config worker --loglevel=info

# Start backend API
python -m uvicorn api.main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev

# Access the application
open http://localhost:3000
```

## 📖 Usage Guide

### 1. Single Document Processing

1. Navigate to **Batch Document Processing**
2. Upload medical documents (PDF, DOCX, TXT, RTF)
3. Monitor processing progress in real-time
4. View extracted entities with highlighting
5. Export results in JSON, CSV, or Excel format

### 2. Entity Extraction Results

The system extracts and categorizes medical entities:

- **🩺 Conditions**: Diseases, symptoms, diagnoses
- **💊 Medications**: Drugs, dosages, frequencies  
- **🔬 Tests**: Lab tests, procedures, observations
- **🫀 Anatomy**: Body parts, organs, systems
- **📊 Procedures**: Medical procedures, treatments

### 3. Terminology Mappings

Each entity is mapped to standard terminologies:

- **SNOMED CT**: Clinical terms and concepts
- **LOINC**: Laboratory and clinical observations
- **RxNorm**: Medications and drug information

### 4. Export Options

Download processing results in multiple formats:

- **JSON**: Complete structured data with metadata
- **CSV**: Flattened data for analysis
- **Excel**: Multi-sheet workbook with entities and mappings

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Document   │───▶│ Text        │───▶│ BioBERT      │───▶│ Terminology │
│  Upload     │    │ Extraction  │    │ Extraction   │    │ Mapping     │
└─────────────┘    └─────────────┘    └──────────────┘    └─────────────┘
                                                                  │
┌─────────────┐    ┌─────────────┐    ┌──────────────┐           │
│ Web UI      │◀───│ Export      │◀───│ Results      │◀──────────┘
│ (React)     │    │ Service     │    │ Processing   │
└─────────────┘    └─────────────┘    └──────────────┘
```

### Technology Stack

**Backend**:
- FastAPI for REST API
- BioBERT for medical entity extraction
- Celery + Redis for background processing
- SQLite for data storage
- Apache Tika for document processing

**Frontend**:
- React 19 with TypeScript
- Tailwind CSS for styling
- React Query for state management
- Vite for build tooling

**Infrastructure**:
- Docker & Docker Compose
- Redis for caching and task queue
- Nginx for production deployment

## 📊 API Documentation

### Key Endpoints

```bash
# Health check
GET /health

# Upload documents for batch processing
POST /api/v1/documents/batch/upload

# Monitor batch processing status
GET /api/v1/documents/batch/{batch_id}/status

# Get batch results
GET /api/v1/documents/batch/{batch_id}/results

# Export batch results
GET /api/v1/documents/batch/{batch_id}/export/{format}

# Single document entity extraction
POST /api/v1/documents/{document_id}/extract-entities
```

### Interactive API Documentation

Once running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

### Run Tests

```bash
# Backend tests
cd backend
pytest --cov=app --cov=api

# Frontend tests  
cd frontend
npm test

# Integration tests
cd backend
python -m pytest tests/test_comprehensive_integration.py
```

### Test Coverage

The project maintains high test coverage:
- **Backend**: 85%+ coverage including API endpoints, entity extraction, and terminology mapping
- **Frontend**: 80%+ coverage for components and services
- **Integration**: End-to-end workflow testing

## 🚀 Deployment

### Production Deployment

```bash
# Build and deploy with production settings
docker-compose -f docker-compose.production.yml up -d

# Scale services
docker-compose up -d --scale celery-worker=3

# Monitor with Flower
open http://localhost:5555  # Celery task monitoring
```

### Environment Variables

Key configuration options:

```bash
# Backend
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
ENVIRONMENT=production

# Frontend  
REACT_APP_API_URL=http://localhost:8000
```

## 🔧 Configuration

### Adding Custom Mappings

```python
# Add custom terminology mappings
from app.standards.terminology.custom_mapping_rules import add_custom_mapping

add_custom_mapping(
    term="MI",
    target_system="snomed",
    target_code="22298006",
    confidence=0.95
)
```

### Adjusting AI Model Settings

```python
# Configure BioBERT model settings
MODEL_CONFIG = {
    "model_name": "dmis-lab/biobert-base-cased-v1.1",
    "confidence_threshold": 0.7,
    "max_length": 512,
    "batch_size": 16
}
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
