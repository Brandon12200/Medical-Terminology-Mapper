#!/usr/bin/env python3
"""
Start Celery worker for document processing
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from celery_config import celery_app

if __name__ == '__main__':
    # Set log level from environment or default to INFO
    log_level = os.getenv('CELERY_LOG_LEVEL', 'INFO')
    
    # Start worker
    celery_app.worker_main([
        'worker',
        '--loglevel', log_level,
        '--queues', 'document_processing,default',
        '--concurrency', '2',  # Number of worker processes
        '--pool', 'prefork',   # Use process pool
    ])