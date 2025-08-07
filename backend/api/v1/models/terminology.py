from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum

class TerminologySystem(str, Enum):
    SNOMED = "snomed"
    LOINC = "loinc"
    RXNORM = "rxnorm"
    ICD10 = "icd10"
    ALL = "all"

class FuzzyAlgorithm(str, Enum):
    PHONETIC = "phonetic"
    TOKEN_SET_RATIO = "token_set_ratio"
    TOKEN_SORT_RATIO = "token_sort_ratio"
    LEVENSHTEIN = "levenshtein"
    JARO_WINKLER = "jaro_winkler"
    ALL = "all"

class TermMapping(BaseModel):
    code: str
    display: str
    system: str
    confidence: float = Field(ge=0.0, le=1.0)
    match_type: str
    fuzzy_algorithm: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "73211009",
                "display": "Diabetes mellitus",
                "system": "snomed",
                "confidence": 0.95,
                "match_type": "fuzzy",
                "fuzzy_algorithm": "token_sort_ratio"
            }
        }
    )

class MappingRequest(BaseModel):
    term: str = Field(..., min_length=1, description="Medical term to map")
    systems: Optional[List[TerminologySystem]] = Field(
        default=[TerminologySystem.ALL],
        description="Terminology systems to search"
    )
    context: Optional[str] = Field(
        default=None,
        description="Clinical context for better matching"
    )
    fuzzy_threshold: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for fuzzy matches"
    )
    fuzzy_algorithms: Optional[List[FuzzyAlgorithm]] = Field(
        default=[FuzzyAlgorithm.ALL],
        description="Fuzzy matching algorithms to use"
    )
    max_results: Optional[int] = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results per system"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "term": "diabetes type 2",
                "systems": ["snomed", "icd10"],
                "context": "diagnosis",
                "fuzzy_threshold": 0.8,
                "fuzzy_algorithms": ["token_sort_ratio", "phonetic"],
                "max_results": 5
            }
        }
    )

class MappingResponse(BaseModel):
    term: str
    results: Dict[str, List[TermMapping]]
    total_matches: int
    processing_time_ms: float
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "term": "diabetes type 2",
                "results": {
                    "snomed": [
                        {
                            "code": "44054006",
                            "display": "Diabetes mellitus type 2",
                            "system": "snomed",
                            "confidence": 0.95,
                            "match_type": "fuzzy",
                            "fuzzy_algorithm": "token_sort_ratio"
                        }
                    ]
                },
                "total_matches": 1,
                "processing_time_ms": 125.5
            }
        }
    )

class BatchMappingRequest(BaseModel):
    terms: List[str] = Field(..., min_length=1, max_length=1000)
    systems: Optional[List[TerminologySystem]] = Field(
        default=[TerminologySystem.ALL]
    )
    context: Optional[str] = None
    fuzzy_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    fuzzy_algorithms: Optional[List[FuzzyAlgorithm]] = Field(
        default=[FuzzyAlgorithm.ALL]
    )
    max_results_per_term: Optional[int] = Field(default=5, ge=1, le=100)

class BatchMappingResponse(BaseModel):
    results: List[MappingResponse]
    total_terms: int
    successful_mappings: int
    failed_mappings: int
    total_processing_time_ms: float

class SystemInfo(BaseModel):
    name: str
    display_name: str
    total_concepts: int
    description: str
    supported: bool

class SystemsResponse(BaseModel):
    systems: List[SystemInfo]
    
class FuzzyAlgorithmInfo(BaseModel):
    name: str
    display_name: str
    description: str
    best_for: List[str]

class FuzzyAlgorithmsResponse(BaseModel):
    algorithms: List[FuzzyAlgorithmInfo]

class ErrorResponse(BaseModel):
    detail: str
    error_type: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Term not found in any system",
                "error_type": "NotFoundError"
            }
        }
    )