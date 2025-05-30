#!/usr/bin/env python3
"""
Download AI models for the Medical Terminology Mapper.
This script downloads the BioBERT model for medical term extraction.
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.models.model_loader import ModelManager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def download_biobert_model():
    """Download the BioBERT model and save it locally."""
    logger.info("Starting BioBERT model download...")
    
    try:
        # Initialize model manager
        manager = ModelManager()
        
        # Initialize the model (this will download if needed)
        logger.info("Downloading BioBERT model from HuggingFace...")
        logger.info("This may take a few minutes (model size: ~420MB)")
        
        manager.initialize()
        model = manager.get_model()
        tokenizer = manager.get_tokenizer()
        
        if tokenizer and model:
            logger.info("✅ BioBERT model downloaded successfully!")
            logger.info(f"Model saved at: {manager.model_path}")
            
            # Test the model
            test_text = "Patient has diabetes mellitus type 2"
            logger.info(f"Testing model with: '{test_text}'")
            
            inputs = tokenizer(test_text, return_tensors="pt", truncation=True, padding=True)
            logger.info("✅ Model is working correctly!")
            
            return True
        else:
            logger.error("Failed to download model")
            return False
            
    except Exception as e:
        logger.error(f"Error downloading model: {str(e)}")
        logger.info("\nTroubleshooting:")
        logger.info("1. Check your internet connection")
        logger.info("2. Ensure you have enough disk space (~500MB)")
        logger.info("3. Try again with: python scripts/download_models.py")
        return False

def main():
    """Main function."""
    print("🤖 Medical Terminology Mapper - AI Model Setup")
    print("=" * 50)
    
    # Check if transformers is installed
    try:
        import transformers
        print(f"✅ Transformers library version: {transformers.__version__}")
    except ImportError:
        print("❌ Transformers library not installed!")
        print("Run: pip install transformers torch")
        sys.exit(1)
    
    # Download the model
    success = download_biobert_model()
    
    if success:
        print("\n✅ AI model setup complete!")
        print("The Medical Terminology Mapper now has AI-powered term extraction enabled.")
    else:
        print("\n❌ AI model setup failed. Please check the logs and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()