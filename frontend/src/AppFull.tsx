import React, { useState } from 'react';
import axios from 'axios';

// Simple API client
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Inline styles
const styles = {
  app: {
    minHeight: '100vh',
    backgroundColor: '#f5f7fa',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '2rem',
    textAlign: 'center' as const,
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '2rem',
  },
  tabs: {
    display: 'flex',
    gap: '1rem',
    marginBottom: '2rem',
    borderBottom: '2px solid #e2e8f0',
  },
  tab: {
    background: 'none',
    border: 'none',
    padding: '1rem 2rem',
    fontSize: '1rem',
    fontWeight: '500',
    color: '#718096',
    cursor: 'pointer',
    position: 'relative' as const,
    transition: 'all 0.3s ease',
  },
  activeTab: {
    color: '#667eea',
    borderBottom: '2px solid #667eea',
  },
  tabContent: {
    background: 'white',
    padding: '2rem',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  form: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1.5rem',
    maxWidth: '600px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  label: {
    fontWeight: '600',
    color: '#4a5568',
    fontSize: '0.95rem',
  },
  input: {
    padding: '0.75rem',
    fontSize: '1rem',
    border: '2px solid #e2e8f0',
    borderRadius: '8px',
    transition: 'all 0.3s ease',
  },
  select: {
    padding: '0.75rem',
    fontSize: '1rem',
    border: '2px solid #e2e8f0',
    borderRadius: '8px',
    background: 'white',
    cursor: 'pointer',
  },
  button: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '0.75rem 2rem',
    border: 'none',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
  },
  buttonDisabled: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
  error: {
    background: '#fed7d7',
    color: '#c53030',
    padding: '1rem',
    borderRadius: '8px',
    marginTop: '1rem',
    border: '1px solid #fc8181',
  },
  results: {
    marginTop: '2rem',
  },
  mappingCard: {
    background: '#f7fafc',
    border: '1px solid #e2e8f0',
    padding: '1.5rem',
    marginBottom: '1rem',
    borderRadius: '8px',
    transition: 'all 0.3s ease',
  },
  mappingHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  systemBadge: {
    background: '#667eea',
    color: 'white',
    padding: '0.25rem 0.75rem',
    borderRadius: '4px',
    fontSize: '0.875rem',
    fontWeight: '600',
    textTransform: 'uppercase' as const,
  },
  confidence: {
    color: '#48bb78',
    fontWeight: '600',
  },
  code: {
    fontFamily: 'monospace',
    fontSize: '1.1rem',
    fontWeight: '600',
    color: '#2d3748',
  },
  comingSoon: {
    background: '#f7fafc',
    border: '2px dashed #cbd5e0',
    borderRadius: '8px',
    padding: '3rem',
    textAlign: 'center' as const,
    marginTop: '2rem',
  },
  footer: {
    background: '#2d3748',
    color: 'white',
    padding: '2rem',
    marginTop: 'auto',
  },
  systemsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '2rem',
  },
};

function AppFull() {
  const [activeTab, setActiveTab] = useState<'single' | 'batch'>('single');
  const [term, setTerm] = useState('');
  const [system, setSystem] = useState('all');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted with term:', term, 'system:', system);
    
    setLoading(true);
    setError('');
    setResults(null);

    try {
      const response = await api.post('/map', {
        term,
        systems: system === 'all' ? ['snomed', 'loinc', 'rxnorm'] : [system],
        fuzzy_threshold: 0.8,
      });
      console.log('API response:', response.data);
      setResults(response.data);
    } catch (err: any) {
      console.error('API error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to map term';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1>Medical Terminology Mapper</h1>
        <p>Map medical terms to standardized terminologies</p>
      </header>

      <main style={{ flex: 1 }}>
        <div style={styles.container}>
          <div style={styles.tabs}>
            <button
              style={{
                ...styles.tab,
                ...(activeTab === 'single' ? styles.activeTab : {}),
              }}
              onClick={() => setActiveTab('single')}
            >
              Single Term
            </button>
            <button
              style={{
                ...styles.tab,
                ...(activeTab === 'batch' ? styles.activeTab : {}),
              }}
              onClick={() => setActiveTab('batch')}
            >
              Batch Processing
            </button>
          </div>

          {activeTab === 'single' && (
            <div style={styles.tabContent}>
              <form onSubmit={handleSubmit} style={styles.form}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Medical Term</label>
                  <input
                    type="text"
                    value={term}
                    onChange={(e) => setTerm(e.target.value)}
                    placeholder="e.g., diabetes mellitus, aspirin, glucose test"
                    style={styles.input}
                    required
                  />
                </div>

                <div style={styles.formGroup}>
                  <label style={styles.label}>Terminology System</label>
                  <select
                    value={system}
                    onChange={(e) => setSystem(e.target.value)}
                    style={styles.select}
                  >
                    <option value="all">All Systems</option>
                    <option value="snomed">SNOMED CT</option>
                    <option value="loinc">LOINC</option>
                    <option value="rxnorm">RxNorm</option>
                  </select>
                </div>

                <button
                  type="submit"
                  style={{
                    ...styles.button,
                    ...(loading ? styles.buttonDisabled : {}),
                  }}
                  disabled={loading}
                >
                  {loading ? 'Mapping...' : 'Map Term'}
                </button>
              </form>

              {error && (
                <div style={styles.error}>
                  {error}
                </div>
              )}

              {results && (
                <div style={styles.results}>
                  <h3>Results for "{results.term}"</h3>
                  {results.total_matches === 0 ? (
                    <p style={{ textAlign: 'center', color: '#718096', padding: '2rem' }}>
                      No mappings found
                    </p>
                  ) : (
                    Object.entries(results.results).map(([system, mappings]: [string, any]) => (
                      <div key={system}>
                        {mappings.map((mapping: any, index: number) => (
                          <div key={index} style={styles.mappingCard}>
                            <div style={styles.mappingHeader}>
                              <span style={styles.systemBadge}>{system}</span>
                              <span style={styles.confidence}>
                                {Math.round(mapping.confidence * 100)}% match
                              </span>
                            </div>
                            <div>
                              <div style={styles.code}>{mapping.code}</div>
                              <div style={{ color: '#4a5568' }}>{mapping.display}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'batch' && (
            <div style={styles.tabContent}>
              <h3>Batch Processing</h3>
              <p>Upload a CSV file with medical terms to process multiple terms at once.</p>
              <div style={styles.comingSoon}>
                <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🚧 Coming Soon</p>
                <p style={{ color: '#718096' }}>
                  Batch processing functionality is under development
                </p>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer style={styles.footer}>
        <div style={styles.container}>
          <div style={styles.systemsGrid}>
            <div>
              <h4 style={{ marginBottom: '0.5rem' }}>SNOMED CT</h4>
              <p style={{ fontSize: '0.9rem', color: '#a0aec0' }}>
                Clinical terminology for conditions & procedures
              </p>
            </div>
            <div>
              <h4 style={{ marginBottom: '0.5rem' }}>LOINC</h4>
              <p style={{ fontSize: '0.9rem', color: '#a0aec0' }}>
                Laboratory observations & test results
              </p>
            </div>
            <div>
              <h4 style={{ marginBottom: '0.5rem' }}>RxNorm</h4>
              <p style={{ fontSize: '0.9rem', color: '#a0aec0' }}>
                Medications & pharmaceutical products
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default AppFull;