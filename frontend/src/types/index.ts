export interface MappingRequest {
  term: string;
  systems: ('snomed' | 'loinc' | 'rxnorm' | 'all')[];
  context?: string;
  fuzzy_threshold?: number;
}

export interface MappingResult {
  system: string;
  code: string;
  display: string;
  confidence: number;
  match_type?: string;
}

export interface MappingResponse {
  term: string;
  mappings: MappingResult[];
}

export interface BatchJobRequest {
  terms: string[];
  system: string;
  context?: string;
}

export interface BatchJobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_terms: number;
  processed_terms: number;
  created_at: string;
  completed_at?: string;
}

export interface SystemInfo {
  name: string;
  display_name: string;
  description: string;
  total_concepts: number;
}

export interface AIExtractionRequest {
  text: string;
  system?: 'snomed' | 'loinc' | 'rxnorm' | 'all';
  map_terms?: boolean;
}

export interface ExtractedTerm {
  term: string;
  category: string;
  confidence: number;
  mappings?: MappingResult[];
}