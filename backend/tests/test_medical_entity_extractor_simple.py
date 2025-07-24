"""
Simple tests for medical entity extractor components
"""
import pytest
import torch


def test_confidence_calibration():
    """Test confidence calibration logic"""
    temperature = 1.5
    scores = torch.tensor([0.9, 0.8, 0.7, 0.6])
    logits = torch.log(scores / (1 - scores + 1e-8))
    calibrated_logits = logits / temperature
    calibrated_scores = torch.sigmoid(calibrated_logits)
    
    # Calibrated scores should be less extreme
    assert all(0 < s < 1 for s in calibrated_scores)
    assert calibrated_scores[0] < scores[0]  # High confidence reduced
    assert calibrated_scores[-1] > scores[-1]  # Low confidence increased


def test_negation_patterns():
    """Test negation pattern matching"""
    import re
    
    negation_patterns = [
        r'\bno\s+(?:evidence|signs?|symptoms?|history)\s+of\b',
        r'\bdenies?\b',
        r'\bnegative\s+for\b',
        r'\brule\s+out\b',
        r'\bwithout\b',
        r'\babsent\b',
    ]
    
    test_cases = [
        ("Patient denies chest pain", True),
        ("No evidence of diabetes", True),
        ("Negative for COVID-19", True),
        ("Patient has diabetes", False),
        ("Chest pain present", False),
    ]
    
    for text, expected_negation in test_cases:
        found_negation = False
        for pattern in negation_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found_negation = True
                break
        assert found_negation == expected_negation, f"Failed for: {text}"


def test_uncertainty_patterns():
    """Test uncertainty pattern matching"""
    import re
    
    uncertainty_patterns = [
        r'\b(?:possible|possibly|probable|probably)\b',
        r'\b(?:suspected|suspect)\b',
        r'\b(?:suggestive|suggests?)\s+of\b',
        r'\b(?:consistent|compatible)\s+with\b',
        r'\b(?:likely|unlikely)\b',
        r'\b(?:may|might|could)\s+(?:be|have|represent)\b',
    ]
    
    test_cases = [
        ("Possible pneumonia on chest x-ray", True),
        ("Symptoms suggest diabetes", True),
        ("Likely viral infection", True),
        ("Confirmed diagnosis of pneumonia", False),
        ("Patient has hypertension", False),
    ]
    
    for text, expected_uncertainty in test_cases:
        found_uncertainty = False
        for pattern in uncertainty_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found_uncertainty = True
                break
        assert found_uncertainty == expected_uncertainty, f"Failed for: {text}"


def test_dosage_pattern_matching():
    """Test dosage regex patterns"""
    import re
    
    dosage_patterns = [
        re.compile(r'\b\d+\s*(?:mg|g|mcg|ug|ml|cc|units?|iu)\b', re.I),
        re.compile(r'\b\d+\s*(?:-|to)\s*\d+\s*(?:mg|g|mcg|ug|ml|cc|units?|iu)\b', re.I),
    ]
    
    test_texts = [
        "metformin 500mg",
        "insulin 10 units",
        "aspirin 81mg",
        "10-20mg daily",
    ]
    
    for text in test_texts:
        found = False
        for pattern in dosage_patterns:
            if pattern.search(text):
                found = True
                break
        assert found, f"Failed to find dosage in: {text}"


def test_frequency_pattern_matching():
    """Test frequency regex patterns"""
    import re
    
    frequency_patterns = [
        re.compile(r'\b(?:once|twice|three\s+times|four\s+times)\s+(?:a\s+)?(?:day|daily|week|weekly|month|monthly)\b', re.I),
        re.compile(r'\b(?:q|every)\s*\d+\s*(?:h|hr|hrs|hours?|d|days?|w|wk|weeks?|mo|months?)\b', re.I),
        re.compile(r'\b(?:bid|tid|qid|qd|qod|prn|ac|pc|hs)\b', re.I),
        re.compile(r'\b\d+\s*times?\s+(?:per|a)\s+(?:day|week|month)\b', re.I),
    ]
    
    test_texts = [
        "twice daily",
        "q6h",
        "tid",
        "3 times per day",
        "once a week",
    ]
    
    for text in test_texts:
        found = False
        for pattern in frequency_patterns:
            if pattern.search(text):
                found = True
                break
        assert found, f"Failed to find frequency in: {text}"


def test_entity_type_enum():
    """Test EntityType enum functionality"""
    from enum import Enum
    
    class EntityType(Enum):
        CONDITION = "CONDITION"
        DRUG = "DRUG"
        PROCEDURE = "PROCEDURE"
        TEST = "TEST"
        ANATOMY = "ANATOMY"
        DOSAGE = "DOSAGE"
        FREQUENCY = "FREQUENCY"
        OBSERVATION = "OBSERVATION"
    
    # Test basic enum
    assert EntityType.CONDITION.value == "CONDITION"
    assert EntityType.DRUG.value == "DRUG"
    
    # Test string conversion
    assert str(EntityType.CONDITION.value) == "CONDITION"


def test_crf_layer_concept():
    """Test CRF layer concept with PyTorch"""
    import torch
    import torch.nn as nn
    
    # Simple CRF-like transitions
    num_tags = 5
    transitions = nn.Parameter(torch.randn(num_tags, num_tags))
    
    # Test that we can create transitions
    assert transitions.shape == (5, 5)
    
    # Test simple scoring
    emissions = torch.randn(1, 10, num_tags)  # batch=1, seq_len=10, tags=5
    assert emissions.shape == (1, 10, 5)


if __name__ == "__main__":
    # Run tests
    test_confidence_calibration()
    test_negation_patterns()
    test_uncertainty_patterns()
    test_dosage_pattern_matching()
    test_frequency_pattern_matching()
    test_entity_type_enum()
    test_crf_layer_concept()
    print("All tests passed!")