import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ConfidenceBar } from '../common/ConfidenceBar';

interface BatchProgressMonitorProps {
  batchId: string;
  onComplete?: () => void;
}

interface DocumentStatus {
  document_id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
  processing_time?: number;
}

interface BatchStatus {
  batch_id: string;
  status: string;
  total_documents: number;
  processed_documents: number;
  successful_documents: number;
  failed_documents: number;
  progress_percentage: number;
  current_document?: string;
  documents: DocumentStatus[];
  started_at?: string;
  completed_at?: string;
}

export const BatchProgressMonitor = ({ batchId, onComplete }: BatchProgressMonitorProps) => {
  const { data: batchStatus, isLoading, error, refetch } = useQuery<BatchStatus>({
    queryKey: ['batchStatus', batchId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/documents/batch/${batchId}/status`);
      if (!response.ok) {
        throw new Error('Failed to fetch batch status');
      }
      return response.json();
    },
    refetchInterval: (data) => {
      // Stop polling when batch is complete
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
    refetchIntervalInBackground: false,
  });

  useEffect(() => {
    if (batchStatus?.status === 'completed' && onComplete) {
      onComplete();
    }
  }, [batchStatus?.status, onComplete]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner />
        <span className="ml-3 text-gray-600">Loading batch status...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <span className="ml-2 text-red-800">Failed to load batch status</span>
        </div>
        <button
          onClick={() => refetch()}
          className="mt-2 px-3 py-1 bg-red-100 text-red-800 rounded text-sm hover:bg-red-200"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!batchStatus) {
    return (
      <div className="text-center p-8 text-gray-500">
        No batch status available
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return (
          <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        );
      case 'processing':
        return <LoadingSpinner size="sm" />;
      case 'completed':
        return (
          <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-gray-600';
      case 'processing': return 'text-blue-600';
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '--';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Batch Processing Status
          </h3>
          <span className="text-sm text-gray-500">
            Batch ID: {batchStatus.batch_id}
          </span>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            {getStatusIcon(batchStatus.status)}
            <span className={`font-medium ${getStatusColor(batchStatus.status)}`}>
              {batchStatus.status.charAt(0).toUpperCase() + batchStatus.status.slice(1)}
            </span>
          </div>
          <div className="text-sm text-gray-600">
            {batchStatus.processed_documents} of {batchStatus.total_documents} processed
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <ConfidenceBar 
            confidence={batchStatus.progress_percentage / 100} 
            label={`${Math.round(batchStatus.progress_percentage)}% Complete`}
            showPercentage={false}
          />
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {batchStatus.successful_documents}
            </div>
            <div className="text-sm text-gray-600">Successful</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {batchStatus.failed_documents}
            </div>
            <div className="text-sm text-gray-600">Failed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">
              {batchStatus.total_documents - batchStatus.processed_documents}
            </div>
            <div className="text-sm text-gray-600">Pending</div>
          </div>
        </div>

        {/* Current Document */}
        {batchStatus.current_document && batchStatus.status === 'processing' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center">
              <LoadingSpinner size="sm" />
              <span className="ml-2 text-blue-800 text-sm">
                Currently processing: {batchStatus.current_document}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Document List */}
      <div className="px-6 pb-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">
          Document Details
        </h4>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {batchStatus.documents.map((doc) => (
            <div
              key={doc.document_id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded border"
            >
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                {getStatusIcon(doc.status)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {doc.filename}
                  </p>
                  {doc.error_message && (
                    <p className="text-xs text-red-600 truncate">
                      {doc.error_message}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                {doc.processing_time && (
                  <span>{formatDuration(doc.processing_time)}</span>
                )}
                <span className={getStatusColor(doc.status)}>
                  {doc.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      {batchStatus.status === 'completed' && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">
              Processing completed successfully
            </span>
            <div className="space-x-2">
              <button
                onClick={() => window.open(`/api/v1/documents/batch/${batchId}/export/json`, '_blank')}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Export JSON
              </button>
              <button
                onClick={() => window.open(`/api/v1/documents/batch/${batchId}/export/csv`, '_blank')}
                className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
              >
                Export CSV
              </button>
              <button
                onClick={() => window.open(`/api/v1/documents/batch/${batchId}/export/excel`, '_blank')}
                className="px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700"
              >
                Export Excel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};