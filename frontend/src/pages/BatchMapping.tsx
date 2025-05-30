import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileUpload } from '../components/BatchProcessor/FileUpload';
import { ProcessingStatus } from '../components/BatchProcessor/ProcessingStatus';
import { mappingService } from '../services/mappingService';
import { exportToCSV, exportToJSON } from '../utils/exportUtils';
import { ConfidenceBar } from '../components/common/ConfidenceBar';
import type { MappingResponse } from '../types';

export const BatchMapping = () => {
  const [jobId, setJobId] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const { data: results } = useQuery({
    queryKey: ['batchResults', jobId],
    queryFn: () => mappingService.getBatchResults(jobId!),
    enabled: isComplete && !!jobId,
  });

  const handleUploadSuccess = (newJobId: string) => {
    setJobId(newJobId);
    setIsComplete(false);
    setIsProcessing(true);
  };

  const handleProcessingComplete = () => {
    setIsComplete(true);
    setIsProcessing(false);
  };

  const downloadResults = (format: 'csv' | 'json') => {
    if (results) {
      const filename = `batch_results_${new Date().toISOString().split('T')[0]}.${format}`;
      if (format === 'csv') {
        exportToCSV(results, filename);
      } else {
        exportToJSON(results, filename);
      }
    }
  };

  const resetBatch = () => {
    setJobId(null);
    setIsComplete(false);
    setIsProcessing(false);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Batch Processing
      </h1>

      {!isProcessing && !isComplete && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Upload CSV File
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Upload a CSV file with a column containing medical terms to map.
            The first column will be used for mapping.
          </p>
          <FileUpload onUploadSuccess={handleUploadSuccess} />
        </div>
      )}

      {jobId && isProcessing && (
        <ProcessingStatus jobId={jobId} onComplete={handleProcessingComplete} />
      )}

      {isComplete && results && (
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">
              Results ({results.length} terms processed)
            </h2>
            <div className="space-x-2">
              <button
                onClick={resetBatch}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                New Batch
              </button>
              <button
                onClick={() => downloadResults('csv')}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Download CSV
              </button>
              <button
                onClick={() => downloadResults('json')}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Download JSON
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Term
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Mappings Found
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Best Match
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.map((result: MappingResponse, index: number) => {
                  const bestMatch = result.mappings[0];
                  return (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {result.term}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {result.mappings.length}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {bestMatch ? (
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium">{bestMatch.display}</span>
                              <span className="text-gray-400">
                                ({bestMatch.system}: {bestMatch.code})
                              </span>
                            </div>
                            <div className="max-w-xs">
                              <ConfidenceBar confidence={bestMatch.confidence} height="sm" showLabel={true} />
                            </div>
                          </div>
                        ) : (
                          <span className="text-gray-400">No mapping found</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};