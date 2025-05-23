"""
FHIR Terminology Validator for the Medical Terminology Mapper.

This module validates FHIR terminology resources created during terminology mapping,
specifically focused on CodeableConcept, ValueSet, and ConceptMap validation.

Adapted from the Clinical Protocol Extractor project with terminology-specific enhancements.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Set up logging
logger = logging.getLogger(__name__)

class FHIRTerminologyValidator:
    """
    Validates FHIR terminology resources against FHIR standards.
    
    This validator focuses on terminology-specific resources such as
    CodeableConcept, ValueSet, ConceptMap, and Bundle.
    """
    
    def __init__(self):
        """Initialize FHIR terminology validator."""
        logger.info("Initializing FHIR terminology validator")
        
        # Define required elements for each resource type
        self.required_elements = {
            "ValueSet": ["resourceType", "status", "url"],
            "ConceptMap": ["resourceType", "status", "url", "group"],
            "Bundle": ["resourceType", "type"],
            "Basic": ["resourceType", "code"]
        }
        
        # Define allowed values for certain elements
        self.allowed_values = {
            "status": ["draft", "active", "retired", "unknown"],
            "bundle_type": ["document", "message", "transaction", "transaction-response", 
                          "batch", "batch-response", "history", "searchset", "collection"],
            "equivalence": ["relatedto", "equivalent", "equal", "wider", "subsumes", 
                          "narrower", "specializes", "inexact", "unmatched", "disjoint"]
        }
        
        # Valid FHIR terminology systems
        self.valid_systems = {
            'http://snomed.info/sct': 'SNOMED CT',
            'http://loinc.org': 'LOINC',
            'http://www.nlm.nih.gov/research/umls/rxnorm': 'RxNorm',
            'http://hl7.org/fhir/sid/icd-10': 'ICD-10',
            'http://www.ama-assn.org/go/cpt': 'CPT'
        }
    
    def validate(self, resources: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Validate FHIR terminology resources against FHIR standards.
        
        Args:
            resources: FHIR resources to validate (single resource or list)
            
        Returns:
            dict: Validation results
        """
        try:
            logger.info("Starting FHIR terminology resource validation")
            
            # Normalize input to list
            if isinstance(resources, dict):
                if resources.get("resourceType") == "Bundle":
                    # Extract resources from bundle
                    resource_list = []
                    if "entry" in resources:
                        for entry in resources["entry"]:
                            if "resource" in entry:
                                resource_list.append(entry["resource"])
                    # Also validate the bundle itself
                    resource_list.append(resources)
                else:
                    resource_list = [resources]
            else:
                resource_list = resources
            
            validation_issues = []
            
            # Validate each resource
            for i, resource in enumerate(resource_list):
                resource_type = resource.get("resourceType")
                
                if resource_type == "ValueSet":
                    issues = self.validate_valueset(resource)
                    validation_issues.extend([f"ValueSet[{i}]: {issue}" for issue in issues])
                elif resource_type == "ConceptMap":
                    issues = self.validate_conceptmap(resource)
                    validation_issues.extend([f"ConceptMap[{i}]: {issue}" for issue in issues])
                elif resource_type == "Bundle":
                    issues = self.validate_bundle(resource)
                    validation_issues.extend([f"Bundle[{i}]: {issue}" for issue in issues])
                elif resource_type == "Basic":
                    issues = self.validate_basic(resource)
                    validation_issues.extend([f"Basic[{i}]: {issue}" for issue in issues])
                else:
                    validation_issues.append(f"Resource[{i}]: Unsupported resource type: {resource_type}")
            
            # Validate CodeableConcepts within resources
            codeable_concept_issues = self.validate_codeable_concepts_in_resources(resource_list)
            validation_issues.extend(codeable_concept_issues)
            
            # Determine overall validation status
            is_valid = len(validation_issues) == 0
            
            validation_result = {
                "valid": is_valid,
                "issues": validation_issues,
                "validated_at": datetime.now().isoformat(),
                "fhir_version": "4.0.1",  # FHIR R4
                "resources_validated": len(resource_list)
            }
            
            logger.info(f"FHIR terminology validation completed with {len(validation_issues)} issues")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error during FHIR terminology validation: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "validated_at": datetime.now().isoformat(),
                "fhir_version": "4.0.1"
            }
    
    def validate_valueset(self, valueset: Dict[str, Any]) -> List[str]:
        """
        Validate ValueSet resource.
        
        Args:
            valueset: ValueSet resource
            
        Returns:
            list: Validation issues
        """
        issues = []
        
        # Check resource type
        if valueset.get("resourceType") != "ValueSet":
            issues.append("Invalid resourceType for ValueSet")
        
        # Check required elements
        for element in self.required_elements["ValueSet"]:
            if element not in valueset or not valueset[element]:
                issues.append(f"Missing required element: {element}")
        
        # Check status value
        if "status" in valueset and valueset["status"] not in self.allowed_values["status"]:
            issues.append(f"Invalid status: {valueset['status']}")
        
        # Validate URL format
        if "url" in valueset:
            url = valueset["url"]
            if not isinstance(url, str) or not (url.startswith("http://") or url.startswith("https://")):
                issues.append(f"Invalid URL format: {url}")
        
        # Validate compose section
        if "compose" in valueset:
            compose_issues = self.validate_valueset_compose(valueset["compose"])
            issues.extend(compose_issues)
        
        # Validate expansion section
        if "expansion" in valueset:
            expansion_issues = self.validate_valueset_expansion(valueset["expansion"])
            issues.extend(expansion_issues)
        
        return issues
    
    def validate_valueset_compose(self, compose: Dict[str, Any]) -> List[str]:
        """
        Validate ValueSet compose section.
        
        Args:
            compose: ValueSet compose section
            
        Returns:
            list: Validation issues
        """
        issues = []
        
        # Check include sections
        if "include" in compose:
            if not isinstance(compose["include"], list):
                issues.append("Compose.include must be an array")
            else:
                for i, include in enumerate(compose["include"]):
                    # Check system
                    if "system" not in include:
                        issues.append(f"Include[{i}] missing system")
                    else:
                        system = include["system"]
                        if system not in self.valid_systems and not system.startswith("http"):
                            issues.append(f"Include[{i}] has invalid system: {system}")
                    
                    # Check concepts
                    if "concept" in include:
                        if not isinstance(include["concept"], list):
                            issues.append(f"Include[{i}].concept must be an array")
                        else:
                            for j, concept in enumerate(include["concept"]):
                                if "code" not in concept:
                                    issues.append(f"Include[{i}].concept[{j}] missing code")
        
        return issues
    
    def validate_valueset_expansion(self, expansion: Dict[str, Any]) -> List[str]:
        """
        Validate ValueSet expansion section.
        
        Args:
            expansion: ValueSet expansion section
            
        Returns:
            list: Validation issues
        """
        issues = []
        
        # Check required elements
        if "timestamp" not in expansion:
            issues.append("Expansion missing timestamp")
        
        # Check contains section
        if "contains" in expansion:
            if not isinstance(expansion["contains"], list):
                issues.append("Expansion.contains must be an array")
            else:
                for i, concept in enumerate(expansion["contains"]):
                    if "system" not in concept:
                        issues.append(f"Expansion.contains[{i}] missing system")
                    if "code" not in concept:
                        issues.append(f"Expansion.contains[{i}] missing code")
                    
                    # Validate system if present
                    if "system" in concept:
                        system = concept["system"]
                        if system not in self.valid_systems and not system.startswith("http"):
                            issues.append(f"Expansion.contains[{i}] has invalid system: {system}")
        
        # Check total count consistency
        if "total" in expansion and "contains" in expansion:
            stated_total = expansion["total"]
            actual_total = len(expansion["contains"])
            if stated_total != actual_total:
                issues.append(f"Expansion total mismatch: stated {stated_total}, actual {actual_total}")
        
        return issues
    
    def validate_conceptmap(self, conceptmap: Dict[str, Any]) -> List[str]:
        """
        Validate ConceptMap resource.
        
        Args:
            conceptmap: ConceptMap resource
            
        Returns:
            list: Validation issues
        """
        issues = []
        
        # Check resource type
        if conceptmap.get("resourceType") != "ConceptMap":
            issues.append("Invalid resourceType for ConceptMap")
        
        # Check required elements
        for element in self.required_elements["ConceptMap"]:
            if element not in conceptmap or not conceptmap[element]:
                issues.append(f"Missing required element: {element}")
        
        # Check status value
        if "status" in conceptmap and conceptmap["status"] not in self.allowed_values["status"]:
            issues.append(f"Invalid status: {conceptmap['status']}")
        
        # Validate URL format
        if "url" in conceptmap:
            url = conceptmap["url"]
            if not isinstance(url, str) or not (url.startswith("http://") or url.startswith("https://")):
                issues.append(f"Invalid URL format: {url}")
        
        # Validate group sections
        if "group" in conceptmap:
            if not isinstance(conceptmap["group"], list):
                issues.append("ConceptMap.group must be an array")
            else:
                for i, group in enumerate(conceptmap["group"]):
                    group_issues = self.validate_conceptmap_group(group, i)
                    issues.extend(group_issues)
        
        return issues
    
    def validate_conceptmap_group(self, group: Dict[str, Any], group_index: int) -> List[str]:
        """
        Validate ConceptMap group section.
        
        Args:
            group: ConceptMap group section
            group_index: Index of the group for error reporting
            
        Returns:
            list: Validation issues
        """
        issues = []
        
        # Check source and target
        if "source" not in group:
            issues.append(f"Group[{group_index}] missing source")
        if "target" not in group:
            issues.append(f"Group[{group_index}] missing target")
        
        # Validate systems
        for system_field in ["source", "target"]:
            if system_field in group:
                system = group[system_field]
                if system not in self.valid_systems and not system.startswith("http"):
                    issues.append(f"Group[{group_index}] has invalid {system_field}: {system}")
        
        # Validate elements
        if "element" in group:
            if not isinstance(group["element"], list):
                issues.append(f"Group[{group_index}].element must be an array")
            else:
                for j, element in enumerate(group["element"]):
                    if "code" not in element:
                        issues.append(f"Group[{group_index}].element[{j}] missing code")
                    
                    # Validate targets
                    if "target" in element:
                        if not isinstance(element["target"], list):
                            issues.append(f"Group[{group_index}].element[{j}].target must be an array")
                        else:
                            for k, target in enumerate(element["target"]):
                                if "equivalence" not in target:
                                    issues.append(f"Group[{group_index}].element[{j}].target[{k}] missing equivalence")
                                elif target["equivalence"] not in self.allowed_values["equivalence"]:
                                    issues.append(f"Group[{group_index}].element[{j}].target[{k}] has invalid equivalence: {target['equivalence']}")
        
        return issues
    
    def validate_bundle(self, bundle: Dict[str, Any]) -> List[str]:
        """
        Validate Bundle resource.
        
        Args:
            bundle: Bundle resource
            
        Returns:
            list: Validation issues
        """
        issues = []
        
        # Check resource type
        if bundle.get("resourceType") != "Bundle":
            issues.append("Invalid resourceType for Bundle")
        
        # Check required elements
        for element in self.required_elements["Bundle"]:
            if element not in bundle or not bundle[element]:
                issues.append(f"Missing required element: {element}")
        
        # Check type value
        if "type" in bundle and bundle["type"] not in self.allowed_values["bundle_type"]:
            issues.append(f"Invalid type: {bundle['type']}")
        
        # Validate entries
        if "entry" in bundle:
            if not isinstance(bundle["entry"], list):
                issues.append("Bundle.entry must be an array")
            else:
                for i, entry in enumerate(bundle["entry"]):
                    if "resource" not in entry:
                        issues.append(f"Entry[{i}] missing resource")
                    
                    # Check fullUrl if present
                    if "fullUrl" in entry:
                        full_url = entry["fullUrl"]
                        if not isinstance(full_url, str):
                            issues.append(f"Entry[{i}] fullUrl must be a string")
        
        # Check total count consistency
        if "total" in bundle and "entry" in bundle:
            stated_total = bundle["total"]
            actual_total = len(bundle["entry"])
            if stated_total != actual_total:
                issues.append(f"Bundle total mismatch: stated {stated_total}, actual {actual_total}")
        
        return issues
    
    def validate_basic(self, basic: Dict[str, Any]) -> List[str]:
        """
        Validate Basic resource.
        
        Args:
            basic: Basic resource
            
        Returns:
            list: Validation issues
        """
        issues = []
        
        # Check resource type
        if basic.get("resourceType") != "Basic":
            issues.append("Invalid resourceType for Basic")
        
        # Check required elements
        for element in self.required_elements["Basic"]:
            if element not in basic or not basic[element]:
                issues.append(f"Missing required element: {element}")
        
        # Validate code structure
        if "code" in basic:
            if not isinstance(basic["code"], dict):
                issues.append("Basic.code must be a CodeableConcept")
            else:
                code_issues = self.validate_codeable_concept(basic["code"], "Basic.code")
                issues.extend(code_issues)
        
        return issues
    
    def validate_codeable_concept(self, codeable_concept: Dict[str, Any], 
                                context: str = "CodeableConcept") -> List[str]:
        """
        Validate CodeableConcept structure.
        
        Args:
            codeable_concept: CodeableConcept to validate
            context: Context for error reporting
            
        Returns:
            list: Validation issues
        """
        issues = []
        
        # Check structure
        if not isinstance(codeable_concept, dict):
            issues.append(f"{context} must be an object")
            return issues
        
        # Validate coding array
        if "coding" in codeable_concept:
            if not isinstance(codeable_concept["coding"], list):
                issues.append(f"{context}.coding must be an array")
            else:
                for i, coding in enumerate(codeable_concept["coding"]):
                    if not isinstance(coding, dict):
                        issues.append(f"{context}.coding[{i}] must be an object")
                        continue
                    
                    # Check required fields
                    if "system" not in coding:
                        issues.append(f"{context}.coding[{i}] missing system")
                    if "code" not in coding:
                        issues.append(f"{context}.coding[{i}] missing code")
                    
                    # Validate system
                    if "system" in coding:
                        system = coding["system"]
                        if system not in self.valid_systems and not system.startswith("http"):
                            issues.append(f"{context}.coding[{i}] has invalid system: {system}")
        
        # Must have either coding or text
        if "coding" not in codeable_concept and "text" not in codeable_concept:
            issues.append(f"{context} must have either coding or text")
        
        return issues
    
    def validate_codeable_concepts_in_resources(self, resources: List[Dict[str, Any]]) -> List[str]:
        """
        Find and validate all CodeableConcept instances in resources.
        
        Args:
            resources: List of FHIR resources
            
        Returns:
            list: Validation issues
        """
        issues = []
        
        for i, resource in enumerate(resources):
            resource_type = resource.get("resourceType", "Unknown")
            
            # Find CodeableConcepts in extensions
            if "extension" in resource:
                for j, extension in enumerate(resource["extension"]):
                    if "valueCodeableConcept" in extension:
                        cc_issues = self.validate_codeable_concept(
                            extension["valueCodeableConcept"],
                            f"{resource_type}[{i}].extension[{j}].valueCodeableConcept"
                        )
                        issues.extend(cc_issues)
        
        return issues
    
    def validate_terminology_system(self, system: str) -> bool:
        """
        Validate if a terminology system URI is valid.
        
        Args:
            system: Terminology system URI
            
        Returns:
            bool: True if valid
        """
        return system in self.valid_systems or system.startswith("http")
    
    def get_fhir_version(self) -> str:
        """Return the FHIR version used by the validator."""
        return "4.0.1"  # FHIR R4
    
    def get_supported_resources(self) -> List[str]:
        """Return list of supported FHIR resource types."""
        return [
            "ValueSet",
            "ConceptMap", 
            "Bundle",
            "Basic"
        ]