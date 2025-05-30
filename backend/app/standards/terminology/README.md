# Terminology Database Component

This component provides access to medical terminology databases for mapping medical terms across different standardized terminologies.

## Overview

The terminology component handles the storage, retrieval, and management of standardized medical terminologies including:

- **SNOMED CT**: Clinical terms and concepts
- **LOINC**: Laboratory observations and measurements
- **RxNorm**: Normalized drug names and medication information

## Files and Structure

- `embedded_db.py`: Core database manager for terminology access
- `db_updater.py`: Utilities for importing data into terminology databases
- `README.md`: This file

## Database Structure

The component uses SQLite databases for terminology storage:

- `/data/terminology/snomed_core.sqlite`: SNOMED CT terminology
- `/data/terminology/loinc_core.sqlite`: LOINC terminology
- `/data/terminology/rxnorm_core.sqlite`: RxNorm terminology
- `/data/terminology/custom_mappings.json`: User-defined custom mappings

## Usage Examples

### Connecting to the Terminology Databases

```python
from app.standards.terminology.embedded_db import EmbeddedDatabaseManager

# Initialize database manager
db_manager = EmbeddedDatabaseManager()

# Connect to databases
if db_manager.connect():
    print("Successfully connected to terminology databases")
else:
    print("Failed to connect to terminology databases")
```

### Looking Up Medical Terms

```python
# Look up a term in SNOMED CT
result = db_manager.lookup_snomed("hypertension")
if result:
    print(f"Found SNOMED code: {result['code']} - {result['display']}")

# Look up a term in LOINC
result = db_manager.lookup_loinc("blood glucose")
if result:
    print(f"Found LOINC code: {result['code']} - {result['display']}")

# Look up a term in RxNorm
result = db_manager.lookup_rxnorm("metformin")
if result:
    print(f"Found RxNorm code: {result['code']} - {result['display']}")
```

### Adding Custom Mappings

```python
# Add a custom SNOMED mapping
mapping = {
    "code": "123456",
    "display": "Custom Disorder (disorder)",
    "system": "http://snomed.info/sct",
    "found": True
}
db_manager.add_mapping("snomed", "custom term", mapping)
```

### Getting Database Statistics

```python
# Get statistics about the databases
stats = db_manager.get_statistics()
print(f"SNOMED concepts: {stats['snomed']['count']}")
print(f"LOINC concepts: {stats['loinc']['count']}")
print(f"RxNorm concepts: {stats['rxnorm']['count']}")
print(f"Custom mappings: {sum(stats['custom'].values())}")
```

### Importing Data from CSV Files

```python
from app.standards.terminology.db_updater import import_from_csv

# Import SNOMED data from a CSV file
import_from_csv(
    csv_path="/path/to/snomed_data.csv",
    db_path="/path/to/snomed_core.sqlite",
    terminology_type="snomed"
)
```

## Database Setup

To set up the terminology databases, run the `setup_terminology_db.py` script:

```bash
python setup_terminology_db.py
```

This will:
1. Create the necessary database files
2. Import sample data for testing
3. Initialize custom mappings

## Testing

To verify the terminology database functionality, run:

```bash
python test_terminology_lookup.py
```

This script demonstrates how to look up medical terms in each terminology system.