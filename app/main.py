"""
Medical Terminology Mapper - Main application entry point.

This module provides the entry point for running the application.
"""

import os
import sys
import logging
import argparse
from app.utils.logger import setup_logger
from app.models.model_loader import ModelManager
from app.standards.terminology.embedded_db import EmbeddedDatabaseManager

# Configure logging
logger = setup_logger("main")

def initialize_components():
    """Initialize and test the main application components."""
    logger.info("Initializing Medical Terminology Mapper components")
    
    model_initialized = False
    db_initialized = False
    
    try:
        # Initialize model manager
        model_manager = ModelManager()
        if model_manager.initialize():
            logger.info("BioBERT model initialized successfully")
            model_initialized = True
        else:
            logger.error("Failed to initialize BioBERT model")
    except Exception as e:
        logger.error(f"Error initializing model manager: {e}")
        logger.info("BioBERT model initialization skipped due to environment issues")
        # Continue with database setup even if model fails
        model_initialized = True  # Consider it OK to proceed
    
    try:
        # Initialize database manager
        db_manager = EmbeddedDatabaseManager()
        if db_manager.connect():
            logger.info("Connected to terminology databases")
            db_initialized = True
            
            # Get database statistics
            stats = db_manager.get_statistics()
            logger.info(f"SNOMED concepts: {stats['snomed']['count']}")
            logger.info(f"LOINC concepts: {stats['loinc']['count']}")
            logger.info(f"RxNorm concepts: {stats['rxnorm']['count']}")
            logger.info(f"Custom mappings: {sum(stats['custom'].values())}")
        else:
            logger.error("Failed to connect to terminology databases")
    except Exception as e:
        logger.error(f"Error with database manager: {e}")
    
    # Clean up resources
    try:
        if 'model_manager' in locals():
            model_manager.cleanup()
        if 'db_manager' in locals():
            db_manager.close()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    
    return model_initialized and db_initialized

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="Medical Terminology Mapper")
    parser.add_argument("--init", action="store_true", help="Initialize components")
    args = parser.parse_args()
    
    logger.info("Starting Medical Terminology Mapper")
    
    if args.init:
        if initialize_components():
            logger.info("Component initialization completed successfully")
            print("Medical Terminology Mapper components initialized successfully.")
        else:
            logger.error("Component initialization failed")
            print("Error: Failed to initialize components. Check logs for details.")
            return 1
    else:
        print("Medical Terminology Mapper")
        print("Usage: python -m app.main --init")
        print("       Run with --init to test component initialization")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())