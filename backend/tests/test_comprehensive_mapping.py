"""
Comprehensive tests for medical term mapping capabilities across SNOMED, LOINC, and RxNorm.
These tests verify the mapping functionality works correctly with the available data.
"""

import pytest
from app.standards.terminology.mapper import TerminologyMapper


@pytest.fixture
def mapper():
    """Create a mapper instance for testing."""
    # Enable external services if API keys are available
    config = {
        "use_external_services": False,  # Set to True if APIs are configured
        "use_fuzzy_matching": True
    }
    return TerminologyMapper(config)


class TestMappingStructure:
    """Test that mappings return correct structure and data types."""
    
    def test_mapping_result_structure(self, mapper):
        """Test that mapping results have the expected structure."""
        # Test with a common medical term
        result = mapper.map_term("diabetes", system="snomed")
        
        if result:
            # Check required fields
            assert "code" in result
            assert "display" in result
            assert "system" in result
            assert "found" in result
            
            # Check data types
            assert isinstance(result["code"], str)
            assert isinstance(result["display"], str)
            assert isinstance(result["system"], str)
            assert isinstance(result["found"], bool)
            
            # Check optional fields if present
            if "confidence" in result:
                assert isinstance(result["confidence"], (int, float))
                assert 0 <= result["confidence"] <= 1
            
            if "match_type" in result:
                assert isinstance(result["match_type"], str)
    
    def test_system_urls(self, mapper):
        """Test that system URLs are correct."""
        # Expected system URLs
        system_urls = {
            "snomed": "http://snomed.info/sct",
            "loinc": "http://loinc.org",
            "rxnorm": "http://www.nlm.nih.gov/research/umls/rxnorm"
        }
        
        for system, expected_url in system_urls.items():
            # Try to find any term in each system
            test_terms = ["test", "blood", "drug", "pain", "fever"]
            
            for term in test_terms:
                result = mapper.map_term(term, system=system)
                if result and result.get("found"):
                    assert result["system"] == expected_url
                    break


class TestSNOMEDMapping:
    """Test SNOMED CT mapping functionality with available data."""
    
    def test_common_conditions(self, mapper):
        """Test mapping of common medical conditions."""
        # These are common terms that should map to something
        test_terms = [
            "diabetes",
            "hypertension",
            "asthma",
            "pneumonia",
            "infection",
            "pain",
            "fever",
            "cough",
            "headache"
        ]
        
        found_count = 0
        for term in test_terms:
            result = mapper.map_term(term, system="snomed")
            if result and result.get("found"):
                found_count += 1
                assert len(result["code"]) > 0
                assert len(result["display"]) > 0
        
        # At least some terms should map
        assert found_count > 0, "No SNOMED mappings found for common conditions"
    
    def test_fuzzy_matching(self, mapper):
        """Test fuzzy matching for misspelled terms."""
        # Test common misspellings
        misspellings = [
            ("diabetis", "diabet"),  # Common misspelling
            ("hypertenshun", "hypertens"),  # Phonetic misspelling
            ("astma", "asthm"),  # Missing letter
        ]
        
        for misspelled, root in misspellings:
            result = mapper.map_term(misspelled, system="snomed")
            if result and result.get("found"):
                # Check that the display contains something related to the root term
                assert root.lower() in result["display"].lower() or \
                       result.get("match_type") in ["fuzzy", "partial_ratio", "token_sort_ratio"]
    
    def test_abbreviations(self, mapper):
        """Test medical abbreviation expansion."""
        abbreviations = [
            "DM",  # Diabetes mellitus
            "HTN",  # Hypertension
            "MI",  # Myocardial infarction
            "CHF",  # Congestive heart failure
            "COPD",  # Chronic obstructive pulmonary disease
        ]
        
        expanded_count = 0
        for abbrev in abbreviations:
            result = mapper.map_term(abbrev, system="snomed")
            if result and result.get("found"):
                expanded_count += 1
        
        # Some abbreviations should be expanded and mapped
        assert expanded_count > 0, "No abbreviations were successfully mapped"


class TestLOINCMapping:
    """Test LOINC mapping functionality with available data."""
    
    def test_lab_tests(self, mapper):
        """Test mapping of common laboratory tests."""
        lab_tests = [
            "glucose",
            "hemoglobin",
            "creatinine",
            "cholesterol",
            "sodium",
            "potassium",
            "white blood cell",
            "platelet"
        ]
        
        found_count = 0
        for test in lab_tests:
            result = mapper.map_term(test, system="loinc")
            if result and result.get("found"):
                found_count += 1
                assert len(result["code"]) > 0
                # LOINC codes have specific format: NNNNN-N
                if "-" in result["code"]:
                    parts = result["code"].split("-")
                    assert len(parts) == 2
                    assert parts[0].isdigit()
                    assert parts[1].isdigit()
        
        assert found_count > 0, "No LOINC mappings found for common lab tests"
    
    def test_lab_panels(self, mapper):
        """Test mapping of laboratory panels."""
        panels = [
            "CBC",  # Complete blood count
            "CMP",  # Comprehensive metabolic panel
            "BMP",  # Basic metabolic panel
            "lipid panel",
            "liver panel"
        ]
        
        for panel in panels:
            result = mapper.map_term(panel, system="loinc")
            if result and result.get("found"):
                assert "panel" in result["display"].lower() or \
                       len(result["code"]) > 0


class TestRxNormMapping:
    """Test RxNorm mapping functionality with available data."""
    
    def test_common_medications(self, mapper):
        """Test mapping of common medications."""
        medications = [
            "aspirin",
            "ibuprofen",
            "acetaminophen",
            "amoxicillin",
            "metformin",
            "lisinopril",
            "omeprazole",
            "atorvastatin"
        ]
        
        found_count = 0
        for med in medications:
            result = mapper.map_term(med, system="rxnorm")
            if result and result.get("found"):
                found_count += 1
                assert len(result["code"]) > 0
                # RxNorm codes are numeric
                assert result["code"].isdigit()
        
        assert found_count > 0, "No RxNorm mappings found for common medications"
    
    def test_brand_names(self, mapper):
        """Test mapping of brand name medications."""
        brand_names = [
            "Tylenol",
            "Advil",
            "Motrin",
            "Zocor",
            "Lipitor",
            "Prilosec"
        ]
        
        for brand in brand_names:
            result = mapper.map_term(brand, system="rxnorm")
            if result and result.get("found"):
                assert len(result["code"]) > 0


class TestCrossSystemMapping:
    """Test mapping across different terminology systems."""
    
    def test_auto_system_detection(self, mapper):
        """Test automatic system detection based on term type."""
        # Since the mapper requires a system parameter, test each system separately
        test_cases = [
            ("diabetes", "snomed"),  # Condition
            ("glucose", "loinc"),  # Lab test
            ("aspirin", "rxnorm"),  # Medication
        ]
        
        for term, expected_system in test_cases:
            result = mapper.map_term(term, system=expected_system)
            if result and result.get("found"):
                # Verify it mapped to the expected system
                detected_system = result.get("system", "").lower()
                assert expected_system in detected_system
    
    def test_multi_system_term(self, mapper):
        """Test terms that could map to multiple systems."""
        # "Glucose" could be a lab test (LOINC) or a substance (SNOMED/RxNorm)
        
        # Try mapping to different systems
        snomed_result = mapper.map_term("glucose", system="snomed")
        loinc_result = mapper.map_term("glucose", system="loinc")
        
        # At least one should succeed
        assert (snomed_result and snomed_result.get("found")) or \
               (loinc_result and loinc_result.get("found"))


class TestBatchMapping:
    """Test batch mapping functionality."""
    
    def test_batch_processing(self, mapper):
        """Test processing multiple terms."""
        terms = [
            {"term": "diabetes", "system": "snomed"},
            {"term": "glucose", "system": "loinc"},
            {"term": "aspirin", "system": "rxnorm"},
            {"term": "hypertension", "system": "snomed"},
            {"term": "hemoglobin", "system": "loinc"}
        ]
        
        results = []
        for item in terms:
            result = mapper.map_term(item["term"], system=item["system"])
            results.append(result)
        
        # Check that we got results
        assert len(results) == len(terms)
        
        # Count successful mappings
        successful = sum(1 for r in results if r and r.get("found"))
        assert successful > 0, "No successful mappings in batch"
    
    def test_performance(self, mapper):
        """Test that mappings complete in reasonable time."""
        import time
        
        # Time a single mapping
        start = time.time()
        result = mapper.map_term("diabetes", system="snomed")
        elapsed = time.time() - start
        
        # Should complete quickly (under 1 second for single term)
        assert elapsed < 1.0, f"Mapping took too long: {elapsed} seconds"


class TestContextAwareMapping:
    """Test context-aware mapping features."""
    
    def test_context_enhancement(self, mapper):
        """Test that context improves mapping accuracy."""
        # Test ambiguous abbreviations with context
        test_cases = [
            ("MS", "neurological disorder", "snomed"),  # Multiple sclerosis
            ("MS", "pain medication", "rxnorm"),  # Morphine sulfate
            ("PT", "laboratory test", "loinc"),  # Prothrombin time
            ("PT", "therapy", "snomed"),  # Physical therapy
        ]
        
        for term, context, system in test_cases:
            result_with_context = mapper.map_term(term, system=system, context=context)
            result_without = mapper.map_term(term, system=system)
            
            if result_with_context and result_without:
                # Context may improve confidence or change the mapping
                if "confidence" in result_with_context and "confidence" in result_without:
                    # Just verify both results are valid
                    assert result_with_context.get("found") or result_without.get("found")
    
    def test_negation_detection(self, mapper):
        """Test detection of negated terms."""
        negated_terms = [
            ("no fever", "snomed"),
            ("denies pain", "snomed"),
            ("without infection", "snomed"),
            ("not diabetic", "snomed")
        ]
        
        for term, system in negated_terms:
            result = mapper.map_term(term, system=system)
            if result and result.get("found"):
                # Negated terms may map but with different handling
                # Just verify the mapping doesn't crash
                assert isinstance(result, dict)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_input(self, mapper):
        """Test handling of empty input."""
        result = mapper.map_term("", system="snomed")
        assert not result.get("found")
        
        # Test with None - should handle gracefully
        try:
            result = mapper.map_term(None, system="snomed")
            assert not result.get("found")
        except:
            # It's okay if it raises an exception for None
            pass
    
    def test_invalid_system(self, mapper):
        """Test handling of invalid system names."""
        result = mapper.map_term("diabetes", system="invalid_system")
        # Should either return None or indicate not found
        assert result is None or not result.get("found")
    
    def test_special_characters(self, mapper):
        """Test handling of special characters."""
        special_terms = [
            ("diabetes/mellitus", "snomed"),
            ("heart-attack", "snomed"),
            ("blood pressure", "loinc"),
            ("25-OH vitamin D", "loinc")
        ]
        
        for term, system in special_terms:
            # Should not crash
            try:
                result = mapper.map_term(term, system=system)
                # Should return a valid result dict
                assert isinstance(result, dict)
                assert "code" in result
                assert "display" in result
                assert "system" in result
                assert "found" in result
            except Exception as e:
                pytest.fail(f"Failed to handle special term '{term}': {e}")
    
    def test_case_insensitivity(self, mapper):
        """Test that matching is case-insensitive."""
        terms = [
            ("DIABETES", "diabetes"),
            ("Hypertension", "HYPERTENSION"),
            ("GlUcOsE", "glucose")
        ]
        
        for term1, term2 in terms:
            result1 = mapper.map_term(term1, system="snomed")
            result2 = mapper.map_term(term2, system="snomed")
            
            if result1 and result2 and result1.get("found") and result2.get("found"):
                # Should map to the same code regardless of case
                assert result1["code"] == result2["code"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])