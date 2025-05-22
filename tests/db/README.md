# Database Tests

This directory contains tests for the database components of the Medical Terminology Mapper.

## Test Files

- `test_db_only.py` - Tests database functionality in isolation
- `test_terminology_lookup.py` - Tests terminology lookup functionality

## Running Tests

From the project root, run:

```bash
# Run all database tests
pytest tests/db/

# Run specific database test
python -m tests.db.test_db_only
```

## Test Coverage

The database tests cover:

- Database connection and initialization
- Terminology lookup functionality
- Database schema validation
- Performance testing for common queries
- Error handling for database operations

## Adding New Tests

When adding new tests:

1. Create isolated test databases rather than using production data
2. Use fixtures to set up and tear down test databases
3. Test both successful operations and error handling
4. Include performance tests for critical database operations
5. Verify database integrity after test operations