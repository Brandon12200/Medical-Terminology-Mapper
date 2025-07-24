"""
Celery configuration for background task processing
"""

import os
from celery import Celery
from kombu import Exchange, Queue

# Get Redis URL from environment or use default
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'medical_terminology_mapper',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.processing.document_processor']
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'app.processing.document_processor.process_document': {'queue': 'document_processing'},
        'app.processing.document_processor.extract_document_text': {'queue': 'document_processing'},
    },
    
    # Queue configuration
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('document_processing', Exchange('document_processing'), routing_key='document_processing'),
    ),
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=100,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Task execution settings
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
    
    # Retry settings
    task_autoretry_for=(Exception,),
    task_max_retries=3,
    task_retry_backoff=True,
    task_retry_backoff_max=600,
    task_retry_jitter=True,
)

# Set up periodic tasks if needed
celery_app.conf.beat_schedule = {
    # Example: Clean up old processing results
    'cleanup-old-results': {
        'task': 'app.processing.document_processor.cleanup_old_results',
        'schedule': 3600.0,  # Run every hour
    },
}