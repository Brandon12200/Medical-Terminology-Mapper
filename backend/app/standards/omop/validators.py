"""
OMOP Terminology Validator for the Medical Terminology Mapper.

This module validates OMOP CDM data created during terminology mapping,
specifically focused on concept and relationship validation.

Adapted from the Clinical Protocol Extractor project with terminology-specific enhancements.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
import pandas as pd

# Set up logging
logger = logging.getLogger(__name__)

class OMOPTerminologyValidator:
    """
    Validates OMOP CDM terminology data against OMOP standards.
    
    This validator focuses on terminology-specific validation such as
    concept IDs, vocabulary consistency, and domain compliance.
    """
    
    def __init__(self):
        """Initialize OMOP terminology validator."""
        logger.info("Initializing OMOP terminology validator")
        
        # Define required fields for each table type
        self.required_fields = {
            "concept": [
                "concept_id", "concept_name", "domain_id", "vocabulary_id",
                "concept_class_id", "concept_code", "valid_start_date", "valid_end_date"
            ],
            "concept_relationship": [
                "concept_id_1", "concept_id_2", "relationship_id", 
                "valid_start_date", "valid_end_date"
            ],
            "condition_occurrence": [
                "condition_occurrence_id", "person_id", "condition_concept_id",
                "condition_start_date", "condition_type_concept_id"
            ],
            "drug_exposure": [
                "drug_exposure_id", "person_id", "drug_concept_id",
                "drug_exposure_start_date", "drug_type_concept_id"
            ],
            "procedure_occurrence": [
                "procedure_occurrence_id", "person_id", "procedure_concept_id",
                "procedure_date", "procedure_type_concept_id"
            ],
            "measurement": [
                "measurement_id", "person_id", "measurement_concept_id",
                "measurement_date", "measurement_type_concept_id"
            ],
            "observation": [
                "observation_id", "person_id", "observation_concept_id",
                "observation_date", "observation_type_concept_id"
            ]
        }
        
        # Valid OMOP vocabularies
        self.valid_vocabularies = {
            'SNOMED', 'LOINC', 'RxNorm', 'ICD10CM', 'ICD9CM', 'CPT4', 
            'HCPCS', 'NDC', 'Gender', 'Race', 'Ethnicity', 'None'
        }
        
        # Valid OMOP domains
        self.valid_domains = {
            'Condition', 'Drug', 'Procedure', 'Measurement', 'Observation',
            'Device', 'Specimen', 'Note', 'Episode', 'Provider', 'Visit',
            'Gender', 'Race', 'Ethnicity', 'Type Concept', 'Unit'
        }
        
        # Valid relationship types
        self.valid_relationships = {
            'Maps to', 'Mapped from', 'Is a', 'Subsumes', 'RxNorm has ing',
            'RxNorm ing of', 'Concept same_as from', 'Concept same_as to',
            'Concept replaces', 'Concept replaced by'
        }
        
        # Standard concept indicators
        self.valid_standard_concepts = {'S', 'C', None}
        
        # Common type concept IDs
        self.common_type_concepts = {
            32817, 32818, 32879, 32880, 32881, 45905771
        }
    
    def validate(self, tables: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Validate OMOP CDM terminology tables against standards.
        
        Args:
            tables: Dictionary of OMOP tables to validate
            
        Returns:
            dict: Validation results
        """
        try:
            logger.info("Starting OMOP CDM terminology validation")
            
            validation_issues = []
            tables_validated = 0
            
            # Validate each table
            for table_name, records in tables.items():
                if not records:
                    logger.info(f"Skipping empty table: {table_name}")
                    continue
                
                logger.info(f"Validating {table_name} with {len(records)} records")
                
                # Validate table structure
                structure_issues = self._validate_table_structure(table_name, records)
                validation_issues.extend([f"{table_name}: {issue}" for issue in structure_issues])
                
                # Validate data quality
                quality_issues = self._validate_data_quality(table_name, records)
                validation_issues.extend([f"{table_name}: {issue}" for issue in quality_issues])
                
                # Validate terminology-specific rules
                terminology_issues = self._validate_terminology_rules(table_name, records)
                validation_issues.extend([f"{table_name}: {issue}" for issue in terminology_issues])
                
                tables_validated += 1
            
            # Validate cross-table consistency
            consistency_issues = self._validate_cross_table_consistency(tables)
            validation_issues.extend(consistency_issues)
            
            # Check concept ID validity
            concept_issues = self._validate_concept_ids(tables)
            validation_issues.extend(concept_issues)
            
            # Determine overall validation status
            is_valid = len(validation_issues) == 0
            
            validation_result = {
                "valid": is_valid,
                "issues": validation_issues,
                "tables_validated": tables_validated,
                "total_records": sum(len(records) for records in tables.values()),
                "validated_at": datetime.now().isoformat(),
                "cdm_version": "5.4"
            }
            
            logger.info(f"OMOP terminology validation completed with {len(validation_issues)} issues")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error during OMOP terminology validation: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "tables_validated": 0,
                "total_records": 0,
                "validated_at": datetime.now().isoformat(),
                "cdm_version": "5.4"
            }
    
    def _validate_table_structure(self, table_name: str, records: List[Dict[str, Any]]) -> List[str]:
        """Validate table structure against OMOP CDM requirements."""
        issues = []
        
        if table_name not in self.required_fields:
            issues.append(f"Unknown table type: {table_name}")
            return issues
        
        required_fields = self.required_fields[table_name]
        
        # Check if records exist
        if not records:
            return issues
        
        # Check required fields in first record (assume all records have same structure)
        first_record = records[0]
        missing_fields = [field for field in required_fields if field not in first_record]
        
        if missing_fields:
            issues.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        return issues
    
    def _validate_data_quality(self, table_name: str, records: List[Dict[str, Any]]) -> List[str]:
        """Validate data quality within records."""
        issues = []
        
        for i, record in enumerate(records):
            # Check for null values in required fields
            if table_name in self.required_fields:
                for field in self.required_fields[table_name]:
                    if field in record and record[field] is None:
                        issues.append(f"Record {i+1}: Required field '{field}' is null")
            
            # Validate data types
            type_issues = self._validate_data_types(table_name, record, i+1)
            issues.extend(type_issues)
            
            # Validate dates
            date_issues = self._validate_dates(record, i+1)
            issues.extend(date_issues)
        
        return issues
    
    def _validate_data_types(self, table_name: str, record: Dict[str, Any], record_num: int) -> List[str]:
        """Validate data types for specific fields."""
        issues = []
        
        # Define fields that should be strings (not integers)
        string_id_fields = {'domain_id', 'vocabulary_id', 'concept_class_id', 'relationship_id'}
        
        # Check ID fields are integers (except for string ID fields)
        id_fields = [field for field in record.keys() if field.endswith('_id')]
        for field in id_fields:
            value = record.get(field)
            if value is not None:
                if field in string_id_fields:
                    # These should be strings
                    if not isinstance(value, str):
                        issues.append(f"Record {record_num}: {field} should be string, got {type(value).__name__}")
                else:
                    # These should be integers
                    if not isinstance(value, int):
                        try:
                            int(value)
                        except (ValueError, TypeError):
                            issues.append(f"Record {record_num}: {field} should be integer, got {type(value).__name__}")
        
        # Check date fields
        date_fields = [field for field in record.keys() if 'date' in field.lower()]
        for field in date_fields:
            value = record.get(field)
            if value is not None:
                if not isinstance(value, (date, datetime, str)):
                    issues.append(f"Record {record_num}: {field} should be date, got {type(value).__name__}")
        
        # Check numeric fields
        numeric_fields = ['value_as_number', 'quantity', 'days_supply', 'refills', 'range_low', 'range_high']
        for field in numeric_fields:
            if field in record:
                value = record.get(field)
                if value is not None and not isinstance(value, (int, float)):
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        issues.append(f"Record {record_num}: {field} should be numeric, got {type(value).__name__}")
        
        return issues
    
    def _validate_dates(self, record: Dict[str, Any], record_num: int) -> List[str]:
        """Validate date logic in records."""
        issues = []
        
        # Check start/end date logic
        date_pairs = [
            ('condition_start_date', 'condition_end_date'),
            ('drug_exposure_start_date', 'drug_exposure_end_date'),
            ('procedure_date', 'procedure_end_date'),
            ('valid_start_date', 'valid_end_date')
        ]
        
        for start_field, end_field in date_pairs:
            start_date = record.get(start_field)
            end_date = record.get(end_field)
            
            if start_date and end_date:
                # Convert to dates if they're strings
                try:
                    if isinstance(start_date, str):
                        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    
                    if isinstance(start_date, datetime):
                        start_date = start_date.date()
                    if isinstance(end_date, datetime):
                        end_date = end_date.date()
                    
                    if start_date > end_date:
                        issues.append(f"Record {record_num}: {start_field} ({start_date}) is after {end_field} ({end_date})")
                        
                except (ValueError, AttributeError):
                    issues.append(f"Record {record_num}: Invalid date format in {start_field} or {end_field}")
        
        return issues
    
    def _validate_terminology_rules(self, table_name: str, records: List[Dict[str, Any]]) -> List[str]:
        """Validate terminology-specific rules."""
        issues = []
        
        if table_name == "concept":
            issues.extend(self._validate_concept_table(records))
        elif table_name == "concept_relationship":
            issues.extend(self._validate_concept_relationship_table(records))
        else:
            # Domain table validation
            issues.extend(self._validate_domain_table(table_name, records))
        
        return issues
    
    def _validate_concept_table(self, records: List[Dict[str, Any]]) -> List[str]:
        """Validate CONCEPT table records."""
        issues = []
        
        for i, record in enumerate(records):
            # Check vocabulary_id is valid
            vocab_id = record.get('vocabulary_id')
            if vocab_id and vocab_id not in self.valid_vocabularies:
                issues.append(f"Record {i+1}: Invalid vocabulary_id '{vocab_id}'")
            
            # Check domain_id is valid
            domain_id = record.get('domain_id')
            if domain_id and domain_id not in self.valid_domains:
                issues.append(f"Record {i+1}: Invalid domain_id '{domain_id}'")
            
            # Check standard_concept indicator
            standard_concept = record.get('standard_concept')
            if standard_concept not in self.valid_standard_concepts:
                issues.append(f"Record {i+1}: Invalid standard_concept '{standard_concept}'")
            
            # Check concept_code is not empty
            concept_code = record.get('concept_code')
            if not concept_code or (isinstance(concept_code, str) and not concept_code.strip()):
                issues.append(f"Record {i+1}: concept_code cannot be empty")
            
            # Check concept_name is not empty
            concept_name = record.get('concept_name')
            if not concept_name or (isinstance(concept_name, str) and not concept_name.strip()):
                issues.append(f"Record {i+1}: concept_name cannot be empty")
        
        return issues
    
    def _validate_concept_relationship_table(self, records: List[Dict[str, Any]]) -> List[str]:
        """Validate CONCEPT_RELATIONSHIP table records."""
        issues = []
        
        for i, record in enumerate(records):
            # Check relationship_id is valid
            relationship_id = record.get('relationship_id')
            if relationship_id and relationship_id not in self.valid_relationships:
                issues.append(f"Record {i+1}: Unknown relationship_id '{relationship_id}' (may be custom)")
            
            # Check concept IDs are different
            concept_id_1 = record.get('concept_id_1')
            concept_id_2 = record.get('concept_id_2')
            if concept_id_1 and concept_id_2 and concept_id_1 == concept_id_2:
                issues.append(f"Record {i+1}: concept_id_1 and concept_id_2 cannot be the same")
            
            # Check for zero concept IDs
            if concept_id_1 == 0:
                issues.append(f"Record {i+1}: concept_id_1 cannot be 0")
            if concept_id_2 == 0:
                issues.append(f"Record {i+1}: concept_id_2 cannot be 0")
        
        return issues
    
    def _validate_domain_table(self, table_name: str, records: List[Dict[str, Any]]) -> List[str]:
        """Validate domain-specific table records."""
        issues = []
        
        # Get the main concept field for this table
        concept_field = None
        if 'condition' in table_name:
            concept_field = 'condition_concept_id'
        elif 'drug' in table_name:
            concept_field = 'drug_concept_id'
        elif 'procedure' in table_name:
            concept_field = 'procedure_concept_id'
        elif 'measurement' in table_name:
            concept_field = 'measurement_concept_id'
        elif 'observation' in table_name:
            concept_field = 'observation_concept_id'
        
        for i, record in enumerate(records):
            # Check main concept ID
            if concept_field:
                concept_id = record.get(concept_field)
                if concept_id == 0:
                    issues.append(f"Record {i+1}: {concept_field} is 0 (unmapped concept)")
                elif concept_id is None:
                    issues.append(f"Record {i+1}: {concept_field} is required")
            
            # Check type concept ID
            type_field = f"{table_name.split('_')[0]}_type_concept_id"
            type_concept_id = record.get(type_field)
            if type_concept_id is None:
                issues.append(f"Record {i+1}: {type_field} is required")
            elif type_concept_id not in self.common_type_concepts and type_concept_id != 0:
                issues.append(f"Record {i+1}: {type_field} '{type_concept_id}' is not a standard type concept")
            
            # Check person_id
            person_id = record.get('person_id')
            if person_id is None or person_id <= 0:
                issues.append(f"Record {i+1}: person_id must be a positive integer")
        
        return issues
    
    def _validate_cross_table_consistency(self, tables: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Validate consistency across tables."""
        issues = []
        
        # Check concept IDs referenced in domain tables exist in concept table
        if 'concept' in tables:
            concept_ids = set(record['concept_id'] for record in tables['concept'])
            
            # Check domain tables
            for table_name, records in tables.items():
                if table_name in ['concept', 'concept_relationship']:
                    continue
                
                concept_field = None
                if 'condition' in table_name:
                    concept_field = 'condition_concept_id'
                elif 'drug' in table_name:
                    concept_field = 'drug_concept_id'
                elif 'procedure' in table_name:
                    concept_field = 'procedure_concept_id'
                elif 'measurement' in table_name:
                    concept_field = 'measurement_concept_id'
                elif 'observation' in table_name:
                    concept_field = 'observation_concept_id'
                
                if concept_field:
                    for i, record in enumerate(records):
                        concept_id = record.get(concept_field)
                        if concept_id and concept_id != 0 and concept_id not in concept_ids:
                            issues.append(f"{table_name} record {i+1}: {concept_field} {concept_id} not found in concept table")
        
        # Check concept_relationship table references
        if 'concept_relationship' in tables and 'concept' in tables:
            concept_ids = set(record['concept_id'] for record in tables['concept'])
            
            for i, record in enumerate(tables['concept_relationship']):
                concept_id_1 = record.get('concept_id_1')
                concept_id_2 = record.get('concept_id_2')
                
                if concept_id_1 and concept_id_1 not in concept_ids:
                    issues.append(f"concept_relationship record {i+1}: concept_id_1 {concept_id_1} not found in concept table")
                
                if concept_id_2 and concept_id_2 not in concept_ids:
                    issues.append(f"concept_relationship record {i+1}: concept_id_2 {concept_id_2} not found in concept table")
        
        return issues
    
    def _validate_concept_ids(self, tables: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Validate concept ID usage patterns."""
        issues = []
        
        # Count unmapped concepts by table
        unmapped_counts = {}
        total_counts = {}
        
        for table_name, records in tables.items():
            if table_name in ['concept', 'concept_relationship']:
                continue
            
            concept_field = None
            if 'condition' in table_name:
                concept_field = 'condition_concept_id'
            elif 'drug' in table_name:
                concept_field = 'drug_concept_id'
            elif 'procedure' in table_name:
                concept_field = 'procedure_concept_id'
            elif 'measurement' in table_name:
                concept_field = 'measurement_concept_id'
            elif 'observation' in table_name:
                concept_field = 'observation_concept_id'
            
            if concept_field and records:
                total_count = len(records)
                unmapped_count = sum(1 for record in records if record.get(concept_field) == 0)
                
                total_counts[table_name] = total_count
                unmapped_counts[table_name] = unmapped_count
                
                if unmapped_count > 0:
                    percentage = (unmapped_count / total_count) * 100
                    issues.append(f"{table_name}: {unmapped_count}/{total_count} ({percentage:.1f}%) records have unmapped concepts")
        
        return issues
    
    def validate_table(self, table_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a single OMOP table.
        
        Args:
            table_name: Name of the table
            records: Records to validate
            
        Returns:
            dict: Validation result
        """
        try:
            issues = []
            
            # Validate structure
            structure_issues = self._validate_table_structure(table_name, records)
            issues.extend(structure_issues)
            
            # Validate data quality
            quality_issues = self._validate_data_quality(table_name, records)
            issues.extend(quality_issues)
            
            # Validate terminology rules
            terminology_issues = self._validate_terminology_rules(table_name, records)
            issues.extend(terminology_issues)
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "table": table_name,
                "record_count": len(records),
                "validated_at": datetime.now().isoformat(),
                "cdm_version": "5.4"
            }
            
        except Exception as e:
            logger.error(f"Error validating {table_name}: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "table": table_name,
                "record_count": len(records) if records else 0,
                "validated_at": datetime.now().isoformat(),
                "cdm_version": "5.4"
            }
    
    def get_cdm_version(self) -> str:
        """Return the OMOP CDM version used by the validator."""
        return "5.4"
    
    def get_supported_tables(self) -> List[str]:
        """Return list of supported OMOP table types."""
        return list(self.required_fields.keys())