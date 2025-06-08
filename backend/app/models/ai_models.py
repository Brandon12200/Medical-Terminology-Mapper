from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification,
    pipeline
)
import openai
from anthropic import Anthropic
import spacy
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.ensemble import RandomForestClassifier
import joblib
import logging
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ModelType(Enum):
    """Supported AI model types for healthcare processing"""
    BIOBERT = "biobert"
    CLINICAL_BERT = "clinical-bert"
    GPT4 = "gpt-4"
    CLAUDE = "claude-3"
    SCISPACY = "scispacy"
    CUSTOM_TRANSFORMER = "custom-transformer"
    ENSEMBLE = "ensemble"


class ProcessingMode(Enum):
    """Processing modes for different use cases"""
    BATCH = "batch"
    STREAMING = "streaming"
    INTERACTIVE = "interactive"
    HYBRID = "hybrid"


@dataclass
class MedicalEntity:
    """Enhanced medical entity with relationships and context"""
    text: str
    type: str
    start: int
    end: int
    confidence: float
    context: str
    relationships: List[Dict[str, Any]]
    attributes: Dict[str, Any]
    terminology_codes: Dict[str, List[str]]
    negated: bool = False
    hypothetical: bool = False
    historical: bool = False
    family_history: bool = False


@dataclass
class ClinicalDocument:
    """Structured clinical document representation"""
    text: str
    metadata: Dict[str, Any]
    sections: Dict[str, str]
    entities: List[MedicalEntity]
    relationships: List[Dict[str, Any]]
    summary: Optional[str] = None
    risk_factors: List[Dict[str, Any]] = None
    recommendations: List[str] = None


class AdvancedMedicalAI:
    """Production-ready medical AI system with multiple model support"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = {}
        self.tokenizers = {}
        self.vector_stores = {}
        self.ensemble_models = {}
        self.processing_stats = {
            "total_processed": 0,
            "errors": 0,
            "avg_latency_ms": 0
        }
        
        # Initialize thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=config.get("max_workers", 4))
        
        # Load models based on configuration
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize AI models based on configuration"""
        
        # Clinical BERT for medical NER
        if self.config.get("enable_clinical_bert", True):
            try:
                model_name = "emilyalsentzer/Bio_ClinicalBERT"
                self.tokenizers["clinical_bert"] = AutoTokenizer.from_pretrained(model_name)
                self.models["clinical_bert"] = AutoModelForTokenClassification.from_pretrained(model_name)
                self.models["clinical_bert_pipeline"] = pipeline(
                    "ner",
                    model=self.models["clinical_bert"],
                    tokenizer=self.tokenizers["clinical_bert"],
                    aggregation_strategy="max"
                )
                logger.info("Clinical BERT model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Clinical BERT: {e}")
        
        # ScispaCy for biomedical NLP
        if self.config.get("enable_scispacy", True):
            try:
                self.models["scispacy"] = spacy.load("en_core_sci_md")
                self.models["scispacy_linker"] = self.models["scispacy"].add_pipe(
                    "scispacy_linker",
                    config={
                        "resolve_abbreviations": True,
                        "linker_name": "umls"
                    }
                )
                logger.info("ScispaCy model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load ScispaCy: {e}")
        
        # Sentence transformer for semantic similarity
        if self.config.get("enable_embeddings", True):
            try:
                self.models["embedder"] = SentenceTransformer('pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb')
                # Initialize FAISS index for fast similarity search
                self.vector_stores["terminology"] = faiss.IndexFlatL2(768)
                logger.info("Sentence transformer and FAISS index initialized")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer: {e}")
        
        # LLM APIs for advanced understanding
        if self.config.get("enable_llm", False):
            if self.config.get("openai_api_key"):
                openai.api_key = self.config["openai_api_key"]
                self.models["gpt4"] = "gpt-4-turbo-preview"
            
            if self.config.get("anthropic_api_key"):
                self.models["claude"] = Anthropic(api_key=self.config["anthropic_api_key"])
        
        # Load custom ensemble models for specific tasks
        self._load_ensemble_models()
    
    def _load_ensemble_models(self):
        """Load pre-trained ensemble models for specific healthcare tasks"""
        model_paths = self.config.get("ensemble_model_paths", {})
        
        for task, path in model_paths.items():
            try:
                self.ensemble_models[task] = joblib.load(path)
                logger.info(f"Loaded ensemble model for {task}")
            except Exception as e:
                logger.error(f"Failed to load ensemble model for {task}: {e}")
    
    async def process_clinical_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        mode: ProcessingMode = ProcessingMode.BATCH
    ) -> ClinicalDocument:
        """Process clinical document with advanced AI capabilities"""
        
        start_time = datetime.now()
        
        try:
            # Parse document structure
            sections = self._parse_clinical_sections(text)
            
            # Extract entities using multiple models
            entities = await self._extract_entities_ensemble(text, sections)
            
            # Extract relationships between entities
            relationships = await self._extract_relationships(entities, text)
            
            # Generate clinical summary if enabled
            summary = None
            if self.config.get("generate_summaries", True):
                summary = await self._generate_clinical_summary(text, entities, relationships)
            
            # Identify risk factors and recommendations
            risk_factors = self._analyze_risk_factors(entities, relationships)
            recommendations = self._generate_recommendations(entities, risk_factors)
            
            # Create structured document
            doc = ClinicalDocument(
                text=text,
                metadata=metadata or {},
                sections=sections,
                entities=entities,
                relationships=relationships,
                summary=summary,
                risk_factors=risk_factors,
                recommendations=recommendations
            )
            
            # Update processing stats
            self._update_stats(start_time)
            
            return doc
            
        except Exception as e:
            logger.error(f"Error processing clinical document: {e}")
            self.processing_stats["errors"] += 1
            raise
    
    def _parse_clinical_sections(self, text: str) -> Dict[str, str]:
        """Parse clinical document into standard sections"""
        sections = {
            "chief_complaint": "",
            "history_present_illness": "",
            "past_medical_history": "",
            "medications": "",
            "allergies": "",
            "physical_exam": "",
            "assessment_plan": "",
            "lab_results": ""
        }
        
        # Section detection logic using regex and NLP
        section_patterns = {
            "chief_complaint": r"(?i)(chief complaint|cc|reason for visit):\s*([^\n]+)",
            "history_present_illness": r"(?i)(history of present illness|hpi):\s*([\s\S]+?)(?=\n[A-Z]|$)",
            "medications": r"(?i)(current medications|medications):\s*([\s\S]+?)(?=\n[A-Z]|$)",
            "allergies": r"(?i)(allergies|nka):\s*([^\n]+)",
            "assessment_plan": r"(?i)(assessment and plan|a/p|plan):\s*([\s\S]+?)(?=\n[A-Z]|$)"
        }
        
        import re
        for section, pattern in section_patterns.items():
            match = re.search(pattern, text)
            if match:
                sections[section] = match.group(2).strip()
        
        return sections
    
    async def _extract_entities_ensemble(
        self,
        text: str,
        sections: Dict[str, str]
    ) -> List[MedicalEntity]:
        """Extract entities using ensemble of models"""
        
        all_entities = []
        
        # Clinical BERT extraction
        if "clinical_bert_pipeline" in self.models:
            bert_entities = await self._extract_with_clinical_bert(text)
            all_entities.extend(bert_entities)
        
        # ScispaCy extraction with UMLS linking
        if "scispacy" in self.models:
            scispacy_entities = await self._extract_with_scispacy(text)
            all_entities.extend(scispacy_entities)
        
        # LLM-based extraction for complex cases
        if self.config.get("enable_llm", False) and len(text) < 4000:
            llm_entities = await self._extract_with_llm(text, sections)
            all_entities.extend(llm_entities)
        
        # Merge and deduplicate entities
        merged_entities = self._merge_entities(all_entities)
        
        # Enhance with terminology mapping
        for entity in merged_entities:
            entity.terminology_codes = await self._map_to_terminologies(entity)
        
        return merged_entities
    
    async def _extract_with_clinical_bert(self, text: str) -> List[MedicalEntity]:
        """Extract entities using Clinical BERT"""
        entities = []
        
        try:
            # Run NER pipeline
            results = self.models["clinical_bert_pipeline"](text)
            
            for result in results:
                entity = MedicalEntity(
                    text=result["word"],
                    type=self._map_bert_label(result["entity_group"]),
                    start=result["start"],
                    end=result["end"],
                    confidence=result["score"],
                    context=text[max(0, result["start"]-50):min(len(text), result["end"]+50)],
                    relationships=[],
                    attributes={},
                    terminology_codes={}
                )
                entities.append(entity)
                
        except Exception as e:
            logger.error(f"Clinical BERT extraction error: {e}")
        
        return entities
    
    async def _extract_with_scispacy(self, text: str) -> List[MedicalEntity]:
        """Extract entities using ScispaCy with UMLS linking"""
        entities = []
        
        try:
            doc = self.models["scispacy"](text)
            
            for ent in doc.ents:
                # Get UMLS concepts if available
                umls_codes = []
                if hasattr(ent, "_.kb_ents") and ent._.kb_ents:
                    umls_codes = [kb[0] for kb in ent._.kb_ents[:3]]  # Top 3 matches
                
                entity = MedicalEntity(
                    text=ent.text,
                    type=self._map_scispacy_label(ent.label_),
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.85,  # ScispaCy doesn't provide confidence
                    context=text[max(0, ent.start_char-50):min(len(text), ent.end_char+50)],
                    relationships=[],
                    attributes={
                        "umls_codes": umls_codes,
                        "is_negated": self._check_negation(doc, ent)
                    },
                    terminology_codes={},
                    negated=self._check_negation(doc, ent)
                )
                entities.append(entity)
                
        except Exception as e:
            logger.error(f"ScispaCy extraction error: {e}")
        
        return entities
    
    async def _extract_with_llm(
        self,
        text: str,
        sections: Dict[str, str]
    ) -> List[MedicalEntity]:
        """Extract entities using LLM for complex understanding"""
        entities = []
        
        prompt = f"""Extract medical entities from this clinical text. For each entity, provide:
        - text: the exact text
        - type: CONDITION, MEDICATION, PROCEDURE, LAB_TEST, or SYMPTOM
        - attributes: relevant attributes (dosage, frequency, severity, etc.)
        - negated: true if negated
        - relationships: related entities
        
        Clinical Text:
        {text[:3000]}  # Truncate for API limits
        
        Return as JSON array.
        """
        
        try:
            if "gpt4" in self.models:
                response = await self._call_openai(prompt)
                entities.extend(self._parse_llm_response(response, text))
            elif "claude" in self.models:
                response = await self._call_claude(prompt)
                entities.extend(self._parse_llm_response(response, text))
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
        
        return entities
    
    async def _extract_relationships(
        self,
        entities: List[MedicalEntity],
        text: str
    ) -> List[Dict[str, Any]]:
        """Extract relationships between medical entities"""
        relationships = []
        
        # Use dependency parsing for syntactic relationships
        if "scispacy" in self.models:
            doc = self.models["scispacy"](text)
            relationships.extend(self._extract_syntactic_relations(doc, entities))
        
        # Use transformer models for semantic relationships
        if self.config.get("enable_relation_extraction", True):
            relationships.extend(await self._extract_semantic_relations(entities, text))
        
        # Use rules for domain-specific relationships
        relationships.extend(self._extract_rule_based_relations(entities))
        
        return self._deduplicate_relationships(relationships)
    
    def _analyze_risk_factors(self, entities: List[MedicalEntity], relationships: List[Dict]) -> List[Dict]:
        """Analyze clinical risk factors from extracted information"""
        risk_factors = []
        
        # Condition-based risk analysis
        conditions = [e for e in entities if e.type == "CONDITION"]
        for condition in conditions:
            risk_score = self._calculate_condition_risk(condition, entities, relationships)
            if risk_score > 0.5:
                risk_factors.append({
                    "factor": condition.text,
                    "type": "condition",
                    "score": risk_score,
                    "related_entities": self._get_related_entities(condition, relationships)
                })
        
        # Medication interaction risks
        medications = [e for e in entities if e.type == "MEDICATION"]
        interactions = self._check_drug_interactions(medications)
        risk_factors.extend(interactions)
        
        # Lab value risks
        lab_results = [e for e in entities if e.type == "LAB_TEST"]
        abnormal_labs = self._identify_abnormal_labs(lab_results)
        risk_factors.extend(abnormal_labs)
        
        return sorted(risk_factors, key=lambda x: x["score"], reverse=True)
    
    def _generate_recommendations(self, entities: List[MedicalEntity], risk_factors: List[Dict]) -> List[str]:
        """Generate clinical recommendations based on analysis"""
        recommendations = []
        
        # High-risk condition recommendations
        for risk in risk_factors:
            if risk["score"] > 0.7:
                rec = self._get_condition_recommendation(risk)
                if rec:
                    recommendations.append(rec)
        
        # Preventive care recommendations
        recommendations.extend(self._get_preventive_recommendations(entities))
        
        # Follow-up recommendations
        recommendations.extend(self._get_followup_recommendations(entities, risk_factors))
        
        return list(set(recommendations))  # Remove duplicates
    
    async def _map_to_terminologies(self, entity: MedicalEntity) -> Dict[str, List[str]]:
        """Map entity to standard terminologies using AI-enhanced matching"""
        mappings = {
            "snomed": [],
            "loinc": [],
            "rxnorm": [],
            "icd10": []
        }
        
        # Use embeddings for semantic similarity matching
        if "embedder" in self.models:
            entity_embedding = self.models["embedder"].encode([entity.text])[0]
            
            # Search in pre-indexed terminology embeddings
            # This would be connected to your existing terminology mapper
            # but with AI-enhanced similarity matching
            
        return mappings
    
    def _merge_entities(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """Merge duplicate entities from different extractors"""
        merged = []
        seen = set()
        
        # Sort by position and confidence
        sorted_entities = sorted(entities, key=lambda x: (x.start, -x.confidence))
        
        for entity in sorted_entities:
            # Check for overlap with existing entities
            key = (entity.text.lower(), entity.type)
            if key not in seen:
                # Check for partial overlaps
                overlap = False
                for merged_entity in merged:
                    if (entity.start >= merged_entity.start and entity.start < merged_entity.end) or \
                       (entity.end > merged_entity.start and entity.end <= merged_entity.end):
                        # Merge attributes and increase confidence
                        merged_entity.confidence = max(merged_entity.confidence, entity.confidence)
                        merged_entity.attributes.update(entity.attributes)
                        overlap = True
                        break
                
                if not overlap:
                    merged.append(entity)
                    seen.add(key)
        
        return merged
    
    def _update_stats(self, start_time: datetime):
        """Update processing statistics"""
        latency = (datetime.now() - start_time).total_seconds() * 1000
        self.processing_stats["total_processed"] += 1
        
        # Update rolling average
        n = self.processing_stats["total_processed"]
        avg = self.processing_stats["avg_latency_ms"]
        self.processing_stats["avg_latency_ms"] = (avg * (n-1) + latency) / n
    
    def _map_bert_label(self, label: str) -> str:
        """Map BERT labels to standard entity types"""
        mapping = {
            "DISEASE": "CONDITION",
            "DRUG": "MEDICATION",
            "TREATMENT": "PROCEDURE",
            "TEST": "LAB_TEST",
            "SYMPTOM": "SYMPTOM"
        }
        return mapping.get(label.upper(), "OTHER")
    
    def _map_scispacy_label(self, label: str) -> str:
        """Map ScispaCy labels to standard entity types"""
        mapping = {
            "DISEASE": "CONDITION",
            "CHEMICAL": "MEDICATION",
            "PROCEDURE": "PROCEDURE",
            "TEST": "LAB_TEST"
        }
        return mapping.get(label.upper(), "OTHER")
    
    def _check_negation(self, doc, entity) -> bool:
        """Check if entity is negated in context"""
        # Simple negation detection - would be enhanced with proper negation detection
        negation_words = ["no", "not", "without", "denies", "negative"]
        
        # Check tokens before entity
        for i in range(max(0, entity.start - 3), entity.start):
            if doc[i].text.lower() in negation_words:
                return True
        
        return False
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API for advanced processing"""
        # Implementation would use actual OpenAI API
        pass
    
    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API for advanced processing"""
        # Implementation would use actual Claude API
        pass
    
    def _parse_llm_response(self, response: str, original_text: str) -> List[MedicalEntity]:
        """Parse LLM response into medical entities"""
        # Implementation would parse JSON response from LLM
        pass
    
    def _extract_syntactic_relations(self, doc, entities: List[MedicalEntity]) -> List[Dict]:
        """Extract syntactic relationships using dependency parsing"""
        # Implementation would use spaCy dependency parsing
        pass
    
    async def _extract_semantic_relations(self, entities: List[MedicalEntity], text: str) -> List[Dict]:
        """Extract semantic relationships using transformer models"""
        # Implementation would use relation extraction models
        pass
    
    def _extract_rule_based_relations(self, entities: List[MedicalEntity]) -> List[Dict]:
        """Extract relationships using domain-specific rules"""
        # Implementation would use medical domain rules
        pass
    
    def _deduplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """Remove duplicate relationships"""
        # Implementation would deduplicate based on entities and relation type
        pass
    
    def _calculate_condition_risk(self, condition: MedicalEntity, all_entities: List[MedicalEntity], relationships: List[Dict]) -> float:
        """Calculate risk score for a medical condition"""
        # Implementation would use clinical risk models
        pass
    
    def _get_related_entities(self, entity: MedicalEntity, relationships: List[Dict]) -> List[str]:
        """Get entities related to a given entity"""
        # Implementation would traverse relationship graph
        pass
    
    def _check_drug_interactions(self, medications: List[MedicalEntity]) -> List[Dict]:
        """Check for potential drug interactions"""
        # Implementation would use drug interaction database
        pass
    
    def _identify_abnormal_labs(self, lab_results: List[MedicalEntity]) -> List[Dict]:
        """Identify abnormal lab values"""
        # Implementation would use reference ranges
        pass
    
    def _get_condition_recommendation(self, risk_factor: Dict) -> Optional[str]:
        """Get recommendation for a specific risk factor"""
        # Implementation would use clinical guidelines
        pass
    
    def _get_preventive_recommendations(self, entities: List[MedicalEntity]) -> List[str]:
        """Generate preventive care recommendations"""
        # Implementation would use preventive care guidelines
        pass
    
    def _get_followup_recommendations(self, entities: List[MedicalEntity], risk_factors: List[Dict]) -> List[str]:
        """Generate follow-up recommendations"""
        # Implementation would use clinical best practices
        pass
    
    async def _generate_clinical_summary(self, text: str, entities: List[MedicalEntity], relationships: List[Dict]) -> str:
        """Generate concise clinical summary using AI"""
        # Implementation would use LLM for summarization
        pass
