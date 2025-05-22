#!/usr/bin/env python
"""
Setup script for terminology databases.

This script initializes the terminology databases and imports sample data.
"""

import os
import logging
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging directly
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "setup_terminology_db.log")),
        logging.StreamHandler()
    ]
)

# Import from app modules
from app.standards.terminology.db_updater import create_sample_databases

# Configure logging
logger = logging.getLogger("setup_terminology_db")

def main():
    """Run the terminology database setup process."""
    logger.info("Starting terminology database setup")
    
    # Define the data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "terminology")
    logger.info(f"Using data directory: {data_dir}")
    
    # Create sample databases
    try:
        logger.info("Creating sample databases...")
        create_sample_databases(data_dir)
        logger.info("Sample databases created successfully")
    except Exception as e:
        logger.error(f"Error creating sample databases: {e}")
        sys.exit(1)
    
    # Print status summary
    print("\nTerminology Database Setup Complete")
    print("----------------------------------")
    print(f"Sample data imported to {data_dir}")
    print("The following databases were created:")
    print("  - snomed_core.sqlite (SNOMED CT terminology)")
    print("  - loinc_core.sqlite (LOINC terminology)")
    print("  - rxnorm_core.sqlite (RxNorm terminology)")
    print("\nSample data imported from:")
    print(f"  - {os.path.join(data_dir, 'sample_data')}")
    print("\nYou can now use these databases for development and testing.")

if __name__ == "__main__":
    main()