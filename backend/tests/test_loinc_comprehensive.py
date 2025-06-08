"""
Comprehensive tests for LOINC term mapping capabilities.
Tests a wide range of laboratory tests, observations, and measurements.
"""

import pytest
from app.standards.terminology.mapper import TerminologyMapper


@pytest.fixture
def mapper():
    """Create a mapper instance for testing."""
    return TerminologyMapper()


class TestLOINCBloodChemistry:
    """Test mapping of blood chemistry tests to LOINC."""
    
    def test_glucose_tests(self, mapper):
        """Test glucose-related test mappings."""
        test_cases = [
            ("glucose", "2345-7"),  # Glucose [Mass/volume] in Serum or Plasma
            ("blood glucose", "2345-7"),
            ("serum glucose", "2345-7"),
            ("plasma glucose", "2345-7"),
            ("fasting glucose", "1558-6"),  # Fasting glucose
            ("random glucose", "2345-7"),
            ("glucose tolerance test", "20438-8"),  # Glucose tolerance test
            ("GTT", "20438-8"),
            ("hemoglobin A1c", "4548-4"),  # Hemoglobin A1c
            ("HbA1c", "4548-4"),
            ("glycated hemoglobin", "4548-4"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
            assert result["confidence"] >= 0.7, f"Low confidence for {term}: {result['confidence']}"
    
    def test_lipid_panel(self, mapper):
        """Test lipid panel test mappings."""
        test_cases = [
            ("cholesterol", "2093-3"),  # Cholesterol [Mass/volume] in Serum or Plasma
            ("total cholesterol", "2093-3"),
            ("serum cholesterol", "2093-3"),
            ("HDL cholesterol", "2085-9"),  # HDL Cholesterol
            ("HDL", "2085-9"),
            ("high density lipoprotein", "2085-9"),
            ("LDL cholesterol", "2089-1"),  # LDL Cholesterol
            ("LDL", "2089-1"),
            ("low density lipoprotein", "2089-1"),
            ("triglycerides", "2571-8"),  # Triglyceride
            ("TG", "2571-8"),
            ("lipid panel", "24331-1"),  # Lipid panel
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_liver_function_tests(self, mapper):
        """Test liver function test mappings."""
        test_cases = [
            ("ALT", "1742-6"),  # Alanine aminotransferase
            ("SGPT", "1742-6"),
            ("alanine aminotransferase", "1742-6"),
            ("AST", "1920-8"),  # Aspartate aminotransferase
            ("SGOT", "1920-8"),
            ("aspartate aminotransferase", "1920-8"),
            ("alkaline phosphatase", "6768-6"),
            ("ALP", "6768-6"),
            ("bilirubin", "1975-2"),  # Bilirubin.total
            ("total bilirubin", "1975-2"),
            ("direct bilirubin", "1968-7"),
            ("albumin", "1751-7"),  # Albumin
            ("serum albumin", "1751-7"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_kidney_function_tests(self, mapper):
        """Test kidney function test mappings."""
        test_cases = [
            ("creatinine", "2160-0"),  # Creatinine
            ("serum creatinine", "2160-0"),
            ("BUN", "3094-0"),  # Blood urea nitrogen
            ("blood urea nitrogen", "3094-0"),
            ("urea nitrogen", "3094-0"),
            ("GFR", "33914-3"),  # Glomerular filtration rate
            ("glomerular filtration rate", "33914-3"),
            ("eGFR", "33914-3"),
            ("uric acid", "3084-1"),  # Uric acid
            ("serum uric acid", "3084-1"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_electrolytes(self, mapper):
        """Test electrolyte test mappings."""
        test_cases = [
            ("sodium", "2951-2"),  # Sodium
            ("Na", "2951-2"),
            ("serum sodium", "2951-2"),
            ("potassium", "2823-3"),  # Potassium
            ("K", "2823-3"),
            ("serum potassium", "2823-3"),
            ("chloride", "2075-0"),  # Chloride
            ("Cl", "2075-0"),
            ("serum chloride", "2075-0"),
            ("bicarbonate", "2028-9"),  # Carbon dioxide
            ("CO2", "2028-9"),
            ("carbon dioxide", "2028-9"),
            ("calcium", "17861-6"),  # Calcium
            ("Ca", "17861-6"),
            ("serum calcium", "17861-6"),
            ("magnesium", "2601-3"),  # Magnesium
            ("Mg", "2601-3"),
            ("phosphorus", "2777-1"),  # Phosphate
            ("phosphate", "2777-1"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestLOINCHematology:
    """Test mapping of hematology tests to LOINC."""
    
    def test_complete_blood_count(self, mapper):
        """Test CBC component mappings."""
        test_cases = [
            ("hemoglobin", "718-7"),  # Hemoglobin
            ("Hgb", "718-7"),
            ("Hb", "718-7"),
            ("hematocrit", "4544-3"),  # Hematocrit
            ("Hct", "4544-3"),
            ("white blood cell count", "6690-2"),  # WBC count
            ("WBC", "6690-2"),
            ("leukocyte count", "6690-2"),
            ("red blood cell count", "789-8"),  # RBC count
            ("RBC", "789-8"),
            ("erythrocyte count", "789-8"),
            ("platelet count", "777-3"),  # Platelet count
            ("PLT", "777-3"),
            ("thrombocyte count", "777-3"),
            ("MCV", "787-2"),  # Mean corpuscular volume
            ("mean corpuscular volume", "787-2"),
            ("MCH", "785-6"),  # Mean corpuscular hemoglobin
            ("MCHC", "786-4"),  # Mean corpuscular hemoglobin concentration
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_differential_count(self, mapper):
        """Test differential count mappings."""
        test_cases = [
            ("neutrophils", "751-8"),  # Neutrophils [#/volume]
            ("neutrophil count", "751-8"),
            ("lymphocytes", "731-0"),  # Lymphocytes [#/volume]
            ("lymphocyte count", "731-0"),
            ("monocytes", "742-7"),  # Monocytes [#/volume]
            ("monocyte count", "742-7"),
            ("eosinophils", "711-2"),  # Eosinophils [#/volume]
            ("eosinophil count", "711-2"),
            ("basophils", "704-7"),  # Basophils [#/volume]
            ("basophil count", "704-7"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_coagulation_studies(self, mapper):
        """Test coagulation study mappings."""
        test_cases = [
            ("PT", "5902-2"),  # Prothrombin time
            ("prothrombin time", "5902-2"),
            ("INR", "5894-1"),  # International normalized ratio
            ("international normalized ratio", "5894-1"),
            ("PTT", "3173-2"),  # Activated partial thromboplastin time
            ("aPTT", "3173-2"),
            ("partial thromboplastin time", "3173-2"),
            ("fibrinogen", "3255-7"),  # Fibrinogen
            ("D-dimer", "30240-6"),  # D-dimer
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestLOINCUrinalysis:
    """Test mapping of urinalysis tests to LOINC."""
    
    def test_basic_urinalysis(self, mapper):
        """Test basic urinalysis component mappings."""
        test_cases = [
            ("urine pH", "2756-5"),  # pH of Urine
            ("urine specific gravity", "2965-2"),  # Specific gravity of Urine
            ("urine protein", "2888-6"),  # Protein [Mass/volume] in Urine
            ("urine glucose", "2350-7"),  # Glucose [Mass/volume] in Urine
            ("urine ketones", "2514-8"),  # Ketones [Mass/volume] in Urine
            ("urine blood", "5794-3"),  # Blood [Presence] in Urine
            ("urine nitrite", "5802-4"),  # Nitrite [Presence] in Urine
            ("urine leukocyte esterase", "5799-2"),  # Leukocyte esterase [Presence] in Urine
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_urine_microscopy(self, mapper):
        """Test urine microscopy mappings."""
        test_cases = [
            ("urine RBC", "30391-7"),  # RBC [#/area] in Urine sediment
            ("urine red blood cells", "30391-7"),
            ("urine WBC", "30405-5"),  # WBC [#/area] in Urine sediment
            ("urine white blood cells", "30405-5"),
            ("urine bacteria", "25145-4"),  # Bacteria [Presence] in Urine sediment
            ("urine crystals", "5767-9"),  # Crystals [Presence] in Urine sediment
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestLOINCMicrobiology:
    """Test mapping of microbiology tests to LOINC."""
    
    def test_culture_tests(self, mapper):
        """Test culture test mappings."""
        test_cases = [
            ("blood culture", "600-7"),  # Bacteria identified in Blood by Culture
            ("urine culture", "630-4"),  # Bacteria identified in Urine by Culture
            ("sputum culture", "624-0"),  # Bacteria identified in Sputum by Culture
            ("throat culture", "626-5"),  # Bacteria identified in Throat by Culture
            ("wound culture", "6462-6"),  # Bacteria identified in Wound by Culture
            ("stool culture", "625-7"),  # Bacteria identified in Stool by Culture
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_sensitivity_tests(self, mapper):
        """Test antibiotic sensitivity mappings."""
        test_cases = [
            ("antibiotic sensitivity", "18769-0"),  # Antibiotic susceptibility
            ("antimicrobial susceptibility", "18769-0"),
            ("MIC", "28-1"),  # Minimum inhibitory concentration
            ("minimum inhibitory concentration", "28-1"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestLOINCHormones:
    """Test mapping of hormone tests to LOINC."""
    
    def test_thyroid_function(self, mapper):
        """Test thyroid function test mappings."""
        test_cases = [
            ("TSH", "3016-3"),  # Thyroid stimulating hormone
            ("thyroid stimulating hormone", "3016-3"),
            ("T4", "3026-2"),  # Thyroxine
            ("thyroxine", "3026-2"),
            ("free T4", "3024-7"),  # Thyroxine free
            ("T3", "3053-6"),  # Triiodothyronine
            ("triiodothyronine", "3053-6"),
            ("free T3", "3051-0"),  # Triiodothyronine free
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_reproductive_hormones(self, mapper):
        """Test reproductive hormone mappings."""
        test_cases = [
            ("testosterone", "2986-8"),  # Testosterone
            ("estradiol", "2243-4"),  # Estradiol
            ("progesterone", "2839-9"),  # Progesterone
            ("LH", "10501-5"),  # Luteinizing hormone
            ("luteinizing hormone", "10501-5"),
            ("FSH", "15067-2"),  # Follicle stimulating hormone
            ("follicle stimulating hormone", "15067-2"),
            ("prolactin", "2842-3"),  # Prolactin
            ("beta hCG", "19080-1"),  # Human chorionic gonadotropin
            ("pregnancy test", "2106-3"),  # Pregnancy test
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_other_hormones(self, mapper):
        """Test other hormone mappings."""
        test_cases = [
            ("cortisol", "2143-6"),  # Cortisol
            ("ACTH", "2141-0"),  # Adrenocorticotropic hormone
            ("growth hormone", "2484-4"),  # Growth hormone
            ("insulin", "20448-7"),  # Insulin
            ("PTH", "2731-8"),  # Parathyroid hormone
            ("parathyroid hormone", "2731-8"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestLOINCTumorMarkers:
    """Test mapping of tumor markers to LOINC."""
    
    def test_common_tumor_markers(self, mapper):
        """Test common tumor marker mappings."""
        test_cases = [
            ("PSA", "2857-1"),  # Prostate specific antigen
            ("prostate specific antigen", "2857-1"),
            ("CEA", "2039-6"),  # Carcinoembryonic antigen
            ("carcinoembryonic antigen", "2039-6"),
            ("CA 125", "10334-1"),  # Cancer antigen 125
            ("CA 19-9", "24108-3"),  # Cancer antigen 19-9
            ("AFP", "1834-1"),  # Alpha fetoprotein
            ("alpha fetoprotein", "1834-1"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestLOINCCardiacMarkers:
    """Test mapping of cardiac markers to LOINC."""
    
    def test_cardiac_enzymes(self, mapper):
        """Test cardiac enzyme mappings."""
        test_cases = [
            ("troponin", "6598-7"),  # Troponin I
            ("troponin I", "42757-5"),  # Troponin I cardiac
            ("troponin T", "6597-9"),  # Troponin T
            ("CK-MB", "13969-1"),  # Creatine kinase MB
            ("creatine kinase MB", "13969-1"),
            ("BNP", "30934-4"),  # Brain natriuretic peptide
            ("brain natriuretic peptide", "30934-4"),
            ("NT-proBNP", "33762-6"),  # N-terminal proBNP
            ("myoglobin", "2154-3"),  # Myoglobin
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestLOINCVitaminsAndNutrition:
    """Test mapping of vitamin and nutrition tests to LOINC."""
    
    def test_vitamin_tests(self, mapper):
        """Test vitamin test mappings."""
        test_cases = [
            ("vitamin D", "1989-3"),  # Vitamin D
            ("25-hydroxyvitamin D", "1989-3"),
            ("vitamin B12", "2132-9"),  # Vitamin B12
            ("cobalamin", "2132-9"),
            ("folate", "2284-8"),  # Folate
            ("folic acid", "2284-8"),
            ("vitamin A", "2923-1"),  # Vitamin A
            ("vitamin E", "7832-3"),  # Vitamin E
            ("vitamin C", "1960-4"),  # Vitamin C
            ("ascorbic acid", "1960-4"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_mineral_tests(self, mapper):
        """Test mineral test mappings."""
        test_cases = [
            ("iron", "2498-4"),  # Iron
            ("serum iron", "2498-4"),
            ("ferritin", "2276-4"),  # Ferritin
            ("transferrin", "3034-6"),  # Transferrin
            ("TIBC", "2500-7"),  # Total iron binding capacity
            ("zinc", "5757-0"),  # Zinc
            ("copper", "5637-4"),  # Copper
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="loinc")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestLOINCFuzzyMatching:
    """Test fuzzy matching capabilities for LOINC terms."""
    
    def test_misspellings(self, mapper):
        """Test handling of common misspellings."""
        test_cases = [
            ("hemoglobin a1c", "4548-4"),  # HbA1c
            ("creatinin", "2160-0"),  # creatinine
            ("billirubin", "1975-2"),  # bilirubin
            ("tryglicerides", "2571-8"),  # triglycerides
            ("prothrombine time", "5902-2"),  # prothrombin time
        ]
        
        for misspelled, expected_code in test_cases:
            result = mapper.map_term(misspelled, system="loinc")
            assert result is not None, f"Failed to map misspelling: {misspelled}"
            assert result["code"] == expected_code, f"Wrong code for {misspelled}: got {result['code']}, expected {expected_code}"
            assert result["confidence"] >= 0.6, f"Confidence too low for {misspelled}: {result['confidence']}"
    
    def test_abbreviation_variants(self, mapper):
        """Test abbreviation variant handling."""
        test_cases = [
            ("Hgb A1c", "4548-4"),  # HbA1c
            ("Hb A1C", "4548-4"),
            ("SGPT", "1742-6"),  # ALT
            ("SGOT", "1920-8"),  # AST
            ("Alk Phos", "6768-6"),  # Alkaline phosphatase
        ]
        
        for variant, expected_code in test_cases:
            result = mapper.map_term(variant, system="loinc")
            assert result is not None, f"Failed to map variant: {variant}"
            assert result["code"] == expected_code, f"Wrong code for {variant}: got {result['code']}, expected {expected_code}"


class TestLOINCContextAwareMapping:
    """Test context-aware mapping for LOINC terms."""
    
    def test_glucose_context(self, mapper):
        """Test glucose mapping with different contexts."""
        # Glucose in different contexts
        result_blood = mapper.map_term("glucose", context="blood test", system="loinc")
        result_urine = mapper.map_term("glucose", context="urinalysis", system="loinc")
        result_fasting = mapper.map_term("glucose", context="fasting", system="loinc")
        
        assert result_blood is not None and result_blood["code"] == "2345-7"  # Blood glucose
        assert result_urine is not None and result_urine["code"] == "2350-7"  # Urine glucose
        assert result_fasting is not None and result_fasting["code"] == "1558-6"  # Fasting glucose
    
    def test_protein_context(self, mapper):
        """Test protein mapping with different contexts."""
        # Protein in different contexts
        result_serum = mapper.map_term("protein", context="blood chemistry", system="loinc")
        result_urine = mapper.map_term("protein", context="urinalysis", system="loinc")
        
        assert result_serum is not None and result_serum["code"] == "2885-2"  # Total protein
        assert result_urine is not None and result_urine["code"] == "2888-6"  # Urine protein


if __name__ == "__main__":
    pytest.main([__file__, "-v"])