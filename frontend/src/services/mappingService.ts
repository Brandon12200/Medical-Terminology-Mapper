import { api } from './api';
import type { 
  MappingRequest, 
  MappingResponse, 
  BatchJobRequest, 
  BatchJobStatus,
  SystemInfo 
} from '../types';


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
    const { data } = await api.get<{ systems: SystemInfo[] }>('/systems');
    return data.systems || [];
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
    const { data } = await api.get<any>(`/batch/result/${jobId}`);
    
    // Backend returns BatchJobResult object with results array
    const resultsArray = data.results || [];
    
    // Transform each result to match frontend interface
    return resultsArray.map((item: any) => {
      const mappings: any[] = [];
      
      // Handle both possible field names (item.mappings or item.results)
      const mappingData = item.mappings || item.results || {};
      
      if (mappingData && typeof mappingData === 'object') {
        // Flatten the mappings dictionary into a single array
        Object.entries(mappingData).forEach(([system, systemMappings]) => {
          if (Array.isArray(systemMappings)) {
            mappings.push(...systemMappings);
          }
        });
      }
      
      return {
        term: item.original_term || item.term, // Handle both field names
        mappings: mappings
      };
    });
  },

  // Upload file for batch processing
  uploadFile: async (file: File): Promise<{ job_id: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_format', 'csv'); // Add required file_format parameter
    formData.append('column_name', 'term'); // Specify the column containing terms
    // Don't send systems parameter - backend has default value of ["all"]
    
    const { data } = await api.post<{ job_id: string }>('/batch/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

};