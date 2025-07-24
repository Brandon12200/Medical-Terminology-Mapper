"""
BioBERT integration for medical entity recognition

This module provides BioBERT-based medical entity extraction capabilities
including model management, entity extraction, and terminology mapping integration.
"""

from app.ml.biobert.model_manager import (
    BioBERTModelManager,
    get_biobert_manager,
    EntityPrediction,
    BatchResult
)

from app.ml.biobert.biobert_service import (
    BioBERTService,
    create_biobert_service,
    MedicalEntity,
    DocumentAnalysis
)

__all__ = [
    "BioBERTModelManager",
    "get_biobert_manager",
    "EntityPrediction",
    "BatchResult",
    "BioBERTService", 
    "create_biobert_service",
    "MedicalEntity",
    "DocumentAnalysis"
]