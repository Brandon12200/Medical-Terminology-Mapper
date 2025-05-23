"""
OMOP Terminology Converter for the Medical Terminology Mapper.

This module handles the conversion of terminology mapping results to OMOP CDM format,
specifically focused on concept and relationship mapping.

Adapted from the Clinical Protocol Extractor project with terminology-specific enhancements.
"""

import os
import json
import uuid
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
import pandas as pd

# Set up logging
logger = logging.getLogger(__name__)

class OMOPTerminologyConverter:
    """
    Converts terminology mapping results to OMOP CDM format.
    
    This converter focuses on creating OMOP-compliant terminology records
    such as CONCEPT, CONCEPT_RELATIONSHIP, and domain-specific tables.
    """
    
    def __init__(self, terminology_mapper=None, config=None):
        """
        Initialize OMOP terminology converter.
        
        Args:
            terminology_mapper: Optional mapper for clinical terminology
            config: Optional configuration dictionary
        """
        self.terminology_mapper = terminology_mapper
        self.config = config or {}
        
        # OMOP domain mappings
        self.domain_mappings = {
            'snomed': {
                'condition': 'Condition',
                'procedure': 'Procedure', 
                'drug': 'Drug',
                'device': 'Device',
                'observation': 'Observation'
            },
            'loinc': 'Measurement',
            'rxnorm': 'Drug'
        }
        
        # Standard OMOP concept type mappings
        self.concept_class_mappings = {
            'snomed': {
                'condition': 'Clinical Finding',
                'procedure': 'Procedure',
                'drug': 'Substance',
                'observation': 'Observable Entity'
            },
            'loinc': 'Lab Test',
            'rxnorm': {
                'ingredient': 'Ingredient',
                'brand': 'Brand Name',
                'clinical_drug': 'Clinical Drug'
            }
        }
        
        # Type concept IDs for different record types
        self.type_concept_ids = {
            'ehr_record': 32817,
            'claim_record': 32818,
            'protocol_record': 32879,
            'survey_record': 45905771
        }
        
        logger.info("Initialized OMOP terminology converter")
    
    def convert_mappings_to_concepts(self, mappings: List[Dict[str, Any]], 
                                   include_source_concepts: bool = True) -> List[Dict[str, Any]]:
        """
        Convert terminology mappings to OMOP CONCEPT records.
        
        Args:
            mappings: List of terminology mapping results
            include_source_concepts: Whether to include source concepts
            
        Returns:
            list: OMOP CONCEPT records
        """
        try:
            logger.info(f"Converting {len(mappings)} mappings to OMOP CONCEPT records")
            
            concepts = []
            concept_id_counter = 2000000000  # Start with high number to avoid conflicts
            
            for mapping in mappings:
                if not mapping.get('found', False):
                    continue
                
                # Create standard concept record
                standard_concept = {
                    'concept_id': concept_id_counter,
                    'concept_name': mapping.get('display', mapping.get('code', 'Unknown')),
                    'domain_id': self._determine_domain(mapping),
                    'vocabulary_id': self._get_vocabulary_id(mapping.get('system', '')),
                    'concept_class_id': self._determine_concept_class(mapping),
                    'standard_concept': 'S',  # Standard concept
                    'concept_code': mapping.get('code', ''),
                    'valid_start_date': date.today(),
                    'valid_end_date': date(2099, 12, 31),
                    'invalid_reason': None
                }
                
                concepts.append(standard_concept)
                concept_id_counter += 1
                
                # Create source concept if requested and different from standard
                if include_source_concepts and 'original_text' in mapping:
                    if mapping['original_text'] != mapping.get('display', ''):
                        source_concept = {
                            'concept_id': concept_id_counter,
                            'concept_name': mapping['original_text'],
                            'domain_id': self._determine_domain(mapping),
                            'vocabulary_id': 'None',  # Source vocabulary
                            'concept_class_id': 'Undefined',
                            'standard_concept': None,  # Source concept
                            'concept_code': mapping['original_text'],
                            'valid_start_date': date.today(),
                            'valid_end_date': date(2099, 12, 31),
                            'invalid_reason': None
                        }
                        
                        concepts.append(source_concept)
                        concept_id_counter += 1
            
            logger.info(f"Created {len(concepts)} OMOP CONCEPT records")
            return concepts
            
        except Exception as e:
            logger.error(f"Error converting mappings to concepts: {e}")
            raise
    
    def convert_mappings_to_concept_relationships(self, mappings: List[Dict[str, Any]], 
                                                concepts: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Convert terminology mappings to OMOP CONCEPT_RELATIONSHIP records.
        
        Args:
            mappings: List of terminology mapping results
            concepts: Optional list of CONCEPT records to reference
            
        Returns:
            list: OMOP CONCEPT_RELATIONSHIP records
        """
        try:
            logger.info(f"Converting {len(mappings)} mappings to CONCEPT_RELATIONSHIP records")
            
            relationships = []
            
            # Create concept lookup if concepts provided
            concept_lookup = {}
            if concepts:
                for concept in concepts:
                    code = concept.get('concept_code', '')
                    vocab = concept.get('vocabulary_id', '')
                    key = f"{vocab}:{code}"
                    concept_lookup[key] = concept['concept_id']
            
            for mapping in mappings:
                if not mapping.get('found', False):
                    continue
                
                # Create "Maps to" relationship if we have source and target concepts
                if 'original_text' in mapping and mapping['original_text'] != mapping.get('display', ''):
                    system = mapping.get('system', '')
                    vocab_id = self._get_vocabulary_id(system)
                    
                    # Find source and target concept IDs
                    source_key = f"None:{mapping['original_text']}"
                    target_key = f"{vocab_id}:{mapping.get('code', '')}"
                    
                    source_concept_id = concept_lookup.get(source_key)
                    target_concept_id = concept_lookup.get(target_key)
                    
                    if source_concept_id and target_concept_id:
                        # Create "Maps to" relationship
                        maps_to_relationship = {
                            'concept_id_1': source_concept_id,
                            'concept_id_2': target_concept_id,
                            'relationship_id': 'Maps to',
                            'valid_start_date': date.today(),
                            'valid_end_date': date(2099, 12, 31),
                            'invalid_reason': None
                        }
                        
                        relationships.append(maps_to_relationship)
                        
                        # Create reverse "Mapped from" relationship
                        mapped_from_relationship = {
                            'concept_id_1': target_concept_id,
                            'concept_id_2': source_concept_id,
                            'relationship_id': 'Mapped from',
                            'valid_start_date': date.today(),
                            'valid_end_date': date(2099, 12, 31),
                            'invalid_reason': None
                        }
                        
                        relationships.append(mapped_from_relationship)
                
                # Add confidence as custom relationship if available
                if 'confidence' in mapping and mapping['confidence'] < 1.0:
                    # This would require custom relationship types in OMOP
                    logger.debug(f"Mapping confidence {mapping['confidence']} could be stored as custom relationship")
            
            logger.info(f"Created {len(relationships)} CONCEPT_RELATIONSHIP records")
            return relationships
            
        except Exception as e:
            logger.error(f"Error converting mappings to concept relationships: {e}")
            raise
    
    def convert_mappings_to_domain_tables(self, mappings: List[Dict[str, Any]], 
                                        person_id: int = 1,
                                        record_date: date = None,
                                        record_type: str = 'protocol_record') -> Dict[str, List[Dict[str, Any]]]:
        """
        Convert terminology mappings to domain-specific OMOP tables.
        
        Args:
            mappings: List of terminology mapping results
            person_id: Person ID for the records
            record_date: Date for the records
            record_type: Type of record being created
            
        Returns:
            dict: Domain tables with records
        """
        try:
            logger.info(f"Converting {len(mappings)} mappings to domain tables")
            
            if record_date is None:
                record_date = date.today()
            
            domain_tables = {
                'condition_occurrence': [],
                'drug_exposure': [],
                'procedure_occurrence': [],
                'measurement': [],
                'observation': []
            }
            
            record_id_counters = {table: 1 for table in domain_tables.keys()}
            
            for mapping in mappings:
                if not mapping.get('found', False):
                    continue
                
                domain = self._determine_domain(mapping)
                system = mapping.get('system', '')
                
                # Determine which table to use based on domain and system
                table_name = None
                if domain == 'Condition' or 'snomed' in system.lower():
                    if 'condition' in mapping.get('category', '').lower():
                        table_name = 'condition_occurrence'
                    elif 'procedure' in mapping.get('category', '').lower():
                        table_name = 'procedure_occurrence'
                    else:
                        table_name = 'observation'  # Default for SNOMED
                elif domain == 'Drug' or 'rxnorm' in system.lower():
                    table_name = 'drug_exposure'
                elif domain == 'Measurement' or 'loinc' in system.lower():
                    table_name = 'measurement'
                else:
                    table_name = 'observation'  # Default fallback
                
                if table_name and table_name in domain_tables:
                    record = self._create_domain_record(
                        table_name, mapping, person_id, record_date,
                        record_id_counters[table_name], record_type
                    )
                    domain_tables[table_name].append(record)
                    record_id_counters[table_name] += 1
            
            # Remove empty tables
            domain_tables = {k: v for k, v in domain_tables.items() if v}
            
            logger.info(f"Created records in {len(domain_tables)} domain tables")
            return domain_tables
            
        except Exception as e:
            logger.error(f"Error converting mappings to domain tables: {e}")
            raise
    
    def _create_domain_record(self, table_name: str, mapping: Dict[str, Any], 
                            person_id: int, record_date: date, 
                            record_id: int, record_type: str) -> Dict[str, Any]:
        """Create a record for a specific domain table."""
        
        base_record = {
            'person_id': person_id,
            f'{table_name.split("_")[0]}_date': record_date,
            f'{table_name.split("_")[0]}_datetime': datetime.combine(record_date, datetime.min.time()),
            f'{table_name.split("_")[0]}_type_concept_id': self.type_concept_ids.get(record_type, 32817),
            f'{table_name.split("_")[0]}_source_value': mapping.get('original_text', mapping.get('display', '')),
            'provider_id': None,
            'visit_occurrence_id': None
        }
        
        if table_name == 'condition_occurrence':
            record = {
                'condition_occurrence_id': record_id,
                'condition_concept_id': self._get_standard_concept_id(mapping),
                'condition_start_date': record_date,
                'condition_start_datetime': datetime.combine(record_date, datetime.min.time()),
                'condition_end_date': None,
                'condition_end_datetime': None,
                'condition_type_concept_id': self.type_concept_ids.get(record_type, 32817),
                'condition_status_concept_id': None,
                'stop_reason': None,
                'provider_id': None,
                'visit_occurrence_id': None,
                'visit_detail_id': None,
                'condition_source_value': mapping.get('original_text', mapping.get('display', '')),
                'condition_source_concept_id': 0,
                'condition_status_source_value': None,
                **base_record
            }
            
        elif table_name == 'drug_exposure':
            record = {
                'drug_exposure_id': record_id,
                'drug_concept_id': self._get_standard_concept_id(mapping),
                'drug_exposure_start_date': record_date,
                'drug_exposure_start_datetime': datetime.combine(record_date, datetime.min.time()),
                'drug_exposure_end_date': record_date,
                'drug_exposure_end_datetime': datetime.combine(record_date, datetime.min.time()),
                'verbatim_end_date': None,
                'drug_type_concept_id': self.type_concept_ids.get(record_type, 32817),
                'stop_reason': None,
                'refills': None,
                'quantity': None,
                'days_supply': None,
                'sig': None,
                'route_concept_id': None,
                'lot_number': None,
                'provider_id': None,
                'visit_occurrence_id': None,
                'visit_detail_id': None,
                'drug_source_value': mapping.get('original_text', mapping.get('display', '')),
                'drug_source_concept_id': 0,
                'route_source_value': None,
                'dose_unit_source_value': None,
                **base_record
            }
            
        elif table_name == 'procedure_occurrence':
            record = {
                'procedure_occurrence_id': record_id,
                'procedure_concept_id': self._get_standard_concept_id(mapping),
                'procedure_date': record_date,
                'procedure_datetime': datetime.combine(record_date, datetime.min.time()),
                'procedure_end_date': None,
                'procedure_end_datetime': None,
                'procedure_type_concept_id': self.type_concept_ids.get(record_type, 32817),
                'modifier_concept_id': None,
                'quantity': None,
                'provider_id': None,
                'visit_occurrence_id': None,
                'visit_detail_id': None,
                'procedure_source_value': mapping.get('original_text', mapping.get('display', '')),
                'procedure_source_concept_id': 0,
                'modifier_source_value': None,
                **base_record
            }
            
        elif table_name == 'measurement':
            record = {
                'measurement_id': record_id,
                'measurement_concept_id': self._get_standard_concept_id(mapping),
                'measurement_date': record_date,
                'measurement_datetime': datetime.combine(record_date, datetime.min.time()),
                'measurement_time': None,
                'measurement_type_concept_id': self.type_concept_ids.get(record_type, 32817),
                'operator_concept_id': None,
                'value_as_number': None,
                'value_as_concept_id': None,
                'unit_concept_id': None,
                'range_low': None,
                'range_high': None,
                'provider_id': None,
                'visit_occurrence_id': None,
                'visit_detail_id': None,
                'measurement_source_value': mapping.get('original_text', mapping.get('display', '')),
                'measurement_source_concept_id': 0,
                'unit_source_value': None,
                'unit_source_concept_id': None,
                'value_source_value': None,
                'measurement_event_id': None,
                'meas_event_field_concept_id': None,
                **base_record
            }
            
        elif table_name == 'observation':
            record = {
                'observation_id': record_id,
                'observation_concept_id': self._get_standard_concept_id(mapping),
                'observation_date': record_date,
                'observation_datetime': datetime.combine(record_date, datetime.min.time()),
                'observation_type_concept_id': self.type_concept_ids.get(record_type, 32817),
                'value_as_number': None,
                'value_as_string': mapping.get('original_text'),
                'value_as_concept_id': None,
                'qualifier_concept_id': None,
                'unit_concept_id': None,
                'provider_id': None,
                'visit_occurrence_id': None,
                'visit_detail_id': None,
                'observation_source_value': mapping.get('original_text', mapping.get('display', '')),
                'observation_source_concept_id': 0,
                'unit_source_value': None,
                'qualifier_source_value': None,
                'value_source_value': mapping.get('original_text'),
                'observation_event_id': None,
                'obs_event_field_concept_id': None,
                **base_record
            }
        
        else:
            record = base_record
        
        return record
    
    def _determine_domain(self, mapping: Dict[str, Any]) -> str:
        """Determine OMOP domain based on mapping system and context."""
        system = mapping.get('system', '').lower()
        
        if 'snomed' in system:
            category = mapping.get('category', '').lower()
            if 'condition' in category or 'disease' in category:
                return 'Condition'
            elif 'procedure' in category:
                return 'Procedure'
            elif 'drug' in category:
                return 'Drug'
            else:
                return 'Observation'  # Default for SNOMED
        elif 'loinc' in system:
            return 'Measurement'
        elif 'rxnorm' in system:
            return 'Drug'
        else:
            return 'Observation'  # Default fallback
    
    def _get_vocabulary_id(self, system: str) -> str:
        """Get OMOP vocabulary ID from system URI."""
        system_lower = system.lower()
        
        if 'snomed' in system_lower:
            return 'SNOMED'
        elif 'loinc' in system_lower:
            return 'LOINC'
        elif 'rxnorm' in system_lower:
            return 'RxNorm'
        elif 'icd10' in system_lower:
            return 'ICD10CM'
        elif 'cpt' in system_lower:
            return 'CPT4'
        else:
            return 'None'
    
    def _determine_concept_class(self, mapping: Dict[str, Any]) -> str:
        """Determine OMOP concept class based on mapping."""
        system = mapping.get('system', '').lower()
        
        if 'snomed' in system:
            category = mapping.get('category', '').lower()
            if 'condition' in category:
                return 'Clinical Finding'
            elif 'procedure' in category:
                return 'Procedure'
            else:
                return 'Clinical Finding'  # Default for SNOMED
        elif 'loinc' in system:
            return 'Lab Test'
        elif 'rxnorm' in system:
            term_type = mapping.get('term_type', '').upper()
            if term_type == 'IN':
                return 'Ingredient'
            elif term_type == 'BN':
                return 'Brand Name'
            else:
                return 'Clinical Drug'
        else:
            return 'Undefined'
    
    def _get_standard_concept_id(self, mapping: Dict[str, Any]) -> int:
        """Get standard concept ID for mapping (placeholder implementation)."""
        # In a real implementation, this would lookup actual OMOP concept IDs
        # For now, we'll use a hash-based approach to generate consistent IDs
        system = mapping.get('system', '')
        code = mapping.get('code', '')
        
        if system and code:
            # Generate a consistent ID based on system and code
            hash_value = hash(f"{system}:{code}")
            # Ensure positive ID in the custom concept range
            return abs(hash_value) % 1000000000 + 2000000000
        else:
            return 0  # Unmapped concept
    
    def convert_batch_mappings(self, batch_mappings: Dict[str, List[Dict[str, Any]]], 
                             output_format: str = 'concepts',
                             person_id: int = 1) -> Dict[str, Any]:
        """
        Convert a batch of terminology mappings to OMOP format.
        
        Args:
            batch_mappings: Dictionary of mapping results by category
            output_format: Format for output ('concepts', 'domain_tables', 'full')
            person_id: Person ID for domain table records
            
        Returns:
            dict: OMOP tables and records
        """
        try:
            logger.info(f"Converting batch mappings in {output_format} format")
            
            # Flatten all mappings
            all_mappings = []
            for category, mappings in batch_mappings.items():
                for mapping in mappings:
                    mapping['category'] = category
                    all_mappings.append(mapping)
            
            result = {}
            
            if output_format in ['concepts', 'full']:
                # Generate CONCEPT records
                concepts = self.convert_mappings_to_concepts(all_mappings)
                result['concept'] = concepts
                
                # Generate CONCEPT_RELATIONSHIP records
                relationships = self.convert_mappings_to_concept_relationships(all_mappings, concepts)
                result['concept_relationship'] = relationships
            
            if output_format in ['domain_tables', 'full']:
                # Generate domain table records
                domain_tables = self.convert_mappings_to_domain_tables(all_mappings, person_id)
                result.update(domain_tables)
            
            logger.info(f"Created OMOP output with {len(result)} tables")
            return result
            
        except Exception as e:
            logger.error(f"Error converting batch mappings: {e}")
            raise
    
    def export_to_csv(self, omop_tables: Dict[str, List[Dict[str, Any]]], 
                     output_dir: str) -> Dict[str, str]:
        """
        Export OMOP tables to CSV files.
        
        Args:
            omop_tables: Dictionary of OMOP tables
            output_dir: Directory to save CSV files
            
        Returns:
            dict: Mapping of table names to file paths
        """
        try:
            logger.info(f"Exporting {len(omop_tables)} OMOP tables to CSV")
            
            os.makedirs(output_dir, exist_ok=True)
            file_paths = {}
            
            for table_name, records in omop_tables.items():
                if not records:
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(records)
                
                # Save to CSV
                file_path = os.path.join(output_dir, f"{table_name}.csv")
                df.to_csv(file_path, index=False)
                file_paths[table_name] = file_path
                
                logger.info(f"Exported {len(records)} records to {file_path}")
            
            return file_paths
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def get_cdm_version(self) -> str:
        """Return the OMOP CDM version used by the converter."""
        return "5.4"  # Current OMOP CDM version
    
    def get_supported_tables(self) -> List[str]:
        """Return list of supported OMOP table types."""
        return [
            "concept",
            "concept_relationship",
            "condition_occurrence",
            "drug_exposure", 
            "procedure_occurrence",
            "measurement",
            "observation"
        ]