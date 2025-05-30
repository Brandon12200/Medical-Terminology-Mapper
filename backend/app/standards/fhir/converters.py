"""
FHIR Terminology Converter for the Medical Terminology Mapper.

This module handles the conversion of terminology mapping results to FHIR resources,
specifically focused on CodeableConcept and ValueSet generation.

Adapted from the Clinical Protocol Extractor project with terminology-specific enhancements.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Set up logging
logger = logging.getLogger(__name__)

class FHIRTerminologyConverter:
    """
    Converts terminology mapping results to FHIR resources.
    
    This converter focuses on creating FHIR-compliant terminology resources
    such as CodeableConcept, ValueSet, and ConceptMap.
    """
    
    def __init__(self, terminology_mapper=None, config=None):
        """
        Initialize FHIR terminology converter.
        
        Args:
            terminology_mapper: Optional mapper for clinical terminology
            config: Optional configuration dictionary
        """
        self.terminology_mapper = terminology_mapper
        self.config = config or {}
        
        # Default FHIR systems
        self.fhir_systems = {
            'snomed': 'http://snomed.info/sct',
            'loinc': 'http://loinc.org',
            'rxnorm': 'http://www.nlm.nih.gov/research/umls/rxnorm',
            'icd10': 'http://hl7.org/fhir/sid/icd-10',
            'cpt': 'http://www.ama-assn.org/go/cpt'
        }
        
        logger.info("Initialized FHIR terminology converter")
    
    def convert_mapping_to_codeable_concept(self, mapping_result: Dict[str, Any], 
                                           original_term: str = None) -> Dict[str, Any]:
        """
        Convert a terminology mapping result to a FHIR CodeableConcept.
        
        Args:
            mapping_result: Result from terminology mapping
            original_term: Original term text if available
            
        Returns:
            dict: FHIR CodeableConcept resource
        """
        try:
            logger.debug(f"Converting mapping to CodeableConcept: {mapping_result}")
            
            codeable_concept = {
                "coding": []
            }
            
            # Add the mapped coding if found
            if mapping_result.get('found', False):
                coding = {
                    "system": mapping_result.get('system'),
                    "code": mapping_result.get('code'),
                    "display": mapping_result.get('display')
                }
                
                # Add version if available
                if 'version' in mapping_result:
                    coding["version"] = mapping_result['version']
                
                # Add confidence as extension
                if 'confidence' in mapping_result:
                    coding["extension"] = [{
                        "url": "http://example.org/fhir/StructureDefinition/mapping-confidence",
                        "valueDecimal": mapping_result['confidence']
                    }]
                
                codeable_concept["coding"].append(coding)
            
            # Add original text
            if original_term:
                codeable_concept["text"] = original_term
            elif 'original_text' in mapping_result:
                codeable_concept["text"] = mapping_result['original_text']
            
            # Add match type as extension if available
            if 'match_type' in mapping_result:
                if "extension" not in codeable_concept:
                    codeable_concept["extension"] = []
                codeable_concept["extension"].append({
                    "url": "http://example.org/fhir/StructureDefinition/match-type",
                    "valueString": mapping_result['match_type']
                })
            
            return codeable_concept
            
        except Exception as e:
            logger.error(f"Error converting mapping to CodeableConcept: {e}")
            # Return minimal CodeableConcept with just text
            return {
                "text": original_term or mapping_result.get('display', 'Unknown term')
            }
    
    def convert_mappings_to_valueset(self, mappings: List[Dict[str, Any]], 
                                   valueset_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Convert multiple terminology mappings to a FHIR ValueSet.
        
        Args:
            mappings: List of terminology mapping results
            valueset_info: Optional metadata for the ValueSet
            
        Returns:
            dict: FHIR ValueSet resource
        """
        try:
            logger.info(f"Converting {len(mappings)} mappings to ValueSet")
            
            # Handle None valueset_info
            if valueset_info is None:
                valueset_info = {}
            
            # Generate unique ID
            valueset_id = f"terminology-valueset-{str(uuid.uuid4())[:8]}"
            
            # Create ValueSet structure
            valueset = {
                "resourceType": "ValueSet",
                "id": valueset_id,
                "meta": {
                    "lastUpdated": datetime.now().isoformat()
                },
                "url": f"http://example.org/fhir/ValueSet/{valueset_id}",
                "version": "1.0.0",
                "name": valueset_info.get('name', f'TerminologyValueSet{valueset_id}'),
                "title": valueset_info.get('title', 'Terminology Mapping ValueSet'),
                "status": "draft",
                "experimental": True,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "publisher": "Medical Terminology Mapper",
                "description": valueset_info.get('description', 
                                               'ValueSet generated from terminology mappings'),
                "compose": {
                    "include": []
                }
            }
            
            # Group mappings by system
            system_mappings = {}
            for mapping in mappings:
                if mapping.get('found', False) and mapping.get('system'):
                    system = mapping['system']
                    if system not in system_mappings:
                        system_mappings[system] = []
                    system_mappings[system].append(mapping)
            
            # Create include sections for each system
            for system, sys_mappings in system_mappings.items():
                include_section = {
                    "system": system,
                    "concept": []
                }
                
                # Add concepts from this system
                for mapping in sys_mappings:
                    concept = {
                        "code": mapping['code'],
                        "display": mapping.get('display', mapping['code'])
                    }
                    
                    # Add designation if original text differs
                    if 'original_text' in mapping and mapping['original_text'] != mapping.get('display'):
                        concept["designation"] = [{
                            "language": "en",
                            "use": {
                                "system": "http://terminology.hl7.org/CodeSystem/designation-usage",
                                "code": "synonym"
                            },
                            "value": mapping['original_text']
                        }]
                    
                    include_section["concept"].append(concept)
                
                valueset["compose"]["include"].append(include_section)
            
            # Add expansion section with all concepts
            expansion_concepts = []
            for mapping in mappings:
                if mapping.get('found', False):
                    expansion_concept = {
                        "system": mapping['system'],
                        "code": mapping['code'],
                        "display": mapping.get('display', mapping['code'])
                    }
                    
                    # Add confidence as extension
                    if 'confidence' in mapping:
                        expansion_concept["extension"] = [{
                            "url": "http://example.org/fhir/StructureDefinition/mapping-confidence",
                            "valueDecimal": mapping['confidence']
                        }]
                    
                    expansion_concepts.append(expansion_concept)
            
            if expansion_concepts:
                valueset["expansion"] = {
                    "identifier": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "total": len(expansion_concepts),
                    "contains": expansion_concepts
                }
            
            logger.info(f"Created ValueSet with {len(expansion_concepts)} concepts")
            return valueset
            
        except Exception as e:
            logger.error(f"Error converting mappings to ValueSet: {e}")
            raise
    
    def convert_mappings_to_conceptmap(self, mappings: List[Dict[str, Any]], 
                                     source_system: str = None,
                                     target_system: str = None,
                                     conceptmap_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Convert terminology mappings to a FHIR ConceptMap.
        
        Args:
            mappings: List of terminology mapping results
            source_system: Source terminology system
            target_system: Target terminology system
            conceptmap_info: Optional metadata for the ConceptMap
            
        Returns:
            dict: FHIR ConceptMap resource
        """
        try:
            logger.info(f"Converting {len(mappings)} mappings to ConceptMap")
            
            # Handle None conceptmap_info
            if conceptmap_info is None:
                conceptmap_info = {}
            
            # Generate unique ID
            conceptmap_id = f"terminology-conceptmap-{str(uuid.uuid4())[:8]}"
            
            # Create ConceptMap structure
            conceptmap = {
                "resourceType": "ConceptMap",
                "id": conceptmap_id,
                "meta": {
                    "lastUpdated": datetime.now().isoformat()
                },
                "url": f"http://example.org/fhir/ConceptMap/{conceptmap_id}",
                "version": "1.0.0",
                "name": conceptmap_info.get('name', f'TerminologyConceptMap{conceptmap_id}'),
                "title": conceptmap_info.get('title', 'Terminology Mapping ConceptMap'),
                "status": "draft",
                "experimental": True,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "publisher": "Medical Terminology Mapper",
                "description": conceptmap_info.get('description', 
                                                 'ConceptMap generated from terminology mappings'),
                "group": []
            }
            
            # Set source and target if provided
            if source_system:
                conceptmap["sourceUri"] = source_system
            if target_system:
                conceptmap["targetUri"] = target_system
            
            # Group mappings by source and target systems
            system_groups = {}
            
            for mapping in mappings:
                if not mapping.get('found', False):
                    continue
                
                source_sys = mapping.get('source_system', source_system or 'unknown')
                target_sys = mapping.get('system', target_system)
                
                group_key = f"{source_sys}|{target_sys}"
                if group_key not in system_groups:
                    system_groups[group_key] = {
                        'source': source_sys,
                        'target': target_sys,
                        'elements': []
                    }
                
                # Create mapping element
                element = {
                    "code": mapping.get('source_code', mapping.get('original_text', '')),
                    "target": [{
                        "code": mapping['code'],
                        "display": mapping.get('display', mapping['code']),
                        "equivalence": self._determine_equivalence(mapping)
                    }]
                }
                
                # Add display for source if available
                if 'source_display' in mapping:
                    element["display"] = mapping['source_display']
                elif 'original_text' in mapping:
                    element["display"] = mapping['original_text']
                
                # Add comment with mapping details
                comments = []
                if 'match_type' in mapping:
                    comments.append(f"Match type: {mapping['match_type']}")
                if 'confidence' in mapping:
                    comments.append(f"Confidence: {mapping['confidence']}")
                
                if comments:
                    element["target"][0]["comment"] = "; ".join(comments)
                
                system_groups[group_key]['elements'].append(element)
            
            # Convert system groups to ConceptMap groups
            for group_info in system_groups.values():
                group = {
                    "source": group_info['source'],
                    "target": group_info['target'],
                    "element": group_info['elements']
                }
                conceptmap["group"].append(group)
            
            logger.info(f"Created ConceptMap with {len(system_groups)} groups")
            return conceptmap
            
        except Exception as e:
            logger.error(f"Error converting mappings to ConceptMap: {e}")
            raise
    
    def _determine_equivalence(self, mapping: Dict[str, Any]) -> str:
        """
        Determine FHIR equivalence based on mapping confidence and type.
        
        Args:
            mapping: Terminology mapping result
            
        Returns:
            str: FHIR equivalence code
        """
        confidence = mapping.get('confidence', 1.0)
        match_type = mapping.get('match_type', 'exact')
        
        if match_type == 'exact' and confidence >= 0.95:
            return 'equal'
        elif confidence >= 0.8:
            return 'equivalent'  
        elif confidence >= 0.6:
            return 'wider'  # Target is broader than source
        elif confidence >= 0.4:
            return 'narrower'  # Target is narrower than source
        else:
            return 'relatedto'  # Some relationship exists
    
    def create_terminology_bundle(self, mappings: List[Dict[str, Any]], 
                                bundle_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a FHIR Bundle containing multiple terminology resources.
        
        Args:
            mappings: List of terminology mapping results
            bundle_info: Optional metadata for the Bundle
            
        Returns:
            dict: FHIR Bundle resource
        """
        try:
            logger.info(f"Creating terminology Bundle with {len(mappings)} mappings")
            
            # Handle None bundle_info
            if bundle_info is None:
                bundle_info = {}
            
            # Generate unique ID
            bundle_id = f"terminology-bundle-{str(uuid.uuid4())[:8]}"
            
            # Create Bundle structure
            bundle = {
                "resourceType": "Bundle",
                "id": bundle_id,
                "meta": {
                    "lastUpdated": datetime.now().isoformat()
                },
                "type": "collection",
                "timestamp": datetime.now().isoformat(),
                "entry": []
            }
            
            # Create ValueSet from mappings
            valueset = self.convert_mappings_to_valueset(
                mappings, 
                bundle_info.get('valueset_info', {})
            )
            
            bundle["entry"].append({
                "fullUrl": f"ValueSet/{valueset['id']}",
                "resource": valueset
            })
            
            # Create ConceptMap from mappings
            conceptmap = self.convert_mappings_to_conceptmap(
                mappings,
                conceptmap_info=bundle_info.get('conceptmap_info', {})
            )
            
            bundle["entry"].append({
                "fullUrl": f"ConceptMap/{conceptmap['id']}",
                "resource": conceptmap
            })
            
            # Add individual CodeableConcept resources as Basic resources
            for i, mapping in enumerate(mappings):
                if mapping.get('found', False):
                    basic_resource = {
                        "resourceType": "Basic",
                        "id": f"terminology-mapping-{i+1}",
                        "meta": {
                            "lastUpdated": datetime.now().isoformat()
                        },
                        "code": {
                            "coding": [{
                                "system": "http://example.org/fhir/CodeSystem/basic-resource-type",
                                "code": "terminology-mapping",
                                "display": "Terminology Mapping"
                            }]
                        },
                        "subject": {
                            "reference": f"ValueSet/{valueset['id']}"
                        }
                    }
                    
                    # Add the actual CodeableConcept as an extension
                    codeable_concept = self.convert_mapping_to_codeable_concept(
                        mapping, 
                        mapping.get('original_text')
                    )
                    
                    basic_resource["extension"] = [{
                        "url": "http://example.org/fhir/StructureDefinition/terminology-mapping",
                        "valueCodeableConcept": codeable_concept
                    }]
                    
                    bundle["entry"].append({
                        "fullUrl": f"Basic/{basic_resource['id']}",
                        "resource": basic_resource
                    })
            
            # Update total count
            bundle["total"] = len(bundle["entry"])
            
            logger.info(f"Created Bundle with {len(bundle['entry'])} resources")
            return bundle
            
        except Exception as e:
            logger.error(f"Error creating terminology Bundle: {e}")
            raise
    
    def convert_batch_mappings(self, batch_mappings: Dict[str, List[Dict[str, Any]]], 
                             output_format: str = 'bundle') -> Dict[str, Any]:
        """
        Convert a batch of terminology mappings to FHIR resources.
        
        Args:
            batch_mappings: Dictionary of mapping results by category
            output_format: Format for output ('bundle', 'valueset', 'conceptmap')
            
        Returns:
            dict: FHIR resource(s)
        """
        try:
            logger.info(f"Converting batch mappings in {output_format} format")
            
            if output_format == 'bundle':
                # Flatten all mappings into a single bundle
                all_mappings = []
                for category, mappings in batch_mappings.items():
                    for mapping in mappings:
                        mapping['category'] = category
                        all_mappings.append(mapping)
                
                return self.create_terminology_bundle(all_mappings, {
                    'valueset_info': {
                        'title': 'Batch Terminology Mappings',
                        'description': f'Combined mappings from {len(batch_mappings)} categories'
                    }
                })
            
            elif output_format == 'valueset':
                # Create separate ValueSets for each category
                valuesets = {}
                for category, mappings in batch_mappings.items():
                    valueset = self.convert_mappings_to_valueset(mappings, {
                        'title': f'{category.title()} Terms',
                        'description': f'ValueSet for {category} terminology mappings'
                    })
                    valuesets[category] = valueset
                
                return valuesets
            
            elif output_format == 'conceptmap':
                # Create separate ConceptMaps for each category
                conceptmaps = {}
                for category, mappings in batch_mappings.items():
                    conceptmap = self.convert_mappings_to_conceptmap(mappings, {
                        'title': f'{category.title()} Mappings',
                        'description': f'ConceptMap for {category} terminology mappings'
                    })
                    conceptmaps[category] = conceptmap
                
                return conceptmaps
            
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
        except Exception as e:
            logger.error(f"Error converting batch mappings: {e}")
            raise
    
    def get_fhir_version(self) -> str:
        """Return the FHIR version used by the converter."""
        return "4.0.1"  # FHIR R4
    
    def get_supported_resources(self) -> List[str]:
        """Return list of supported FHIR resource types."""
        return [
            "CodeableConcept",
            "ValueSet", 
            "ConceptMap",
            "Bundle"
        ]