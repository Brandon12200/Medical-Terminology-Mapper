# Command Line Interface (CLI)

This directory contains the command-line interface implementations for the Medical Terminology Mapper.

## Available Commands

- `map_terms.py` - Main CLI tool for mapping medical terms to standardized terminologies

## Usage

While you can call these scripts directly, it's recommended to use the wrapper scripts in the project root:

```bash
# From project root
python map_terms.py --term "hypertension" --system snomed
```

For detailed usage information, see the [CLI Usage Guide](../docs/user_guides/cli_usage.md).

## Quick Examples

### Basic Mapping

```bash
python map_terms.py --term "diabetes mellitus type 2" --system snomed
```

### Fuzzy Matching

```bash
python map_terms.py --term "hypertenshun" --fuzzy-algorithm token
```

### Context-Aware Mapping

```bash
python map_terms.py --term "glucose" --context "diabetes monitoring" --system loinc
```

### Batch Processing

```bash
python map_terms.py --batch sample_terms.csv --output mappings.json
```

## Development Guidelines

When modifying CLI tools:

1. Follow consistent argument naming conventions
2. Provide meaningful help text for all options
3. Include examples in the help text
4. Ensure proper error handling and user feedback
5. Update tests in `tests/cli/` when adding features