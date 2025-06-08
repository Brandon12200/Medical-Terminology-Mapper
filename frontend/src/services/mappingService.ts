import { api } from './api';
import type { 
  MappingRequest, 
  MappingResponse, 
  BatchJobRequest, 
  BatchJobStatus,
  SystemInfo 
} from '../types';

export interface AIExtractionRequest {
  text: string;
  systems?: string[];
  fuzzy_threshold?: number;
  include_context?: boolean;
}

export interface ExtractedTerm {
  text: string;
  entity_type: string;
  confidence: number;
  start: number;
  end: number;
}

export interface AIExtractionResponse {
  ai_enabled: boolean;
  extracted_terms: ExtractedTerm[];
  mapped_terms: Record<string, any>;
  extraction_method: string;
}

export interface AIStatus {
  ai_enabled: boolean;
  model: string | null;
  capabilities: string[];
  status: string;
}

export interface TestFile {
  filename: string;
  name: string;
  description: string;
  size: number;
  size_category: string;
}

export const mappingService = {
  // Map a single term
  mapTerm: async (request: MappingRequest): Promise<MappingResponse> => {
    const { data } = await api.post<any>('/map', request);
    
    // Transform backend response to match frontend expectations
    // Backend returns: { term, results: { system: [...] }, ... }
    // Frontend expects: { term, mappings: [...] }
    if (data.results && typeof data.results === 'object') {
      const mappings: any[] = [];
      
      // Flatten the results dictionary into a single array
      Object.entries(data.results).forEach(([system, systemMappings]) => {
        if (Array.isArray(systemMappings)) {
          mappings.push(...systemMappings);
        }
      });
      
      return {
        term: data.term,
        mappings: mappings
      };
    }
    
    // If the response is already in the expected format, return as-is
    return data;
  },

  // Get available systems
  getSystems: async (): Promise<SystemInfo[]> => {
    const { data } = await api.get<SystemInfo[]>('/systems');
    return data;
  },

  // Process batch
  processBatch: async (request: BatchJobRequest): Promise<{ job_id: string }> => {
    const { data } = await api.post<{ job_id: string }>('/batch', request);
    return data;
  },

  // Get batch job status
  getBatchStatus: async (jobId: string): Promise<BatchJobStatus> => {
    const { data } = await api.get<BatchJobStatus>(`/batch/status/${jobId}`);
    return data;
  },

  // Get batch results
  getBatchResults: async (jobId: string): Promise<MappingResponse[]> => {
    const { data } = await api.get<any[]>(`/batch/result/${jobId}`);
    
    // Transform each result if needed
    return data.map(item => {
      if (item.results && typeof item.results === 'object') {
        const mappings: any[] = [];
        
        // Flatten the results dictionary into a single array
        Object.entries(item.results).forEach(([system, systemMappings]) => {
          if (Array.isArray(systemMappings)) {
            mappings.push(...systemMappings);
          }
        });
        
        return {
          term: item.term,
          mappings: mappings
        };
      }
      
      // If already in expected format, return as-is
      return item;
    });
  },

  // Upload file for batch processing
  uploadFile: async (file: File): Promise<{ job_id: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const { data } = await api.post<{ job_id: string }>('/batch/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

  // AI-powered features
  getAIStatus: async (): Promise<AIStatus> => {
    const { data } = await api.get<AIStatus>('/ai/status');
    return data;
  },

  extractAndMapTerms: async (request: AIExtractionRequest): Promise<AIExtractionResponse> => {
    const { data } = await api.post<AIExtractionResponse>('/ai/extract', request);
    return data;
  },

  extractTermsOnly: async (text: string): Promise<{ ai_enabled: boolean; extracted_terms: ExtractedTerm[]; extraction_method: string }> => {
    const { data } = await api.post('/ai/extract-only', { text });
    return data;
  },

  // Test files
  getTestFiles: async (): Promise<TestFile[]> => {
    const { data } = await api.get<TestFile[]>('/test-files');
    return data;
  },

  downloadTestFile: async (filename: string): Promise<Blob> => {
    const { data } = await api.get(`/test-files/${filename}`, {
      responseType: 'blob',
    });
    return data;
  },
};