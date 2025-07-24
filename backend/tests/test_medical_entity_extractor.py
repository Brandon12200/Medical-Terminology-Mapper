"""
Test the MedicalEntityExtractor with advanced NER capabilities
"""
import pytest
from app.ml.medical_entity_extractor import (
    MedicalEntityExtractor,
    EntityType,
    MedicalEntity,
    ConfidenceCalibrator,
    NegationDetector,
    UncertaintyDetector,
    EntityLinker,
    HierarchicalRecognizer
)


class TestConfidenceCalibrator:
    """Test confidence calibration"""
    
    def test_calibration(self):
        calibrator = ConfidenceCalibrator(temperature=1.5)
        scores = [0.9, 0.8, 0.7, 0.6]
        calibrated = calibrator.calibrate_scores(scores)
        
        # Calibrated scores should be less extreme
        assert all(0 < s < 1 for s in calibrated)
        assert calibrated[0] < scores[0]  # High confidence reduced
        assert calibrated[-1] > scores[-1]  # Low confidence increased


class TestNegationDetector:
    """Test negation detection"""
    
    def test_negation_patterns(self):
        detector = NegationDetector()
        
        # Test cases
        test_cases = [
            ("Patient denies chest pain", "chest pain", True),
            ("No evidence of diabetes", "diabetes", True),
            ("Negative for COVID-19", "COVID-19", True),
            ("Patient has diabetes", "diabetes", False),
            ("Chest pain present", "chest pain", False),
        ]
        
        for text, entity_text, expected_negation in test_cases:
            # Find entity position
            start = text.lower().find(entity_text.lower())
            end = start + len(entity_text)
            
            entity = MedicalEntity(
                text=entity_text,
                type=EntityType.CONDITION,
                start=start,
                end=end,
                confidence=0.9,
                raw_confidence=0.9
            )
            
            is_negated = detector.is_negated(entity, text)
            assert is_negated == expected_negation, f"Failed for: {text}"


class TestUncertaintyDetector:
    """Test uncertainty detection"""
    
    def test_uncertainty_patterns(self):
        detector = UncertaintyDetector()
        
        test_cases = [
            ("Possible pneumonia on chest x-ray", "pneumonia", True),
            ("Symptoms suggest diabetes", "diabetes", True),
            ("Likely viral infection", "viral infection", True),
            ("Confirmed diagnosis of pneumonia", "pneumonia", False),
            ("Patient has hypertension", "hypertension", False),
        ]
        
        for text, entity_text, expected_uncertainty in test_cases:
            start = text.lower().find(entity_text.lower())
            end = start + len(entity_text)
            
            entity = MedicalEntity(
                text=entity_text,
                type=EntityType.CONDITION,
                start=start,
                end=end,
                confidence=0.9,
                raw_confidence=0.9
            )
            
            is_uncertain = detector.is_uncertain(entity, text)
            assert is_uncertain == expected_uncertainty, f"Failed for: {text}"


class TestEntityLinker:
    """Test entity linking"""
    
    def test_entity_linking(self):
        linker = EntityLinker()
        
        # Test known entities
        diabetes_entity = MedicalEntity(
            text="diabetes",
            type=EntityType.CONDITION,
            start=0,
            end=8,
            confidence=0.9,
            raw_confidence=0.9
        )
        
        linked_id = linker.link_entity(diabetes_entity)
        assert linked_id == "SNOMED:73211009"
        
        # Test medication
        aspirin_entity = MedicalEntity(
            text="aspirin",
            type=EntityType.DRUG,
            start=0,
            end=7,
            confidence=0.9,
            raw_confidence=0.9
        )
        
        linked_id = linker.link_entity(aspirin_entity)
        assert linked_id == "RXNORM:1191"


class TestHierarchicalRecognizer:
    """Test hierarchical recognition"""
    
    def test_hierarchy(self):
        recognizer = HierarchicalRecognizer()
        
        # Test diabetes hierarchy
        diabetes_entity = MedicalEntity(
            text="type 2 diabetes",
            type=EntityType.CONDITION,
            start=0,
            end=15,
            confidence=0.9,
            raw_confidence=0.9
        )
        
        hierarchy = recognizer.get_hierarchy(diabetes_entity)
        assert hierarchy is not None
        assert "diabetes" in hierarchy
        assert "endocrine disorder" in hierarchy


class TestMedicalEntityExtractor:
    """Test the complete MedicalEntityExtractor"""
    
    @pytest.fixture
    def extractor(self):
        # Use a smaller model for testing or mock
        return MedicalEntityExtractor(
            models=["dmis-lab/biobert-base-cased-v1.2"],
            use_crf=False,  # Disable CRF for testing
            calibration_temperature=1.5
        )
    
    def test_extract_entities(self, extractor):
        text = """
        The patient is a 65-year-old male with a history of diabetes mellitus type 2 
        and hypertension. He denies chest pain but reports shortness of breath. 
        Current medications include metformin 500mg twice daily and lisinopril 10mg daily.
        Lab results show glucose level of 180 mg/dL. Possible pneumonia on chest x-ray.
        """
        
        entities = extractor.extract_entities(text)
        
        # Check that entities were extracted
        assert len(entities) > 0
        
        # Check for different entity types
        entity_types = {entity.type for entity in entities}
        assert EntityType.CONDITION in entity_types
        assert EntityType.DRUG in entity_types
        
        # Check for negation
        negated_entities = [e for e in entities if e.negated]
        assert any("chest pain" in e.text.lower() for e in negated_entities)
        
        # Check for uncertainty
        uncertain_entities = [e for e in entities if e.uncertain]
        assert any("pneumonia" in e.text.lower() for e in uncertain_entities)
    
    def test_dosage_frequency_extraction(self, extractor):
        text = "Take metformin 500mg twice daily and aspirin 81mg once daily as needed."
        
        entities = extractor.extract_entities(text)
        
        # Check for dosage entities
        dosage_entities = [e for e in entities if e.type == EntityType.DOSAGE]
        assert len(dosage_entities) >= 2
        assert any("500mg" in e.text for e in dosage_entities)
        assert any("81mg" in e.text for e in dosage_entities)
        
        # Check for frequency entities
        frequency_entities = [e for e in entities if e.type == EntityType.FREQUENCY]
        assert len(frequency_entities) >= 2
        assert any("twice daily" in e.text for e in frequency_entities)
        assert any("once daily" in e.text for e in frequency_entities)
    
    def test_anatomy_extraction(self, extractor):
        text = "The patient has pain in the left knee and swelling of the right ankle."
        
        entities = extractor.extract_entities(text)
        
        # Check for anatomy entities
        anatomy_entities = [e for e in entities if e.type == EntityType.ANATOMY]
        assert len(anatomy_entities) >= 2
        assert any("knee" in e.text for e in anatomy_entities)
        assert any("ankle" in e.text for e in anatomy_entities)
    
    def test_entity_linking(self, extractor):
        text = "Patient diagnosed with diabetes and prescribed metformin."
        
        entities = extractor.extract_entities(text)
        
        # Check that some entities have linked IDs
        linked_entities = [e for e in entities if e.linked_id is not None]
        assert len(linked_entities) > 0
    
    def test_hierarchical_recognition(self, extractor):
        text = "Patient has type 2 diabetes."
        
        entities = extractor.extract_entities(text)
        
        # Check for hierarchical information
        hierarchical_entities = [e for e in entities if e.hierarchy is not None]
        assert len(hierarchical_entities) > 0
    
    def test_sliding_window(self, extractor):
        # Create a long text
        long_text = " ".join([
            "The patient has diabetes." for _ in range(100)
        ])
        
        entities = extractor.extract_with_sliding_window(long_text, window_size=512, overlap=50)
        
        # Should extract multiple instances
        assert len(entities) > 0
        
        # Check that entities from different windows are merged
        diabetes_entities = [e for e in entities if "diabetes" in e.text.lower()]
        assert len(diabetes_entities) > 0


@pytest.mark.integration
class TestBioBERTServiceIntegration:
    """Test integration with BioBERT service"""
    
    def test_biobert_service_with_advanced_extractor(self):
        from app.ml.biobert.biobert_service import BioBERTService
        
        service = BioBERTService(
            use_advanced_extractor=True,
            use_regex_patterns=False,
            use_ensemble=False
        )
        
        text = """
        Patient presents with severe headache and fever. No evidence of meningitis.
        Started on acetaminophen 650mg every 6 hours for fever control.
        """
        
        entities = service.extract_entities(text)
        
        # Check that advanced features are working
        assert len(entities) > 0
        
        # Check for negated conditions
        negated = [e for e in entities if e.attributes and e.attributes.get("negated")]
        assert any("meningitis" in e.text.lower() for e in negated)
        
        # Check for dosage information
        assert any(e.entity_type == "DOSAGE" for e in entities)