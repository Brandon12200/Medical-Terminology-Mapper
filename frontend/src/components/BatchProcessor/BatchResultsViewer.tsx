import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { ConfidenceBar } from '../common/ConfidenceBar';
import { EntityHighlighter } from './EntityHighlighter';

interface BatchResultsViewerProps {
  batchId: string;
}

interface EntityData {
  text: string;
  label: string;
  start: number;
  end: number;
  confidence?: number;
}

interface TerminologyMapping {
  original_text: string;
  entity_type: string;
  code?: string;
  rxcui?: string;
  display?: string;
  name?: string;
  confidence?: number;
}

interface DocumentResult {
  document_id: string;
  filename: string;
  status: string;
  document_type: string;
  file_size: number;
  processing_time?: number;
  extracted_text?: string;
  entities?: EntityData[];
  terminology_mappings?: {
    snomed?: TerminologyMapping[];
    loinc?: TerminologyMapping[];
    rxnorm?: TerminologyMapping[];
  };
  entity_statistics?: {
    total_entities: number;
    entity_types: Record<string, number>;
    avg_confidence: number;
    high_confidence_entities: number;
  };
}

interface BatchResults {
  batch_id: string;
  export_timestamp: string;
  export_type: string;
  total_documents: number;
  documents: DocumentResult[];
  batch_statistics?: {
    total_documents: number;
    completed_documents: number;
    failed_documents: number;
    success_rate: number;
    total_entities_extracted: number;
    average_confidence: number;
    entities_per_document: number;
  };
}

export const BatchResultsViewer = ({ batchId }: BatchResultsViewerProps) => {
  const [selectedDocument, setSelectedDocument] = useState<DocumentResult | null>(null);
  const [showRawText, setShowRawText] = useState(false);

  const { data: results, isLoading, error } = useQuery<BatchResults>({
    queryKey: ['batchResults', batchId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/documents/batch/${batchId}/results`);
      if (!response.ok) {
        throw new Error('Failed to fetch batch results');
      }
      return response.json();
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner />
        <span className="ml-3 text-gray-600">Loading batch results...</span>
      </div>
    );
  }

  if (error) {
    return (
      <ErrorAlert message="Failed to load batch results" />
    );
  }

  if (!results) {
    return (
      <div className="text-center p-8 text-gray-500">
        No results available
      </div>
    );
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '--';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  const DocumentListItem = ({ doc }: { doc: DocumentResult }) => (
    <div
      className={`p-4 border rounded-lg cursor-pointer transition-all duration-200 ${
        selectedDocument?.document_id === doc.document_id
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
      }`}
      onClick={() => setSelectedDocument(doc)}
    >
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium text-gray-900 truncate">{doc.filename}</h4>
        <span
          className={`px-2 py-1 text-xs rounded ${
            doc.status === 'completed'
              ? 'bg-green-100 text-green-800'
              : doc.status === 'failed'
              ? 'bg-red-100 text-red-800'
              : 'bg-yellow-100 text-yellow-800'
          }`}
        >
          {doc.status}
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
        <div>
          <span className="font-medium">Entities:</span> {doc.entity_statistics?.total_entities || 0}
        </div>
        <div>
          <span className="font-medium">Size:</span> {formatFileSize(doc.file_size)}
        </div>
        <div>
          <span className="font-medium">Time:</span> {formatDuration(doc.processing_time)}
        </div>
        <div>
          <span className="font-medium">Confidence:</span>{' '}
          {doc.entity_statistics?.avg_confidence 
            ? `${(doc.entity_statistics.avg_confidence * 100).toFixed(1)}%`
            : '--'
          }
        </div>
      </div>

      {doc.entity_statistics && (
        <div className="mt-3">
          <div className="text-xs text-gray-500 mb-1">Entity Types:</div>
          <div className="flex flex-wrap gap-1">
            {Object.entries(doc.entity_statistics.entity_types).map(([type, count]) => (
              <span
                key={type}
                className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
              >
                {type}: {count}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const DocumentDetails = ({ doc }: { doc: DocumentResult }) => (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <h3 className="text-lg font-medium text-gray-900">{doc.filename}</h3>
        <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Status:</span>
            <span className={`ml-2 font-medium ${
              doc.status === 'completed' ? 'text-green-600' : 'text-red-600'
            }`}>
              {doc.status}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Type:</span>
            <span className="ml-2 font-medium">{doc.document_type}</span>
          </div>
          <div>
            <span className="text-gray-500">Size:</span>
            <span className="ml-2 font-medium">{formatFileSize(doc.file_size)}</span>
          </div>
          <div>
            <span className="text-gray-500">Processing Time:</span>
            <span className="ml-2 font-medium">{formatDuration(doc.processing_time)}</span>
          </div>
        </div>
      </div>

      {/* Entity Statistics */}
      {doc.entity_statistics && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-3">Entity Extraction Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {doc.entity_statistics.total_entities}
              </div>
              <div className="text-sm text-gray-600">Total Entities</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {doc.entity_statistics.high_confidence_entities}
              </div>
              <div className="text-sm text-gray-600">High Confidence</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {Object.keys(doc.entity_statistics.entity_types).length}
              </div>
              <div className="text-sm text-gray-600">Entity Types</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {(doc.entity_statistics.avg_confidence * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Avg Confidence</div>
            </div>
          </div>
          
          <ConfidenceBar 
            confidence={doc.entity_statistics.avg_confidence}
            label="Average Confidence"
          />
        </div>
      )}

      {/* Terminology Mappings Summary */}
      {doc.terminology_mappings && (
        <div className="bg-blue-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-3">Terminology Mappings</h4>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-xl font-bold text-red-600">
                {doc.terminology_mappings.snomed?.length || 0}
              </div>
              <div className="text-sm text-gray-600">SNOMED CT</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-green-600">
                {doc.terminology_mappings.loinc?.length || 0}
              </div>
              <div className="text-sm text-gray-600">LOINC</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-blue-600">
                {doc.terminology_mappings.rxnorm?.length || 0}
              </div>
              <div className="text-sm text-gray-600">RxNorm</div>
            </div>
          </div>
        </div>
      )}

      {/* Text View Controls */}
      {doc.extracted_text && (
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900">Document Text with Entity Highlighting</h4>
          <button
            onClick={() => setShowRawText(!showRawText)}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
          >
            {showRawText ? 'Show Highlighted' : 'Show Raw Text'}
          </button>
        </div>
      )}

      {/* Document Text */}
      {doc.extracted_text && (
        <div className="bg-white border rounded-lg p-4">
          {showRawText ? (
            <div className="text-sm font-mono whitespace-pre-wrap text-gray-800 max-h-96 overflow-y-auto">
              {doc.extracted_text.slice(0, 2000)}
              {doc.extracted_text.length > 2000 && (
                <div className="mt-2 text-gray-500 italic">
                  Text truncated at 2000 characters...
                </div>
              )}
            </div>
          ) : (
            <div className="max-h-96 overflow-y-auto">
              <EntityHighlighter
                text={doc.extracted_text}
                entities={doc.entities || []}
                terminologyMappings={doc.terminology_mappings}
                maxLength={2000}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Batch Summary */}
      {results.batch_statistics && (
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Batch Results Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {results.batch_statistics.total_documents}
              </div>
              <div className="text-sm text-gray-600">Total Documents</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {results.batch_statistics.success_rate.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Success Rate</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">
                {results.batch_statistics.total_entities_extracted}
              </div>
              <div className="text-sm text-gray-600">Total Entities</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">
                {results.batch_statistics.entities_per_document.toFixed(1)}
              </div>
              <div className="text-sm text-gray-600">Entities/Document</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document List */}
        <div className="lg:col-span-1">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Documents ({results.documents.length})
          </h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {results.documents.map((doc) => (
              <DocumentListItem key={doc.document_id} doc={doc} />
            ))}
          </div>
        </div>

        {/* Document Details */}
        <div className="lg:col-span-2">
          {selectedDocument ? (
            <DocumentDetails doc={selectedDocument} />
          ) : (
            <div className="text-center p-8 text-gray-500 border-2 border-dashed border-gray-200 rounded-lg">
              Select a document to view detailed results
            </div>
          )}
        </div>
      </div>
    </div>
  );
};