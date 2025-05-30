import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

// Simple API client
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

function App() {
  const [activeTab, setActiveTab] = useState<'single' | 'batch'>('single');
  const [term, setTerm] = useState('');
  const [system, setSystem] = useState('all');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');

  const handleSingleTermSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResults(null);

    try {
      const response = await api.post('/map', {
        term,
        systems: system === 'all' ? ['snomed', 'loinc', 'rxnorm'] : [system],
        fuzzy_threshold: 0.8,
      });
      setResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to map term');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <h1>Medical Terminology Mapper</h1>
          <p>Map medical terms to standardized terminologies</p>
        </div>
      </header>

      <main className="main">
        <div className="container">
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'single' ? 'active' : ''}`}
              onClick={() => setActiveTab('single')}
            >
              Single Term
            </button>
            <button
              className={`tab ${activeTab === 'batch' ? 'active' : ''}`}
              onClick={() => setActiveTab('batch')}
            >
              Batch Processing
            </button>
          </div>

          {activeTab === 'single' && (
            <div className="tab-content">
              <form onSubmit={handleSingleTermSubmit} className="form">
                <div className="form-group">
                  <label htmlFor="term">Medical Term</label>
                  <input
                    id="term"
                    type="text"
                    value={term}
                    onChange={(e) => setTerm(e.target.value)}
                    placeholder="e.g., diabetes mellitus, aspirin, glucose test"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="system">Terminology System</label>
                  <select
                    id="system"
                    value={system}
                    onChange={(e) => setSystem(e.target.value)}
                  >
                    <option value="all">All Systems</option>
                    <option value="snomed">SNOMED CT</option>
                    <option value="loinc">LOINC</option>
                    <option value="rxnorm">RxNorm</option>
                  </select>
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Mapping...' : 'Map Term'}
                </button>
              </form>

              {error && (
                <div className="alert alert-error">
                  {error}
                </div>
              )}

              {results && (
                <div className="results">
                  <h3>Results for "{results.term}"</h3>
                  {results.mappings.length === 0 ? (
                    <p className="no-results">No mappings found</p>
                  ) : (
                    <div className="mappings">
                      {results.mappings.map((mapping: any, index: number) => (
                        <div key={index} className="mapping-card">
                          <div className="mapping-header">
                            <span className="system-badge">{mapping.system}</span>
                            <span className="confidence">
                              {Math.round(mapping.confidence * 100)}% match
                            </span>
                          </div>
                          <div className="mapping-body">
                            <div className="code">{mapping.code}</div>
                            <div className="display">{mapping.display}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'batch' && (
            <div className="tab-content">
              <div className="batch-info">
                <h3>Batch Processing</h3>
                <p>Upload a CSV file with medical terms to process multiple terms at once.</p>
                <div className="coming-soon">
                  <p>🚧 Coming Soon</p>
                  <p>Batch processing functionality is under development</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="footer">
        <div className="container">
          <div className="systems-info">
            <div className="system">
              <h4>SNOMED CT</h4>
              <p>Clinical terminology for conditions & procedures</p>
            </div>
            <div className="system">
              <h4>LOINC</h4>
              <p>Laboratory observations & test results</p>
            </div>
            <div className="system">
              <h4>RxNorm</h4>
              <p>Medications & pharmaceutical products</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;