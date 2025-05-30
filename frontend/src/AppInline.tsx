import React, { useState } from 'react';
import axios from 'axios';

// Simple API client
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Inline styles to avoid CSS import issues
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
  },
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '2rem',
  },
  form: {
    background: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  input: {
    width: '100%',
    padding: '0.75rem',
    fontSize: '1rem',
    border: '2px solid #e2e8f0',
    borderRadius: '4px',
    marginBottom: '1rem',
  },
  button: {
    background: '#667eea',
    color: 'white',
    padding: '0.75rem 2rem',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
  },
  error: {
    background: '#fed7d7',
    color: '#c53030',
    padding: '1rem',
    borderRadius: '4px',
    marginTop: '1rem',
  },
  results: {
    marginTop: '2rem',
  },
  mapping: {
    background: 'white',
    padding: '1rem',
    marginBottom: '1rem',
    borderRadius: '4px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
};

function AppInline() {
  const [term, setTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted with term:', term);
    
    setLoading(true);
    setError('');
    setResults(null);

    try {
      console.log('Sending request to API...');
      const response = await api.post('/map', {
        term,
        systems: ['snomed', 'loinc', 'rxnorm'],
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

      <div style={styles.container}>
        <form onSubmit={handleSubmit} style={styles.form}>
          <h2>Enter a Medical Term</h2>
          <input
            type="text"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="e.g., diabetes, aspirin, glucose test"
            style={styles.input}
            required
          />
          <button type="submit" style={styles.button} disabled={loading}>
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
            {Object.keys(results.results).length === 0 ? (
              <p>No mappings found</p>
            ) : (
              Object.entries(results.results).map(([system, mappings]: [string, any]) => (
                <div key={system}>
                  {mappings.map((mapping: any, index: number) => (
                    <div key={index} style={styles.mapping}>
                      <strong>{system.toUpperCase()}</strong><br />
                      Code: {mapping.code}<br />
                      Display: {mapping.display}<br />
                      Confidence: {Math.round(mapping.confidence * 100)}%
                    </div>
                  ))}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default AppInline;