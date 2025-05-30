"""
Medical Terminology Mapper - Main application package.

This package provides functionality for mapping medical terms across 
different standardized terminologies.
"""

import os
import logging
from app.utils.logger import configure_root_logger

# Set up logging for the application
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
configure_root_logger(log_dir=log_dir)

# Get a logger for this module
logger = logging.getLogger(__name__)
logger.info("Initializing Medical Terminology Mapper application")

# Version information
__version__ = '0.1.0'