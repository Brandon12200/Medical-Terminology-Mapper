# Document Processing Module

This module handles text extraction from uploaded documents using various extraction methods and background processing with Celery.

## Components

### 1. Text Extractor (`text_extractor.py`)
Handles text extraction from different document formats:
- **PDF**: Uses PyPDF2 with Apache Tika fallback
- **DOCX**: Uses python-docx library
- **TXT**: Direct file reading with encoding detection
- **RTF**: Uses Apache Tika
- **HL7**: Basic parsing of Health Level 7 messages

Features:
- Automatic fallback to Apache Tika for complex documents
- Text cleaning and normalization
- Metadata extraction (page count, encoding, etc.)
- Preview generation for large texts

### 2. Document Processor (`document_processor.py`)
Celery tasks for asynchronous document processing:
- `process_document`: Main task that extracts text and updates database
- `extract_document_text`: Simple text extraction task
- `cleanup_old_results`: Periodic cleanup of old processing results

Features:
- Automatic retry on failure
- Progress tracking and status updates
- Error handling and logging
- Metadata storage

## Setup

### 1. Install Redis
The system uses Redis as the Celery message broker:

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

### 2. Start Celery Worker
Run the Celery worker to process documents:

```bash
# From the backend directory
python start_celery_worker.py

# Or with custom settings
CELERY_LOG_LEVEL=DEBUG python start_celery_worker.py
```

### 3. Environment Variables
- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379/0`)
- `CELERY_LOG_LEVEL`: Logging level (default: `INFO`)

## Usage

### Document Upload with Automatic Processing
When a document is uploaded via the API, it's automatically queued for text extraction:

```python
# This happens automatically in the upload endpoint
from app.processing.document_processor import queue_document_processing

task_id = queue_document_processing(document_id)
```

### Manual Text Extraction
You can also extract text directly:

```python
from app.processing.text_extractor import TextExtractor

extractor = TextExtractor()
text, method, metadata = extractor.extract_text(
    file_path="/path/to/document.pdf",
    document_type="pdf"
)
```

### Checking Processing Status
The API provides endpoints to check document status:

```bash
# Check processing status
GET /api/v1/documents/{document_id}/status

# Get extracted text
GET /api/v1/documents/{document_id}/text
```

## Text Extraction Methods

### PyPDF2
- Primary method for PDF files
- Extracts text and metadata
- Falls back to Tika if extraction yields little content

### python-docx
- Handles Microsoft Word documents
- Extracts paragraphs and tables
- Preserves document structure

### Apache Tika
- Universal document parser
- Fallback for complex or problematic documents
- Handles RTF and other formats

### Direct Reading
- For plain text files
- Automatic encoding detection
- Supports UTF-8, UTF-16, Latin-1, and CP1252

## Error Handling

The system handles various error scenarios:
- Missing files
- Corrupted documents
- Unsupported formats
- Extraction failures

All errors are logged and stored in the database with the document record.

## Performance Considerations

- Text extraction runs asynchronously to avoid blocking the API
- Large documents are processed with streaming where possible
- Extracted text is cached in the database
- Worker concurrency can be adjusted based on system resources

## Testing

Run the text extraction tests:

```bash
# Unit tests
pytest tests/test_text_extraction.py -v

# Integration tests
pytest tests/test_document_processing.py -v

# All document-related tests
pytest tests/test_document*.py -v
```

## Future Enhancements

Planned improvements:
- OCR support for scanned PDFs
- Advanced HL7 parsing with segment extraction
- Support for additional formats (ODT, EPUB)
- Text extraction from images
- Language detection
- Section detection and structuring