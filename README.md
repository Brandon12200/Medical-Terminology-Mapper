# Medical Terminology Mapper

A comprehensive platform that leverages BioBERT and advanced NLP techniques to standardize and map medical terminology across healthcare standards including SNOMED CT, RxNorm, LOINC, FHIR, and OMOP.

## Overview

Medical Terminology Mapper addresses the critical healthcare interoperability challenge of inconsistent terminology usage across different systems and standards. The platform intelligently identifies medical terms in unstructured text and maps them to standardized terminologies while providing FHIR and OMOP output formats for seamless integration.

## Key Features

- **AI-Powered Term Recognition**: Uses BioBERT to identify medical terms in context
- **Comprehensive Terminology Support**: Maps to SNOMED CT, RxNorm, LOINC, and custom terminologies
- **Multi-Standard Output**: Generates both FHIR and OMOP formatted outputs
- **Intelligent Fuzzy Matching**: Handles spelling variations, abbreviations, and synonyms
- **Confidence Scoring**: Provides match confidence metrics for all mappings
- **Interactive Mapping UI**: Allows users to review and refine mappings visually
- **Robust API**: Well-documented REST API for integration into clinical workflows
- **Offline Capability**: Functions without external API dependencies
- **Comprehensive Audit Trail**: Tracks all mapping decisions and changes

## Use Cases

- **Clinical Data Standardization**: Convert free-text clinical notes to structured data
- **Clinical Trial Protocol Analysis**: Standardize eligibility criteria across protocols
- **Healthcare Analytics**: Ensure consistent terminology for accurate reporting
- **Research Data Integration**: Map research terms to standard medical vocabularies
- **Regulatory Submission Preparation**: Ensure terminology complies with regulatory requirements

## Technical Stack

- **Backend**: Python with Flask framework
- **NLP Engine**: BioBERT with custom medical entity recognition models
- **Database**: SQLite for terminology storage (upgradable to PostgreSQL)
- **Frontend**: HTML, CSS, JavaScript with modern framework
- **Containerization**: Docker support for easy deployment
- **Documentation**: Swagger/OpenAPI for API documentation

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/medical-terminology-mapper.git
cd medical-terminology-mapper

# Setup using Docker (recommended)
./start.sh

# Or manual setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Getting Started

1. Access the web interface at http://localhost:8000
2. Upload text with medical terminology or enter it directly
3. Review the identified terms and their mapped standard terms
4. Export the results in FHIR or OMOP format

## API Usage

```python
import requests

# Map a medical term
response = requests.post('http://localhost:8000/api/map', json={
    'text': 'Patient has elevated glucose levels and is taking metformin 500mg BID',
    'output_format': 'fhir'  # or 'omop'
})

# Get the standardized results
standardized_terms = response.json()
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
