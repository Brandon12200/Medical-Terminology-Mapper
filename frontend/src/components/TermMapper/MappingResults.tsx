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

  return (
    <div className="results-container">
      <div className="result-card">
        <div className="result-header">
          <h3 className="result-term">
            Results for: "{results.term}"
          </h3>
          {results.mappings.length > 0 && (
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={handleExportCSV}
                className="btn btn-secondary"
                style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
              >
                Export CSV
              </button>
              <button
                onClick={handleExportJSON}
                className="btn btn-secondary"
                style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
              >
                Export JSON
              </button>
            </div>
          )}
        </div>
        
        {results.mappings.length === 0 ? (
          <p style={{ color: '#718096', textAlign: 'center', padding: '2rem' }}>
            No mappings found for this term.
          </p>
        ) : (
          <div className="result-mappings">
            {results.mappings.map((mapping, index) => (
              <div key={index} className="mapping-item">
                <div>
                  <div className="mapping-system">{mapping.system.toUpperCase()}</div>
                  <div style={{ marginTop: '0.25rem' }}>{mapping.display}</div>
                  <div className="mapping-code">Code: {mapping.code}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className="result-confidence">
                    {(mapping.confidence * 100).toFixed(0)}% match
                  </div>
                  {mapping.match_type && (
                    <div style={{ fontSize: '0.75rem', color: '#718096', marginTop: '0.25rem' }}>
                      {mapping.match_type}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};