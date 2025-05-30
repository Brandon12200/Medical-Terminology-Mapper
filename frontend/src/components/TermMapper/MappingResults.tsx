import type { MappingResponse } from '../../types';
import { ConfidenceBar } from '../common/ConfidenceBar';
import { exportToCSV, exportToJSON } from '../../utils/exportUtils';

interface MappingResultsProps {
  results: MappingResponse | null;
}

export const MappingResults = ({ results }: MappingResultsProps) => {
  if (!results) return null;

  const handleExportCSV = () => {
    const filename = `mapping_${results.term.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.csv`;
    exportToCSV(results, filename);
  };

  const handleExportJSON = () => {
    const filename = `mapping_${results.term.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.json`;
    exportToJSON(results, filename);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 bg-green-50';
    if (confidence >= 0.7) return 'text-yellow-600 bg-yellow-50';
    return 'text-orange-600 bg-orange-50';
  };

  return (
    <div className="mt-6 bg-white p-6 rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          Results for: "{results.term}"
        </h3>
        {results.mappings.length > 0 && (
          <div className="flex gap-2">
            <button
              onClick={handleExportCSV}
              className="text-sm px-3 py-1 text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Export CSV
            </button>
            <button
              onClick={handleExportJSON}
              className="text-sm px-3 py-1 text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Export JSON
            </button>
          </div>
        )}
      </div>
      
      {results.mappings.length === 0 ? (
        <p className="text-gray-500">No mappings found for this term.</p>
      ) : (
        <div className="space-y-4">
          {results.mappings.map((mapping, index) => (
            <div key={index} className="border rounded-lg p-4">
              <div className="mb-3">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="text-sm font-medium text-gray-500 uppercase">
                      {mapping.system}
                    </span>
                    <h4 className="text-lg font-medium text-gray-900">
                      {mapping.display}
                    </h4>
                    <p className="text-sm text-gray-600">Code: {mapping.code}</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(mapping.confidence)}`}>
                      {(mapping.confidence * 100).toFixed(0)}% match
                    </span>
                    {mapping.match_type && (
                      <p className="text-xs text-gray-500 mt-1">{mapping.match_type}</p>
                    )}
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-xs text-gray-500 mb-1">Confidence Score</div>
                  <ConfidenceBar confidence={mapping.confidence} height="sm" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};