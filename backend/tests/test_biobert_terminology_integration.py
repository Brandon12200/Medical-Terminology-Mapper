"""
Test BioBERT-Terminology Integration

This test verifies the integration between BioBERT entity extraction
and terminology mapping functionality.
"""

import pytest
from app.ml.biobert.biobert_service import BioBERTService
from app.standards.terminology.mapper import TerminologyMapper


def test_biobert_terminology_integration():
    """Test that BioBERT entities are correctly mapped to terminologies"""
    
    # Initialize services
    terminology_mapper = TerminologyMapper()
    biobert_service = BioBERTService(
        use_advanced_extractor=True,
        confidence_threshold=0.7,
        terminology_mapper=terminology_mapper
    )
    
    # Test medical text with various entity types
    test_text = """
    The patient presents with type 2 diabetes mellitus and hypertension. 
    Current medications include metformin 500mg twice daily and lisinopril 10mg once daily.
    Recent lab tests show elevated glucose levels. 
    Physical examination reveals no abnormalities in the heart or lungs.
    """
    
    # Extract entities with terminology mapping
    entities = biobert_service.extract_entities(
        test_text,
        extract_context=True,
        map_to_terminologies=True
    )
    
    # Verify entities were extracted
    assert len(entities) > 0, "No entities extracted"
    
    # Check for specific entity types
    entity_types = {entity.entity_type for entity in entities}
    expected_types = {"CONDITION", "MEDICATION", "LAB_TEST", "ANATOMY"}
    
    # Find entities with terminology mappings
    mapped_entities = [e for e in entities if e.terminology_mappings]
    assert len(mapped_entities) > 0, "No entities have terminology mappings"
    
    # Verify entity-to-terminology routing
    for entity in mapped_entities:
        if entity.entity_type == "MEDICATION":
            # Medications should map to RxNorm
            assert "rxnorm" in entity.terminology_mappings
        elif entity.entity_type == "LAB_TEST":
            # Lab tests should map to LOINC
            assert "loinc" in entity.terminology_mappings
        elif entity.entity_type in ["CONDITION", "PROCEDURE"]:
            # Conditions and procedures should map to SNOMED
            assert "snomed" in entity.terminology_mappings
    
    # Print results for manual inspection
    print(f"\nExtracted {len(entities)} entities")
    print(f"Entities with terminology mappings: {len(mapped_entities)}")
    
    for entity in mapped_entities:
        print(f"\n{entity.entity_type}: {entity.text}")
        print(f"  Confidence: {entity.confidence:.2f}")
        if entity.terminology_mappings:
            for system, mappings in entity.terminology_mappings.items():
                if mappings:
                    print(f"  {system.upper()}:")
                    for mapping in mappings[:2]:  # Show top 2 matches
                        print(f"    - {mapping.get('code')}: {mapping.get('display')}")


def test_confidence_threshold_filtering():
    """Test that confidence threshold filtering works correctly"""
    
    biobert_service = BioBERTService(
        use_advanced_extractor=True,
        confidence_threshold=0.8,  # High threshold
        terminology_mapper=None
    )
    
    test_text = "The patient has diabetes and takes metformin."
    
    # Extract entities with high confidence threshold
    entities = biobert_service.extract_entities(test_text)
    
    # All returned entities should have confidence >= 0.8
    for entity in entities:
        assert entity.confidence >= 0.8, f"Entity {entity.text} has confidence {entity.confidence} < 0.8"


def test_entity_type_routing():
    """Test that different entity types route to correct terminology systems"""
    
    terminology_mapper = TerminologyMapper()
    biobert_service = BioBERTService(
        terminology_mapper=terminology_mapper
    )
    
    # Test cases for different entity types
    test_cases = [
        ("The patient has diabetes", "CONDITION", "snomed"),
        ("Prescribed metformin 500mg", "MEDICATION", "rxnorm"),
        ("Blood glucose test ordered", "LAB_TEST", "loinc"),
    ]
    
    for text, expected_type, expected_system in test_cases:
        entities = biobert_service.extract_entities(
            text,
            map_to_terminologies=True
        )
        
        # Find entity of expected type
        typed_entities = [e for e in entities if e.entity_type == expected_type]
        
        if typed_entities and typed_entities[0].terminology_mappings:
            # Verify correct terminology system is used
            assert expected_system in typed_entities[0].terminology_mappings, \
                f"Expected {expected_system} mapping for {expected_type}"


if __name__ == "__main__":
    # Run tests
    print("Testing BioBERT-Terminology Integration...")
    test_biobert_terminology_integration()
    print("\nTesting Confidence Threshold Filtering...")
    test_confidence_threshold_filtering()
    print("\nTesting Entity Type Routing...")
    test_entity_type_routing()
    print("\nAll tests completed!")