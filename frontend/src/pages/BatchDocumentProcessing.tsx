import React, { useState } from 'react';
import { Layout } from '../components/Layout/Layout';
import { BatchFileUpload } from '../components/BatchProcessor/BatchFileUpload';
import { BatchProgressMonitor } from '../components/BatchProcessor/BatchProgressMonitor';
import { BatchResultsViewer } from '../components/BatchProcessor/BatchResultsViewer';

type ProcessingPhase = 'upload' | 'processing' | 'completed';

export const BatchDocumentProcessing = () => {
  const [currentPhase, setCurrentPhase] = useState<ProcessingPhase>('upload');
  const [batchId, setBatchId] = useState<string | null>(null);

  const handleUploadSuccess = (newBatchId: string) => {
    setBatchId(newBatchId);
    setCurrentPhase('processing');
  };

  const handleProcessingComplete = () => {
    setCurrentPhase('completed');
  };

  const resetToUpload = () => {
    setCurrentPhase('upload');
    setBatchId(null);
  };

  const PhaseIndicator = () => (
    <div className="mb-8">
      <nav aria-label="Progress">
        <ol className="flex items-center">
          {[
            { id: 'upload', name: 'Upload Documents', description: 'Select and upload medical documents' },
            { id: 'processing', name: 'Processing', description: 'Extract entities and map terminology' },
            { id: 'completed', name: 'Results', description: 'View and export results' }
          ].map((step, stepIdx) => (
            <li key={step.id} className={`relative ${stepIdx !== 2 ? 'pr-8 sm:pr-20' : ''}`}>
              <div className="flex items-center">
                <div
                  className={`relative flex h-8 w-8 items-center justify-center rounded-full ${
                    (currentPhase === 'upload' && step.id === 'upload') ||
                    (currentPhase === 'processing' && ['upload', 'processing'].includes(step.id)) ||
                    (currentPhase === 'completed' && ['upload', 'processing', 'completed'].includes(step.id))
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {step.id === 'upload' && (
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                  {step.id === 'processing' && (
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                    </svg>
                  )}
                  {step.id === 'completed' && (
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <div className="ml-4 min-w-0">
                  <p className={`text-sm font-medium ${
                    (currentPhase === 'upload' && step.id === 'upload') ||
                    (currentPhase === 'processing' && ['upload', 'processing'].includes(step.id)) ||
                    (currentPhase === 'completed')
                      ? 'text-blue-600'
                      : 'text-gray-500'
                  }`}>
                    {step.name}
                  </p>
                  <p className="text-sm text-gray-500">{step.description}</p>
                </div>
              </div>
              {stepIdx !== 2 && (
                <div
                  className={`absolute top-4 left-4 -ml-px mt-0.5 h-full w-0.5 ${
                    (currentPhase === 'processing' && step.id === 'upload') ||
                    (currentPhase === 'completed' && ['upload', 'processing'].includes(step.id))
                      ? 'bg-blue-600'
                      : 'bg-gray-300'
                  }`}
                  aria-hidden="true"
                />
              )}
            </li>
          ))}
        </ol>
      </nav>
    </div>
  );

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Batch Document Processing</h1>
          <p className="mt-2 text-gray-600">
            Upload multiple medical documents for automated entity extraction and terminology mapping
          </p>
        </div>

        {/* Phase Indicator */}
        <PhaseIndicator />

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow">
          {currentPhase === 'upload' && (
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Upload Medical Documents
              </h2>
              <p className="text-gray-600 mb-6">
                Select multiple medical documents (PDF, DOCX, TXT, RTF) to process as a batch. 
                The system will extract medical entities and map them to standard terminologies.
              </p>
              <BatchFileUpload onUploadSuccess={handleUploadSuccess} />
            </div>
          )}

          {currentPhase === 'processing' && batchId && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  Processing Documents
                </h2>
                <button
                  onClick={resetToUpload}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Start New Batch
                </button>
              </div>
              <p className="text-gray-600 mb-6">
                Your documents are being processed. This includes text extraction, medical entity recognition 
                using BioBERT, and terminology mapping to SNOMED CT, LOINC, and RxNorm.
              </p>
              <BatchProgressMonitor 
                batchId={batchId} 
                onComplete={handleProcessingComplete}
              />
            </div>
          )}

          {currentPhase === 'completed' && batchId && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  Processing Complete
                </h2>
                <button
                  onClick={resetToUpload}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Process New Batch
                </button>
              </div>
              <p className="text-gray-600 mb-6">
                Your batch has been processed successfully. Review the extracted entities, 
                terminology mappings, and export the results in your preferred format.
              </p>
              <BatchResultsViewer batchId={batchId} />
            </div>
          )}
        </div>

        {/* Help Section */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-3">
            How Batch Processing Works
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-blue-800">
            <div>
              <h4 className="font-medium mb-2">1. Document Upload</h4>
              <p>Upload multiple medical documents in supported formats. The system validates each file and creates a processing batch.</p>
            </div>
            <div>
              <h4 className="font-medium mb-2">2. AI Processing</h4>
              <p>BioBERT extracts medical entities (conditions, medications, tests) and maps them to standard terminologies.</p>
            </div>
            <div>
              <h4 className="font-medium mb-2">3. Results & Export</h4>
              <p>View detailed results with entity highlighting and confidence scores. Export to JSON, CSV, or Excel formats.</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};