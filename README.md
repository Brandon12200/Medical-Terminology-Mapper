# Medical Terminology Mapper

A full-stack healthcare interoperability platform that intelligently maps medical terms to standardized terminologies (SNOMED CT, LOINC, RxNorm, ICD-10) using advanced NLP and fuzzy matching algorithms.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![React](https://img.shields.io/badge/React-19-61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)
![Coverage](https://img.shields.io/badge/Coverage-90%25-green)

## 🎯 Overview

Medical Terminology Mapper solves the critical healthcare challenge of terminology standardization across different systems. It provides intelligent mapping between various medical coding standards with confidence scoring, context awareness, and fuzzy matching capabilities.

### Key Features

- **🔍 Intelligent Mapping**: Advanced algorithms map terms across SNOMED CT, LOINC, RxNorm, and ICD-10
- **🧠 Context-Aware**: Considers clinical context for improved accuracy
- **📊 Confidence Scoring**: Visual confidence indicators for all mappings
- **🚀 High Performance**: Optimized fuzzy matching with multiple algorithms
- **📦 Batch Processing**: Upload CSV files for bulk term mapping
- **🌐 Modern Web UI**: React-based frontend with real-time results
- **🔌 REST API**: Well-documented API for system integration
- **🐳 Docker Ready**: Full containerization with one-command startup

## 🖥️ Live Demo

```bash
# Quick start with Docker
./start-dev.sh
```

This opens:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## 🛠️ Technology Stack

### Backend
- **Python 3.12** with **FastAPI** for high-performance async API
- **SQLite** databases with optimized indexing
- **scikit-learn** & **RapidFuzz** for fuzzy matching
- **BioBERT** for medical NLP
- **Pydantic** for data validation

### Frontend
- **React 19** with **TypeScript** for type safety
- **Vite** for lightning-fast development
- **TailwindCSS** for modern UI
- **TanStack Query** for efficient data fetching
- **Vitest** for testing

### Infrastructure
- **Docker** & **Docker Compose** for containerization
- **Nginx** for production deployment
- **GitHub Actions** ready for CI/CD

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker (optional but recommended)

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/medical-terminology-mapper.git
cd medical-terminology-mapper

# Start everything with one command
./start-dev.sh
```

### Manual Setup

#### Backend
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up terminology databases
python scripts/setup_terminology_db.py

# Start API server
python run_api.py
```

#### Frontend
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📚 API Documentation

Interactive API documentation is available at http://localhost:8000/docs

### Quick Examples

```python
# Map a single term
import requests

response = requests.post('http://localhost:8000/api/v1/map', json={
    'term': 'diabetes mellitus type 2',
    'systems': ['snomed', 'icd10'],
    'context': 'endocrine disorder'
})

print(response.json())
# Returns mapped codes with confidence scores
```

See [API Examples](docs/API_EXAMPLES.md) for comprehensive usage.

## 🧪 Testing

The project maintains >90% test coverage:

```bash
# Run backend tests
cd backend && pytest

# Run frontend tests
cd frontend && npm test

# Run integration tests
cd backend && pytest tests/integration/
```

## 📊 Performance

- **Response Time**: <50ms for single term mapping
- **Batch Processing**: 1000+ terms/minute
- **Fuzzy Match Accuracy**: 95%+ with context
- **Memory Efficient**: Optimized caching and indexing

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   FastAPI       │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────▼─────┐           ┌──────▼──────┐
              │ Mapper     │           │ Fuzzy       │
              │ Engine     │◀─────────▶│ Matcher     │
              └─────┬─────┘           └─────────────┘
                    │
         ┌──────────┴──────────┐
         │   SQLite DBs        │
         │ (SNOMED, LOINC,     │
         │  RxNorm, ICD-10)    │
         └─────────────────────┘
```

## 📁 Project Structure

```
medical-terminology-mapper/
├── backend/                    # Backend application
│   ├── api/                   # FastAPI application
│   │   ├── v1/               # API version 1
│   │   │   ├── models/       # Pydantic models
│   │   │   ├── routers/      # API endpoints
│   │   │   └── services/     # Business logic
│   │   ├── config.py         # API configuration
│   │   └── main.py           # FastAPI app
│   ├── app/                   # Core application
│   │   ├── extractors/       # Term extraction & NLP
│   │   ├── models/           # ML models & loaders
│   │   ├── standards/        # Standards implementation
│   │   │   └── terminology/  # Terminology mappers
│   │   └── utils/            # Utility functions
│   ├── cli/                   # Command-line interface
│   ├── tests/                 # Backend tests
│   ├── scripts/               # Utility scripts
│   └── requirements.txt       # Python dependencies
├── frontend/                   # React application
│   ├── src/                   # Source code
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   ├── types/           # TypeScript types
│   │   └── utils/           # Utilities
│   ├── public/               # Static assets
│   └── package.json          # Node dependencies
├── data/                      # Data files
│   └── terminology/          # Terminology databases
├── docs/                      # Documentation
├── logs/                      # Application logs
├── docker-compose.yml         # Docker orchestration
├── start-dev.sh              # Start development
├── stop-dev.sh               # Stop development
└── check-health.sh           # Health check script
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📈 Roadmap

- [ ] Additional terminology systems (CPT, HCPCS)
- [ ] Machine learning model improvements
- [ ] Real-time collaborative mapping
- [ ] FHIR server integration
- [ ] Multi-language support
