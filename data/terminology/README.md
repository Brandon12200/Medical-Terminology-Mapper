# Medical Terminology Database Files

This directory contains the SQLite database files for various medical terminology standards:

1. `snomed_core.sqlite` - SNOMED CT terminology database
2. `loinc_core.sqlite` - LOINC terminology database
3. `rxnorm_core.sqlite` - RxNorm terminology database
4. `custom_mappings.json` - User-defined custom mappings

## Database Structure

### SNOMED CT Database
The SNOMED CT database contains clinical terms organized by clinical concepts.

Table: `snomed_concepts`
- `id` (INTEGER): Primary key 
- `code` (TEXT): SNOMED CT concept ID
- `term` (TEXT): Term for mapping
- `display` (TEXT): Human-readable display text
- `is_active` (INTEGER): Flag indicating if concept is active (1) or inactive (0)

### LOINC Database
The LOINC database contains laboratory tests and clinical observations.

Table: `loinc_concepts`
- `id` (INTEGER): Primary key
- `code` (TEXT): LOINC code
- `term` (TEXT): Term for mapping
- `display` (TEXT): Human-readable display text
- `component` (TEXT): Component/analyte
- `property` (TEXT): Property measured
- `time` (TEXT): Time aspect
- `system` (TEXT): System (specimen)
- `scale` (TEXT): Type of scale
- `method` (TEXT): Method of measurement

### RxNorm Database
The RxNorm database contains normalized names for clinical drugs.

Table: `rxnorm_concepts`
- `id` (INTEGER): Primary key
- `code` (TEXT): RxNorm concept ID
- `term` (TEXT): Term for mapping
- `display` (TEXT): Human-readable display text
- `tty` (TEXT): Term type
- `is_active` (INTEGER): Flag indicating if concept is active (1) or inactive (0)

## Custom Mappings

The `custom_mappings.json` file contains user-defined mappings in the following format:

```json
{
  "snomed": {
    "term1": {
      "code": "123456",
      "display": "Term 1 Display Text",
      "system": "http://snomed.info/sct",
      "found": true
    }
  },
  "loinc": {
    "term2": {
      "code": "12345-6",
      "display": "Term 2 Display Text",
      "system": "http://loinc.org",
      "found": true
    }
  },
  "rxnorm": {
    "term3": {
      "code": "123456",
      "display": "Term 3 Display Text",
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "found": true
    }
  }
}
```

## Adding Data

You can populate these databases using:

1. The database import scripts in the `app/standards/terminology` module
2. Direct SQL import for large datasets
3. Manual entry through the application interface

For testing purposes, sample data files are available in the `sample_data` directory.