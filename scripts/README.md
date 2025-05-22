# Utility Scripts

This directory contains utility scripts for the Medical Terminology Mapper.

## Available Scripts

- `setup_terminology_db.py` - Sets up the terminology databases
- `verify_db_contents.py` - Verifies database contents and structure

## Usage

### Setting up terminology databases

```bash
python scripts/setup_terminology_db.py
```

This script will:
1. Download or use local terminology files (SNOMED CT, LOINC, RxNorm)
2. Process these files into SQLite databases
3. Place the databases in the `data/terminology` directory

### Verifying database contents

```bash
python scripts/verify_db_contents.py
```

This script will:
1. Check that all required terminology databases exist
2. Verify database structure (tables, indices)
3. Run sample queries to ensure data integrity
4. Report statistics on database contents

## Adding New Scripts

When adding new scripts to this directory:

1. Include clear documentation at the top of the script
2. Add a description in this README
3. Ensure the script has proper error handling
4. Add logging to the script for debugging
5. Consider adding tests in the `tests/scripts` directory