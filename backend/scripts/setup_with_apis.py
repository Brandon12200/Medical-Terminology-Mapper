#!/usr/bin/env python3
"""
Enhanced setup script for terminology databases with API configuration.

This script:
1. Sets up local terminology databases
2. Configures external API access
3. Tests API connections
4. Updates configuration files
"""

import os
import json
import logging
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.logger import setup_logger
from app.standards.terminology.db_updater import create_sample_databases
from app.standards.terminology.api_services import TerminologyAPIService

# Configure logging
logger = setup_logger("setup_with_apis", 
                     log_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                          "logs", "setup_with_apis.log"))


def update_configuration(config_path: str, enable_apis: bool = True):
    """Update configuration to enable API services."""
    logger.info(f"Updating configuration at {config_path}")
    
    # Load existing config
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # Update external services configuration
    if 'external_services' not in config:
        config['external_services'] = {}
    
    config['external_services'].update({
        "use_external_services": enable_apis,
        "use_rxnav_api": True,
        "use_clinical_tables_api": True,
        "use_snomed_browser_api": True,
        "api_cache_ttl_days": 7,
        "api_timeout_seconds": 30
    })
    
    # Ensure matching configuration is set up
    if 'matching' not in config:
        config['matching'] = {}
    
    config['matching'].update({
        "enable_fuzzy_matching": True,
        "fuzzy_threshold": 0.6,
        "enable_context_aware_matching": True,
        "enable_api_fallback": enable_apis,
        "max_results": 5
    })
    
    # Save updated config
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info("Configuration updated successfully")
    return config


def test_api_connectivity():
    """Test connectivity to all external APIs."""
    logger.info("Testing API connectivity...")
    print("\nTesting External API Connectivity")
    print("=" * 50)
    
    api_service = TerminologyAPIService()
    results = {
        "RxNorm API": False,
        "Clinical Tables API": False,
        "SNOMED Browser API": False
    }
    
    # Test RxNorm API
    print("\n1. Testing RxNorm API (rxnav.nlm.nih.gov)...")
    try:
        rxnorm_results = api_service.search_rxnorm("aspirin")
        if rxnorm_results:
            results["RxNorm API"] = True
            print(f"   ✓ Success! Found {len(rxnorm_results)} results")
            print(f"   Example: {rxnorm_results[0]['display']} ({rxnorm_results[0]['code']})")
        else:
            print("   ✗ No results returned")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test Clinical Tables API
    print("\n2. Testing Clinical Tables API (clinicaltables.nlm.nih.gov)...")
    try:
        ct_results = api_service.search_clinical_tables("diabetes", "icd10")
        if ct_results:
            results["Clinical Tables API"] = True
            print(f"   ✓ Success! Found {len(ct_results)} results")
            print(f"   Example: {ct_results[0]['display']} ({ct_results[0]['code']})")
        else:
            print("   ✗ No results returned")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test SNOMED Browser API
    print("\n3. Testing SNOMED Browser API (browser.ihtsdotools.org)...")
    try:
        snomed_results = api_service.search_snomed_browser("pneumonia")
        if snomed_results:
            results["SNOMED Browser API"] = True
            print(f"   ✓ Success! Found {len(snomed_results)} results")
            print(f"   Example: {snomed_results[0]['display']} ({snomed_results[0]['code']})")
        else:
            print("   ✗ No results returned")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Summary
    print("\nAPI Connectivity Summary:")
    print("-" * 30)
    for api, status in results.items():
        status_str = "✓ Available" if status else "✗ Unavailable"
        print(f"{api:.<25} {status_str}")
    
    return all(results.values())


def setup_api_cache():
    """Set up cache directory for API responses."""
    cache_dirs = [
        "app/cache/api_cache",
        "backend/app/cache/api_cache"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(os.path.dirname(cache_dir)):
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"Created API cache directory: {cache_dir}")
            # Create .gitignore in cache directory
            gitignore_path = os.path.join(cache_dir, ".gitignore")
            with open(gitignore_path, 'w') as f:
                f.write("# Ignore all cached API responses\n*\n!.gitignore\n")
            return cache_dir
    
    return None


def main():
    """Run the enhanced setup process."""
    logger.info("Starting enhanced terminology database setup with API configuration")
    
    print("\nMedical Terminology Mapper - Enhanced Setup")
    print("=" * 50)
    print("This script will:")
    print("1. Set up local terminology databases")
    print("2. Configure access to free public APIs")
    print("3. Test API connectivity")
    print("4. Update configuration files")
    
    # Step 1: Create local databases
    print("\nStep 1: Setting up local databases...")
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           "data", "terminology")
    
    try:
        create_sample_databases(data_dir)
        print("✓ Local databases created successfully")
    except Exception as e:
        logger.error(f"Error creating databases: {e}")
        print(f"✗ Error creating databases: {e}")
        sys.exit(1)
    
    # Step 2: Set up API cache
    print("\nStep 2: Setting up API cache...")
    cache_dir = setup_api_cache()
    if cache_dir:
        print(f"✓ API cache directory created: {cache_dir}")
    else:
        print("⚠ Could not create cache directory, API responses won't be cached")
    
    # Step 3: Update configuration
    print("\nStep 3: Updating configuration...")
    config_paths = [
        os.path.join(data_dir, "mapping_config.json"),
        os.path.join(os.path.dirname(data_dir), "mapping_config.json")
    ]
    
    config_updated = False
    for config_path in config_paths:
        try:
            update_configuration(config_path, enable_apis=True)
            print(f"✓ Configuration updated: {config_path}")
            config_updated = True
            break
        except Exception as e:
            logger.warning(f"Could not update config at {config_path}: {e}")
    
    if not config_updated:
        print("⚠ Could not update configuration file")
    
    # Step 4: Test API connectivity
    print("\nStep 4: Testing API connectivity...")
    api_test_success = test_api_connectivity()
    
    # Print summary
    print("\n" + "=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    print("\nLocal Database Summary:")
    print(f"  - Location: {data_dir}")
    print("  - SNOMED CT: ~385 concepts")
    print("  - LOINC: ~90 concepts")
    print("  - RxNorm: ~124 concepts")
    
    print("\nAPI Access Summary:")
    print("  All APIs are FREE and require NO authentication!")
    print("  - RxNorm API: Access to 100,000+ medications")
    print("  - Clinical Tables API: ICD-10, LOINC, SNOMED, RxNorm")
    print("  - SNOMED Browser API: 350,000+ clinical concepts")
    
    if api_test_success:
        print("\n✓ All APIs are accessible and working!")
    else:
        print("\n⚠ Some APIs may be unavailable. The system will use local data as fallback.")
    
    print("\nConfiguration:")
    print("  - External APIs: ENABLED")
    print("  - API response caching: ENABLED (7 days)")
    print("  - Automatic fallback: Local DB → Fuzzy Match → API")
    
    print("\nTo disable API access, set 'use_external_services': false in mapping_config.json")
    print("\nThe mapper will now automatically use APIs when local lookups fail!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\nSetup failed: {e}")
        sys.exit(1)