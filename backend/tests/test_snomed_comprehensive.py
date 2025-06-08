"""
Comprehensive tests for SNOMED CT term mapping capabilities.
Tests a wide range of medical conditions, symptoms, and findings.
"""

import pytest
from app.standards.terminology.mapper import TerminologyMapper


@pytest.fixture
def mapper():
    """Create a mapper instance for testing."""
    return TerminologyMapper()


class TestSNOMEDConditions:
    """Test mapping of common medical conditions to SNOMED CT."""
    
    def test_diabetes_variations(self, mapper):
        """Test different ways to express diabetes."""
        test_cases = [
            ("diabetes mellitus type 2", "44054006"),
            ("type 2 diabetes", "44054006"),
            ("T2DM", "44054006"),
            ("diabetes type II", "44054006"),
            ("non-insulin dependent diabetes", "44054006"),
            ("diabetes mellitus type 1", "46635009"),
            ("type 1 diabetes", "46635009"),
            ("T1DM", "46635009"),
            ("insulin dependent diabetes", "46635009"),
            ("juvenile diabetes", "46635009"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
            assert result["confidence"] >= 0.7, f"Low confidence for {term}: {result['confidence']}"
    
    def test_cardiovascular_conditions(self, mapper):
        """Test cardiovascular disease mappings."""
        test_cases = [
            ("hypertension", "38341003"),
            ("high blood pressure", "38341003"),
            ("HTN", "38341003"),
            ("essential hypertension", "59621000"),
            ("myocardial infarction", "22298006"),
            ("heart attack", "22298006"),
            ("MI", "22298006"),
            ("acute MI", "57054005"),
            ("congestive heart failure", "42343007"),
            ("CHF", "42343007"),
            ("heart failure", "84114007"),
            ("atrial fibrillation", "49436004"),
            ("afib", "49436004"),
            ("coronary artery disease", "53741008"),
            ("CAD", "53741008"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_respiratory_conditions(self, mapper):
        """Test respiratory condition mappings."""
        test_cases = [
            ("asthma", "195967001"),
            ("bronchial asthma", "195967001"),
            ("COPD", "13645005"),
            ("chronic obstructive pulmonary disease", "13645005"),
            ("pneumonia", "233604007"),
            ("community acquired pneumonia", "385093006"),
            ("CAP", "385093006"),
            ("bronchitis", "32398004"),
            ("acute bronchitis", "10509002"),
            ("chronic bronchitis", "63480004"),
            ("pulmonary embolism", "59282003"),
            ("PE", "59282003"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_neurological_conditions(self, mapper):
        """Test neurological condition mappings."""
        test_cases = [
            ("stroke", "230690007"),
            ("CVA", "230690007"),
            ("cerebrovascular accident", "230690007"),
            ("migraine", "37796009"),
            ("epilepsy", "84757009"),
            ("seizure disorder", "84757009"),
            ("Parkinson's disease", "49049000"),
            ("Parkinsons", "49049000"),
            ("Alzheimer's disease", "26929004"),
            ("Alzheimers", "26929004"),
            ("multiple sclerosis", "24700007"),
            ("MS", "24700007"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_gastrointestinal_conditions(self, mapper):
        """Test GI condition mappings."""
        test_cases = [
            ("GERD", "235595009"),
            ("gastroesophageal reflux disease", "235595009"),
            ("acid reflux", "698065002"),
            ("peptic ulcer", "13200003"),
            ("gastric ulcer", "44989001"),
            ("duodenal ulcer", "51868009"),
            ("IBS", "10743008"),
            ("irritable bowel syndrome", "10743008"),
            ("Crohn's disease", "34000006"),
            ("Crohns", "34000006"),
            ("ulcerative colitis", "64766004"),
            ("UC", "64766004"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_infectious_diseases(self, mapper):
        """Test infectious disease mappings."""
        test_cases = [
            ("COVID-19", "840539006"),
            ("coronavirus disease 2019", "840539006"),
            ("SARS-CoV-2 infection", "840539006"),
            ("influenza", "6142004"),
            ("flu", "6142004"),
            ("urinary tract infection", "68566005"),
            ("UTI", "68566005"),
            ("cellulitis", "128045006"),
            ("sepsis", "91302008"),
            ("tuberculosis", "56717001"),
            ("TB", "56717001"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestSNOMEDSymptoms:
    """Test mapping of symptoms and clinical findings to SNOMED CT."""
    
    def test_pain_symptoms(self, mapper):
        """Test pain-related symptom mappings."""
        test_cases = [
            ("chest pain", "29857009"),
            ("abdominal pain", "21522001"),
            ("headache", "25064002"),
            ("back pain", "161891005"),
            ("low back pain", "279039007"),
            ("joint pain", "57676002"),
            ("arthralgia", "57676002"),
            ("muscle pain", "68962001"),
            ("myalgia", "68962001"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_respiratory_symptoms(self, mapper):
        """Test respiratory symptom mappings."""
        test_cases = [
            ("cough", "49727002"),
            ("dyspnea", "267036007"),
            ("shortness of breath", "267036007"),
            ("SOB", "267036007"),
            ("wheezing", "56018004"),
            ("hemoptysis", "66857006"),
            ("coughing up blood", "66857006"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_general_symptoms(self, mapper):
        """Test general symptom mappings."""
        test_cases = [
            ("fever", "386661006"),
            ("pyrexia", "386661006"),
            ("fatigue", "84229001"),
            ("tiredness", "267032009"),
            ("nausea", "422587007"),
            ("vomiting", "422400008"),
            ("dizziness", "404640003"),
            ("vertigo", "399153001"),
            ("weight loss", "161833006"),
            ("edema", "20741006"),
            ("swelling", "20741006"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestSNOMEDProcedures:
    """Test mapping of medical procedures to SNOMED CT."""
    
    def test_surgical_procedures(self, mapper):
        """Test surgical procedure mappings."""
        test_cases = [
            ("appendectomy", "80146002"),
            ("cholecystectomy", "38102005"),
            ("gallbladder removal", "38102005"),
            ("coronary artery bypass graft", "232717009"),
            ("CABG", "232717009"),
            ("total knee replacement", "609588000"),
            ("TKR", "609588000"),
            ("hip replacement", "76915002"),
            ("THR", "76915002"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_diagnostic_procedures(self, mapper):
        """Test diagnostic procedure mappings."""
        test_cases = [
            ("colonoscopy", "73761001"),
            ("endoscopy", "423827005"),
            ("upper endoscopy", "386478006"),
            ("EGD", "386478006"),
            ("MRI", "113091000"),
            ("magnetic resonance imaging", "113091000"),
            ("CT scan", "77477000"),
            ("computed tomography", "77477000"),
            ("X-ray", "363680008"),
            ("radiography", "363680008"),
            ("ECG", "29303009"),
            ("electrocardiogram", "29303009"),
            ("EKG", "29303009"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestSNOMEDAnatomicalStructures:
    """Test mapping of anatomical structures to SNOMED CT."""
    
    def test_organs(self, mapper):
        """Test organ mappings."""
        test_cases = [
            ("heart", "80891009"),
            ("lung", "39607008"),
            ("liver", "10200004"),
            ("kidney", "64033007"),
            ("brain", "12738006"),
            ("stomach", "69695003"),
            ("pancreas", "15776009"),
            ("spleen", "78961009"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_body_parts(self, mapper):
        """Test body part mappings."""
        test_cases = [
            ("arm", "40983000"),
            ("leg", "30021000"),
            ("hand", "85562004"),
            ("foot", "56459004"),
            ("head", "69536005"),
            ("neck", "45048000"),
            ("chest", "51185008"),
            ("abdomen", "113345001"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="snomed")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestSNOMEDFuzzyMatching:
    """Test fuzzy matching capabilities for SNOMED terms."""
    
    def test_misspellings(self, mapper):
        """Test handling of common misspellings."""
        test_cases = [
            ("diabetis", "73211009"),  # diabetes
            ("hypertenshun", "38341003"),  # hypertension
            ("noomonia", "233604007"),  # pneumonia
            ("astma", "195967001"),  # asthma
            ("epilepsi", "84757009"),  # epilepsy
        ]
        
        for misspelled, expected_code in test_cases:
            result = mapper.map_term(misspelled, system="snomed")
            assert result is not None, f"Failed to map misspelling: {misspelled}"
            assert result["code"] == expected_code, f"Wrong code for {misspelled}: got {result['code']}, expected {expected_code}"
            assert result["confidence"] >= 0.6, f"Confidence too low for {misspelled}: {result['confidence']}"
    
    def test_abbreviation_expansion(self, mapper):
        """Test abbreviation expansion."""
        test_cases = [
            ("DM", "73211009"),  # diabetes mellitus
            ("HTN", "38341003"),  # hypertension
            ("CAD", "53741008"),  # coronary artery disease
            ("CHF", "42343007"),  # congestive heart failure
            ("COPD", "13645005"),  # chronic obstructive pulmonary disease
        ]
        
        for abbrev, expected_code in test_cases:
            result = mapper.map_term(abbrev, system="snomed")
            assert result is not None, f"Failed to map abbreviation: {abbrev}"
            assert result["code"] == expected_code, f"Wrong code for {abbrev}: got {result['code']}, expected {expected_code}"


class TestSNOMEDContextAwareMapping:
    """Test context-aware mapping for SNOMED terms."""
    
    def test_context_enhancement(self, mapper):
        """Test that context improves mapping accuracy."""
        # Test ambiguous terms with context
        result_no_context = mapper.map_term("MS", system="snomed")
        result_with_context = mapper.map_term("MS", context="neurological disorder", system="snomed")
        
        assert result_with_context is not None
        assert result_with_context["code"] == "24700007"  # multiple sclerosis
        if result_no_context:
            assert result_with_context["confidence"] > result_no_context["confidence"]
    
    def test_negation_handling(self, mapper):
        """Test handling of negated terms."""
        test_cases = [
            ("no fever", "386661006", 0.3),  # Should have low confidence due to negation
            ("denies chest pain", "29857009", 0.3),
            ("without cough", "49727002", 0.3),
        ]
        
        for term, expected_code, max_confidence in test_cases:
            result = mapper.map_term(term, system="snomed")
            if result:
                assert result["confidence"] <= max_confidence, f"Confidence too high for negated term {term}: {result['confidence']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])