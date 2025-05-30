import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { mappingService } from '../services/mappingService';
import { AIExtractionRequest, ExtractedTerm } from '../types';
import { ConfidenceBar } from '../components/common/ConfidenceBar';

const AIExtraction: React.FC = () => {
  const [clinicalText, setClinicalText] = useState('');
  const [selectedSystem, setSelectedSystem] = useState<'snomed' | 'loinc' | 'rxnorm' | 'all'>('all');
  const [extractedTerms, setExtractedTerms] = useState<ExtractedTerm[]>([]);

  // Query AI status
  const { data: aiStatus } = useQuery({
    queryKey: ['ai-status'],
    queryFn: mappingService.getAIStatus,
    refetchInterval: 5000, // Check every 5 seconds
  });

  // Extract and map mutation
  const extractAndMapMutation = useMutation({
    mutationFn: (request: AIExtractionRequest) => mappingService.extractAndMapTerms(request),
    onSuccess: (data) => {
      setExtractedTerms(data.extracted_terms);
    },
  });

  // Extract only mutation
  const extractOnlyMutation = useMutation({
    mutationFn: (text: string) => mappingService.extractTermsOnly({ text }),
    onSuccess: (data) => {
      setExtractedTerms(data.extracted_terms.map(term => ({
        ...term,
        mappings: []
      })));
    },
  });

  const handleExtractAndMap = () => {
    if (!clinicalText.trim()) return;
    
    extractAndMapMutation.mutate({
      text: clinicalText,
      terminology_system: selectedSystem,
    });
  };

  const handleExtractOnly = () => {
    if (!clinicalText.trim()) return;
    extractOnlyMutation.mutate(clinicalText);
  };

  const isLoading = extractAndMapMutation.isPending || extractOnlyMutation.isPending;

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">AI-Powered Term Extraction</h1>
        <p className="text-gray-600">
          Extract medical terms from clinical text using BioBERT and map them to standardized terminologies.
        </p>
        
        {/* AI Status Indicator */}
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${aiStatus?.ai_enabled ? 'bg-green-500' : 'bg-yellow-500'}`} />
            <span className="text-sm font-medium">
              AI Status: {aiStatus?.ai_enabled ? 'Enabled' : 'Using Fallback Pattern Matching'}
            </span>
          </div>
          {aiStatus?.model_info && (
            <div className="mt-2 text-xs text-gray-600">
              Model: {aiStatus.model_info.model_name} | 
              Version: {aiStatus.model_info.version}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Clinical Text Input</h2>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Paste or type clinical text:
            </label>
            <textarea
              value={clinicalText}
              onChange={(e) => setClinicalText(e.target.value)}
              placeholder="Example: Patient presents with type 2 diabetes mellitus and hypertension. Recent HbA1c test shows 7.5%. Prescribed metformin 500mg twice daily."
              className="w-full h-48 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Terminology System:
            </label>
            <select
              value={selectedSystem}
              onChange={(e) => setSelectedSystem(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Systems</option>
              <option value="snomed">SNOMED CT</option>
              <option value="loinc">LOINC</option>
              <option value="rxnorm">RxNorm</option>
            </select>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleExtractAndMap}
              disabled={!clinicalText.trim() || isLoading}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Processing...' : 'Extract & Map Terms'}
            </button>
            <button
              onClick={handleExtractOnly}
              disabled={!clinicalText.trim() || isLoading}
              className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Processing...' : 'Extract Only'}
            </button>
          </div>

          {/* Sample Text Buttons */}
          <div className="mt-4">
            <p className="text-sm text-gray-600 mb-2">Try sample text:</p>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setClinicalText("Patient diagnosed with type 2 diabetes mellitus. HbA1c level is 8.2%. Started on metformin 500mg twice daily.")}
                className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-md"
              >
                Diabetes Sample
              </button>
              <button
                onClick={() => setClinicalText("Blood pressure 145/90 mmHg. Patient has essential hypertension. Prescribed lisinopril 10mg daily.")}
                className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-md"
              >
                Hypertension Sample
              </button>
              <button
                onClick={() => setClinicalText("CBC shows WBC 12.5, Hgb 14.2, Platelets 250K. Urinalysis negative for protein and glucose.")}
                className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-md"
              >
                Lab Results Sample
              </button>
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Extracted Terms</h2>
          
          {extractedTerms.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No terms extracted yet.</p>
              <p className="text-sm mt-2">Enter clinical text and click extract to see results.</p>
            </div>
          ) : (
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {extractedTerms.map((term, index) => (
                <div key={index} className="border-b border-gray-200 pb-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-medium text-gray-900">{term.text}</h3>
                      <div className="flex items-center space-x-3 text-sm text-gray-600 mt-1">
                        <span>Type: {term.entity_type}</span>
                        {term.start_char !== undefined && (
                          <span>Position: {term.start_char}-{term.end_char}</span>
                        )}
                      </div>
                    </div>
                    {term.confidence && (
                      <div className="text-sm text-gray-600">
                        Confidence: {(term.confidence * 100).toFixed(1)}%
                      </div>
                    )}
                  </div>
                  
                  {term.mappings && term.mappings.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <p className="text-sm font-medium text-gray-700">Mappings:</p>
                      {term.mappings.map((mapping, mapIndex) => (
                        <div key={mapIndex} className="bg-gray-50 p-3 rounded-md">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-sm font-medium">{mapping.display}</p>
                              <p className="text-xs text-gray-600 mt-1">
                                {mapping.system.toUpperCase()}: {mapping.code}
                              </p>
                            </div>
                            <div className="ml-4">
                              <ConfidenceBar confidence={mapping.confidence} />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Export Options */}
          {extractedTerms.length > 0 && (
            <div className="mt-6 pt-4 border-t border-gray-200">
              <button className="text-sm text-blue-600 hover:text-blue-700">
                Export Results as JSON
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Error Display */}
      {(extractAndMapMutation.isError || extractOnlyMutation.isError) && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-700">
            Error: {(extractAndMapMutation.error || extractOnlyMutation.error)?.message || 'An error occurred'}
          </p>
        </div>
      )}
    </div>
  );
};

export default AIExtraction;