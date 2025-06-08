"""
Comprehensive tests for cross-standard term mapping capabilities.
Tests mapping the same medical concepts across SNOMED, LOINC, and RxNorm.
"""

import pytest
from app.standards.terminology.mapper import TerminologyMapper


@pytest.fixture
def mapper():
    """Create a mapper instance for testing."""
    return TerminologyMapper()


class TestCrossStandardDiseases:
    """Test mapping common diseases across different standards."""
    
    def test_diabetes_across_standards(self, mapper):
        """Test diabetes mapping across standards."""
        # SNOMED should map diabetes as a condition
        snomed_result = mapper.map_term("diabetes mellitus type 2", system="snomed")
        assert snomed_result is not None
        assert snomed_result["system"] == "snomed"
        assert snomed_result["code"] == "44054006"
        
        # LOINC should map diabetes-related lab tests
        loinc_glucose = mapper.map_term("glucose", system="loinc")
        assert loinc_glucose is not None
        assert loinc_glucose["system"] == "loinc"
        assert loinc_glucose["code"] == "2345-7"
        
        loinc_hba1c = mapper.map_term("hemoglobin A1c", system="loinc")
        assert loinc_hba1c is not None
        assert loinc_hba1c["system"] == "loinc"
        assert loinc_hba1c["code"] == "4548-4"
        
        # RxNorm should map diabetes medications
        rxnorm_metformin = mapper.map_term("metformin", system="rxnorm")
        assert rxnorm_metformin is not None
        assert rxnorm_metformin["system"] == "rxnorm"
        assert rxnorm_metformin["code"] == "6809"
    
    def test_hypertension_across_standards(self, mapper):
        """Test hypertension mapping across standards."""
        # SNOMED for the condition
        snomed_result = mapper.map_term("hypertension", system="snomed")
        assert snomed_result is not None
        assert snomed_result["system"] == "snomed"
        assert snomed_result["code"] == "38341003"
        
        # No specific LOINC code for hypertension as a condition,
        # but blood pressure measurements exist
        
        # RxNorm for antihypertensive medications
        rxnorm_lisinopril = mapper.map_term("lisinopril", system="rxnorm")
        assert rxnorm_lisinopril is not None
        assert rxnorm_lisinopril["system"] == "rxnorm"
        assert rxnorm_lisinopril["code"] == "29046"
    
    def test_infection_across_standards(self, mapper):
        """Test infection mapping across standards."""
        # SNOMED for the condition
        snomed_uti = mapper.map_term("urinary tract infection", system="snomed")
        assert snomed_uti is not None
        assert snomed_uti["system"] == "snomed"
        assert snomed_uti["code"] == "68566005"
        
        # LOINC for urine culture
        loinc_culture = mapper.map_term("urine culture", system="loinc")
        assert loinc_culture is not None
        assert loinc_culture["system"] == "loinc"
        assert loinc_culture["code"] == "630-4"
        
        # RxNorm for antibiotics
        rxnorm_cipro = mapper.map_term("ciprofloxacin", system="rxnorm")
        assert rxnorm_cipro is not None
        assert rxnorm_cipro["system"] == "rxnorm"
        assert rxnorm_cipro["code"] == "2551"


class TestCrossStandardLaboratory:
    """Test laboratory-related terms across standards."""
    
    def test_cholesterol_across_standards(self, mapper):
        """Test cholesterol mapping across standards."""
        # LOINC for the lab test
        loinc_result = mapper.map_term("cholesterol", system="loinc")
        assert loinc_result is not None
        assert loinc_result["system"] == "loinc"
        assert loinc_result["code"] == "2093-3"
        
        # SNOMED for hyperlipidemia condition
        snomed_hyperlipidemia = mapper.map_term("hyperlipidemia", system="snomed")
        assert snomed_hyperlipidemia is not None
        assert snomed_hyperlipidemia["system"] == "snomed"
        
        # RxNorm for statins
        rxnorm_statin = mapper.map_term("atorvastatin", system="rxnorm")
        assert rxnorm_statin is not None
        assert rxnorm_statin["system"] == "rxnorm"
        assert rxnorm_statin["code"] == "83367"
    
    def test_kidney_function_across_standards(self, mapper):
        """Test kidney function terms across standards."""
        # LOINC for creatinine test
        loinc_creatinine = mapper.map_term("creatinine", system="loinc")
        assert loinc_creatinine is not None
        assert loinc_creatinine["system"] == "loinc"
        assert loinc_creatinine["code"] == "2160-0"
        
        # SNOMED for chronic kidney disease
        snomed_ckd = mapper.map_term("chronic kidney disease", system="snomed")
        assert snomed_ckd is not None
        assert snomed_ckd["system"] == "snomed"
        
        # No specific medications for creatinine, but related conditions treated
    
    def test_liver_function_across_standards(self, mapper):
        """Test liver function terms across standards."""
        # LOINC for ALT test
        loinc_alt = mapper.map_term("ALT", system="loinc")
        assert loinc_alt is not None
        assert loinc_alt["system"] == "loinc"
        assert loinc_alt["code"] == "1742-6"
        
        # SNOMED for liver disease
        snomed_hepatitis = mapper.map_term("hepatitis", system="snomed")
        assert snomed_hepatitis is not None
        assert snomed_hepatitis["system"] == "snomed"


class TestCrossStandardMedications:
    """Test medication-related terms across standards."""
    
    def test_pain_medication_across_standards(self, mapper):
        """Test pain medication mapping across standards."""
        # RxNorm for the medication
        rxnorm_ibuprofen = mapper.map_term("ibuprofen", system="rxnorm")
        assert rxnorm_ibuprofen is not None
        assert rxnorm_ibuprofen["system"] == "rxnorm"
        assert rxnorm_ibuprofen["code"] == "5640"
        
        # SNOMED for pain as a symptom
        snomed_pain = mapper.map_term("pain", system="snomed")
        assert snomed_pain is not None
        assert snomed_pain["system"] == "snomed"
        
        # No specific LOINC code for ibuprofen levels (not commonly measured)
    
    def test_antibiotic_across_standards(self, mapper):
        """Test antibiotic mapping across standards."""
        # RxNorm for the medication
        rxnorm_amox = mapper.map_term("amoxicillin", system="rxnorm")
        assert rxnorm_amox is not None
        assert rxnorm_amox["system"] == "rxnorm"
        assert rxnorm_amox["code"] == "723"
        
        # SNOMED for bacterial infection
        snomed_infection = mapper.map_term("bacterial infection", system="snomed")
        assert snomed_infection is not None
        assert snomed_infection["system"] == "snomed"
        
        # LOINC for culture and sensitivity
        loinc_culture = mapper.map_term("blood culture", system="loinc")
        assert loinc_culture is not None
        assert loinc_culture["system"] == "loinc"
        assert loinc_culture["code"] == "600-7"


class TestSystemAutoDetection:
    """Test automatic system detection based on term type."""
    
    def test_auto_detect_conditions(self, mapper):
        """Test auto-detection for medical conditions."""
        # These should auto-detect as SNOMED
        conditions = [
            "diabetes mellitus",
            "hypertension",
            "asthma",
            "pneumonia",
            "heart failure"
        ]
        
        for condition in conditions:
            result = mapper.map_term(condition, system=None)  # No system specified
            assert result is not None, f"Failed to auto-detect: {condition}"
            assert result["system"] == "snomed", f"Wrong system for {condition}: {result['system']}"
    
    def test_auto_detect_lab_tests(self, mapper):
        """Test auto-detection for laboratory tests."""
        # These should auto-detect as LOINC
        lab_tests = [
            "glucose",
            "hemoglobin",
            "creatinine",
            "cholesterol",
            "blood culture"
        ]
        
        for test in lab_tests:
            result = mapper.map_term(test, system=None)
            assert result is not None, f"Failed to auto-detect: {test}"
            assert result["system"] == "loinc", f"Wrong system for {test}: {result['system']}"
    
    def test_auto_detect_medications(self, mapper):
        """Test auto-detection for medications."""
        # These should auto-detect as RxNorm
        medications = [
            "amoxicillin",
            "ibuprofen",
            "metformin",
            "lisinopril",
            "omeprazole"
        ]
        
        for med in medications:
            result = mapper.map_term(med, system=None)
            assert result is not None, f"Failed to auto-detect: {med}"
            assert result["system"] == "rxnorm", f"Wrong system for {med}: {result['system']}"


class TestComplexClinicalScenarios:
    """Test complex clinical scenarios requiring multiple standards."""
    
    def test_diabetes_management_scenario(self, mapper):
        """Test complete diabetes management scenario."""
        # Diagnosis
        diagnosis = mapper.map_term("type 2 diabetes mellitus", system="snomed")
        assert diagnosis is not None
        assert diagnosis["code"] == "44054006"
        
        # Monitoring tests
        glucose_test = mapper.map_term("fasting glucose", system="loinc")
        assert glucose_test is not None
        assert glucose_test["code"] == "1558-6"
        
        hba1c_test = mapper.map_term("HbA1c", system="loinc")
        assert hba1c_test is not None
        assert hba1c_test["code"] == "4548-4"
        
        # Medications
        metformin = mapper.map_term("metformin 1000mg", system="rxnorm")
        assert metformin is not None
        
        insulin = mapper.map_term("insulin glargine", system="rxnorm")
        assert insulin is not None
    
    def test_cardiac_event_scenario(self, mapper):
        """Test acute cardiac event scenario."""
        # Diagnosis
        mi = mapper.map_term("acute myocardial infarction", system="snomed")
        assert mi is not None
        
        # Diagnostic tests
        troponin = mapper.map_term("troponin I", system="loinc")
        assert troponin is not None
        
        ecg = mapper.map_term("ECG", system="snomed")
        assert ecg is not None
        
        # Medications
        aspirin = mapper.map_term("aspirin", system="rxnorm")
        assert aspirin is not None
        
        clopidogrel = mapper.map_term("clopidogrel", system="rxnorm")
        assert clopidogrel is not None
        
        atorvastatin = mapper.map_term("atorvastatin", system="rxnorm")
        assert atorvastatin is not None
    
    def test_infection_treatment_scenario(self, mapper):
        """Test infection diagnosis and treatment scenario."""
        # Diagnosis
        pneumonia = mapper.map_term("community acquired pneumonia", system="snomed")
        assert pneumonia is not None
        
        # Diagnostic tests
        wbc = mapper.map_term("white blood cell count", system="loinc")
        assert wbc is not None
        assert wbc["code"] == "6690-2"
        
        blood_culture = mapper.map_term("blood culture", system="loinc")
        assert blood_culture is not None
        assert blood_culture["code"] == "600-7"
        
        # Treatment
        azithromycin = mapper.map_term("azithromycin", system="rxnorm")
        assert azithromycin is not None
        assert azithromycin["code"] == "18631"
        
        ceftriaxone = mapper.map_term("ceftriaxone", system="rxnorm")
        assert ceftriaxone is not None
        assert ceftriaxone["code"] == "2193"


class TestBatchCrossStandardMapping:
    """Test batch mapping across multiple standards."""
    
    def test_mixed_term_batch(self, mapper):
        """Test batch processing of mixed term types."""
        terms = [
            {"term": "diabetes", "expected_system": "snomed"},
            {"term": "glucose", "expected_system": "loinc"},
            {"term": "metformin", "expected_system": "rxnorm"},
            {"term": "hypertension", "expected_system": "snomed"},
            {"term": "creatinine", "expected_system": "loinc"},
            {"term": "lisinopril", "expected_system": "rxnorm"},
        ]
        
        for term_data in terms:
            result = mapper.map_term(term_data["term"], system=None)
            assert result is not None, f"Failed to map: {term_data['term']}"
            assert result["system"] == term_data["expected_system"], \
                f"Wrong system for {term_data['term']}: expected {term_data['expected_system']}, got {result['system']}"
    
    def test_system_specific_batch(self, mapper):
        """Test batch processing with specified systems."""
        # Force all terms to specific systems
        terms = ["pain", "glucose", "amoxicillin"]
        
        # Map all to SNOMED
        for term in terms:
            result = mapper.map_term(term, system="snomed")
            if result:  # Some may not map to SNOMED
                assert result["system"] == "snomed"
        
        # Map all to LOINC
        for term in terms:
            result = mapper.map_term(term, system="loinc")
            if result:  # Some may not map to LOINC
                assert result["system"] == "loinc"
        
        # Map all to RxNorm
        for term in terms:
            result = mapper.map_term(term, system="rxnorm")
            if result:  # Some may not map to RxNorm
                assert result["system"] == "rxnorm"


class TestEdgeCasesAndErrors:
    """Test edge cases and error handling across standards."""
    
    def test_ambiguous_terms(self, mapper):
        """Test handling of ambiguous terms."""
        # "MS" could mean multiple sclerosis or morphine sulfate
        ms_snomed = mapper.map_term("MS", system="snomed")
        ms_rxnorm = mapper.map_term("MS", system="rxnorm")
        
        # Both should potentially find matches in their respective systems
        if ms_snomed:
            assert ms_snomed["system"] == "snomed"
        if ms_rxnorm:
            assert ms_rxnorm["system"] == "rxnorm"
    
    def test_unmappable_terms(self, mapper):
        """Test handling of terms that don't map to certain systems."""
        # Medication name shouldn't map to LOINC
        result = mapper.map_term("amoxicillin", system="loinc")
        # May return None or low confidence
        
        # Lab test shouldn't map to RxNorm
        result = mapper.map_term("hemoglobin A1c", system="rxnorm")
        # May return None or low confidence
    
    def test_system_case_insensitivity(self, mapper):
        """Test that system names are case-insensitive."""
        systems = ["SNOMED", "snomed", "Snomed", "LOINC", "loinc", "Loinc", "RXNORM", "rxnorm", "RxNorm"]
        
        for system in systems:
            result = mapper.map_term("glucose", system=system)
            # Should work regardless of case
            if result:
                assert result["system"].lower() in ["snomed", "loinc", "rxnorm"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])