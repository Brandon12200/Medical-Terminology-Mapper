# CLI Tests

This directory contains tests for the command-line interface (CLI) of the Medical Terminology Mapper.

## Test Files

- `test_cli.py` - Tests CLI functionality with various options and inputs

## Running Tests

From the project root, run:

```bash
# Run all CLI tests
pytest tests/cli/

# Run specific CLI test
python -m tests.cli.test_cli
```

## Test Coverage

The CLI tests cover:

- Basic term mapping functionality
- Fuzzy matching options
- Context-aware mapping
- Batch processing
- Output formatting
- Error handling

## Adding New Tests

When adding new tests:

1. Organize tests by functionality
2. Use clear test names that describe what is being tested
3. Include both positive and negative test cases
4. Mock external dependencies when appropriate
5. Ensure tests are deterministic and don't depend on specific data