import { useState, useEffect } from 'react';
import { api } from './services/api';
import { exportToCSV, exportToJSON } from './utils/exportUtils';
import type { MappingRequest, MappingResponse, BatchJobStatus, SystemInfo } from './types';
import './styles.css';

// Sample files data
const SAMPLE_FILES = [
  {
    filename: 'hospital_discharge_summary.csv',
    name: 'Hospital Discharge Summary',
    icon: '🏥',
    description: '120+ comprehensive medical conditions across all specialties including cardiology, neurology, oncology, and emergency medicine with detailed clinical contexts.',
    details: 'Complex multi-system cases • Severity classifications • Specialty mappings',
    count: '120+ terms'
  },
  {
    filename: 'comprehensive_lab_tests.csv',
    name: 'Comprehensive Lab Tests',
    icon: '🧪',
    description: '150+ laboratory tests including hematology, chemistry, microbiology, immunology, and specialized genetic testing with clinical significance.',
    details: 'LOINC optimization • Clinical contexts • Test type classifications',
    count: '150+ terms'
  },
  {
    filename: 'comprehensive_medications.csv',
    name: 'Pharmaceutical Database',
    icon: '💊',
    description: '200+ medications covering all major drug classes from basic analgesics to specialized biologics with therapeutic indications and mechanisms.',
    details: 'RxNorm standardization • Drug class mapping • Clinical applications',
    count: '200+ terms'
  },
  {
    filename: 'emergency_department_cases.csv',
    name: 'Emergency Department Cases',
    icon: '🚨',
    description: '100+ emergency scenarios from critical life-threatening conditions to minor injuries with triage severity and specialty assignments.',
    details: 'Severity scoring • Department routing • Clinical presentations',
    count: '100+ terms'
  },
  {
    filename: 'surgical_procedures.csv',
    name: 'Surgical Procedures',
    icon: '⚕️',
    description: '130+ surgical procedures from minimally invasive outpatient procedures to complex multi-organ transplants with complexity ratings.',
    details: 'Procedure complexity • Specialty mapping • Risk stratification',
    count: '130+ terms'
  },
  {
    filename: 'rare_diseases_comprehensive.csv',
    name: 'Rare Diseases',
    icon: '🧬',
    description: '200+ rare genetic conditions including metabolic disorders, neurodegenerative diseases, and genetic syndromes with inheritance patterns.',
    details: 'Genetic classifications • Inheritance patterns • Specialty focus areas',
    count: '200+ terms'
  }
];

// Simplified mapping service
const mappingService = {
  mapTerm: async (request: MappingRequest): Promise<MappingResponse> => {
    const { data } = await api.post<any>('/map', request);
    
    if (data.results && typeof data.results === 'object') {
      const mappings: any[] = [];
      Object.entries(data.results).forEach(([, systemMappings]) => {
        if (Array.isArray(systemMappings)) {
          mappings.push(...systemMappings);
        }
      });
      
      return {
        term: data.term,
        mappings: mappings
      };
    }
    
    return data;
  },

  getSystems: async (): Promise<SystemInfo[]> => {
    const { data } = await api.get<{ systems: SystemInfo[] }>('/systems');
    return data.systems || [];
  },

  processBatch: async (request: any): Promise<{ job_id: string }> => {
    const { data } = await api.post<{ job_id: string }>('/batch', request);
    return data;
  },

  getBatchStatus: async (jobId: string): Promise<BatchJobStatus> => {
    const { data } = await api.get<BatchJobStatus>(`/batch/status/${jobId}`);
    return data;
  },

  getBatchResults: async (jobId: string): Promise<MappingResponse[]> => {
    const { data } = await api.get<any>(`/batch/result/${jobId}`);
    
    const resultsArray = data.results || [];
    
    return resultsArray.map((item: any) => {
      const mappings: any[] = [];
      const mappingData = item.mappings || item.results || {};
      
      if (mappingData && typeof mappingData === 'object') {
        Object.entries(mappingData).forEach(([system, systemMappings]) => {
          if (Array.isArray(systemMappings)) {
            systemMappings.forEach(mapping => {
              if (mapping && mapping.code && mapping.display) {
                mappings.push({
                  ...mapping,
                  system: system
                });
              }
            });
          }
        });
      }
      
      return {
        term: item.original_term || item.term,
        mappings: mappings
      };
    });
  },

  uploadFile: async (file: File): Promise<{ job_id: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_format', 'csv');
    formData.append('column_name', 'term');
    
    const { data } = await api.post<{ job_id: string }>('/batch/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },
};

// Simple components inline
const LoadingSpinner = () => (
  <div className="loading-spinner">
    <div className="spinner"></div>
  </div>
);

const ErrorAlert = ({ message }: { message: string }) => (
  <div className="error-alert">
    <p>{message}</p>
  </div>
);

const ConfidenceBar = ({ confidence, height = 'md', showLabel = true }: { 
  confidence: number; 
  height?: 'sm' | 'md' | 'lg'; 
  showLabel?: boolean;
}) => {
  const percentage = Math.round(confidence * 100);
  const heightClass = height === 'sm' ? 'h-2' : height === 'lg' ? 'h-4' : 'h-3';
  
  const getColorClass = () => {
    if (confidence >= 0.8) return 'bg-green-500';
    if (confidence >= 0.6) return 'bg-yellow-500';
    if (confidence >= 0.4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div>
      <div className={`w-full bg-gray-200 rounded-full ${heightClass} overflow-hidden`}>
        <div
          className={`${heightClass} ${getColorClass()} transition-all duration-300 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="text-xs text-gray-600 mt-1">
          {percentage}%
        </div>
      )}
    </div>
  );
};

function App() {
  // Navigation state
  const [currentView, setCurrentView] = useState<'home' | 'single' | 'batch' | 'docs'>('home');
  
  // Single mapping state
  const [singleResults, setSingleResults] = useState<MappingResponse | null>(null);
  const [singleFormData, setSingleFormData] = useState<MappingRequest>({
    term: '',
    systems: ['all'],
    context: '',
    fuzzy_threshold: 0.7,
  });
  const [singleLoading, setSingleLoading] = useState(false);
  const [singleError, setSingleError] = useState<string | null>(null);
  const [systems, setSystems] = useState<SystemInfo[]>([]);

  // Batch mapping state
  const [jobId, setJobId] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [batchResults, setBatchResults] = useState<MappingResponse[] | null>(null);
  const [batchStatus, setBatchStatus] = useState<BatchJobStatus | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  // Load systems on mount
  useEffect(() => {
    mappingService.getSystems().then(setSystems).catch(console.error);
  }, []);

  // Batch status polling
  useEffect(() => {
    if (!jobId || !isProcessing) return;

    const pollStatus = async () => {
      try {
        const status = await mappingService.getBatchStatus(jobId);
        setBatchStatus(status);
        
        if (status.status === 'completed') {
          setIsComplete(true);
          setIsProcessing(false);
          const results = await mappingService.getBatchResults(jobId);
          setBatchResults(results);
        } else if (status.status === 'failed') {
          setIsProcessing(false);
          alert('Batch processing failed. Please try again.');
        }
      } catch (error) {
        console.error('Error polling status:', error);
      }
    };

    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, [jobId, isProcessing]);

  // Single form handlers
  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!singleFormData.term.trim()) return;

    setSingleLoading(true);
    setSingleError(null);
    
    try {
      const result = await mappingService.mapTerm(singleFormData);
      setSingleResults(result);
    } catch (error: any) {
      setSingleError(error.message || 'An error occurred');
    } finally {
      setSingleLoading(false);
    }
  };

  const handleSingleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setSingleFormData(prev => ({
      ...prev,
      [name]: name === 'fuzzy_threshold' 
        ? parseFloat(value) 
        : name === 'systems' 
          ? [value] 
          : value,
    }));
  };

  // Batch handlers
  const handleFileUpload = async (file: File) => {
    setUploadLoading(true);
    try {
      const response = await mappingService.uploadFile(file);
      setJobId(response.job_id);
      setIsComplete(false);
      setIsProcessing(true);
      setBatchResults(null);
    } catch (error: any) {
      alert('Upload failed: ' + error.message);
    } finally {
      setUploadLoading(false);
    }
  };

  const downloadSampleFile = async (filename: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/test-files/${filename}`);
      if (!response.ok) throw new Error('File not found');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
  };

  const processSampleFile = async (filename: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/test-files/${filename}`);
      if (!response.ok) throw new Error('File not found');
      
      const blob = await response.blob();
      const file = new File([blob], filename, { type: 'text/csv' });
      
      await handleFileUpload(file);
    } catch (error: any) {
      console.error('Processing failed:', error);
      const errorMessage = error.message?.includes('validation') || error.message?.includes('code') 
        ? 'Processing failed due to API data validation. This file may contain terms that cause issues with external APIs. Please try a different sample file.'
        : 'Processing failed. Please try again.';
      alert(errorMessage);
    }
  };

  const resetBatch = () => {
    setJobId(null);
    setIsComplete(false);
    setIsProcessing(false);
    setBatchResults(null);
    setBatchStatus(null);
  };

  const resetSingle = () => {
    setSingleResults(null);
    setSingleError(null);
    setSingleFormData({
      term: '',
      systems: ['all'],
      context: '',
      fuzzy_threshold: 0.7,
    });
  };

  // Export handlers
  const downloadSingleResults = (format: 'csv' | 'json') => {
    if (singleResults) {
      const filename = `mapping_${singleResults.term.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.${format}`;
      if (format === 'csv') {
        exportToCSV(singleResults, filename);
      } else {
        exportToJSON(singleResults, filename);
      }
    }
  };

  const downloadBatchResults = (format: 'csv' | 'json') => {
    if (batchResults) {
      const filename = `batch_results_${new Date().toISOString().split('T')[0]}.${format}`;
      if (format === 'csv') {
        exportToCSV(batchResults, filename);
      } else {
        exportToJSON(batchResults, filename);
      }
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <button 
            onClick={() => setCurrentView('home')} 
            className="app-title"
            style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer' }}
          >
            Medical Terminology Mapper
          </button>
          <nav className="nav-links">
            <button 
              onClick={() => setCurrentView('single')}
              style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontWeight: '500' }}
            >
              Single Term
            </button>
            <button 
              onClick={() => {
                setCurrentView('batch');
                resetBatch();
              }}
              style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontWeight: '500' }}
            >
              Batch Processing
            </button>
            <button 
              onClick={() => setCurrentView('docs')}
              style={{ 
                background: 'rgba(255, 255, 255, 0.1)', 
                border: '1px solid rgba(255, 255, 255, 0.2)', 
                borderRadius: '6px',
                padding: '0.5rem 0.75rem',
                color: 'white', 
                cursor: 'pointer', 
                fontWeight: '500',
                fontSize: '0.875rem',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.15)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.1)';
              }}
            >
              📖 Docs
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        <div className="container">
          
          {/* Home View */}
          {currentView === 'home' && (
            <div>
              <div className="hero-section">
                <h1 className="hero-title">
                  Medical Terminology Mapper
                </h1>
                <p className="hero-subtitle">
                  Transform medical terms into standardized terminologies with precision. 
                  Supporting SNOMED CT, LOINC, and RxNorm for comprehensive healthcare data mapping.
                </p>
              </div>

              <div className="feature-grid">
                <button 
                  onClick={() => setCurrentView('single')} 
                  className="feature-card"
                  style={{ border: 'none', cursor: 'pointer', textAlign: 'left' }}
                >
                  <div className="feature-icon">📋</div>
                  <h2 className="feature-title">
                    Single Term Mapping
                  </h2>
                  <p className="feature-description">
                    Instantly map individual medical terms to standard terminology systems with real-time results.
                  </p>
                  <span className="feature-link">Get started →</span>
                </button>

                <button 
                  onClick={() => setCurrentView('batch')} 
                  className="feature-card"
                  style={{ border: 'none', cursor: 'pointer', textAlign: 'left' }}
                >
                  <div className="feature-icon">📁</div>
                  <h2 className="feature-title">
                    Batch Processing
                  </h2>
                  <p className="feature-description">
                    Upload CSV files with multiple terms and process them all at once for efficient bulk mapping.
                  </p>
                  <span className="feature-link">Upload file →</span>
                </button>
              </div>

              <div className="systems-section">
                <h3 className="systems-title">
                  Supported Terminology Systems
                </h3>
                <div className="systems-grid">
                  <div className="system-item">
                    <h4 className="system-name">SNOMED CT</h4>
                    <p className="system-description">Comprehensive clinical terminology for healthcare</p>
                  </div>
                  <div className="system-item">
                    <h4 className="system-name">LOINC</h4>
                    <p className="system-description">Universal codes for laboratory and clinical observations</p>
                  </div>
                  <div className="system-item">
                    <h4 className="system-name">RxNorm</h4>
                    <p className="system-description">Standardized nomenclature for medications and drugs</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Single Mapping View */}
          {currentView === 'single' && (
            <div className="form-container">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h1 className="form-title" style={{ margin: 0 }}>
                  Single Term Mapping
                </h1>
                {(singleResults || singleError) && (
                  <button
                    onClick={resetSingle}
                    className="btn btn-secondary"
                    style={{ 
                      padding: '0.5rem 1rem',
                      fontSize: '0.875rem'
                    }}
                  >
                    New Search
                  </button>
                )}
              </div>
              <p className="form-description">
                Enter a medical term to find its standardized mappings across SNOMED CT, LOINC, and RxNorm terminologies.
              </p>
              
              {/* Single Term Form */}
              <form onSubmit={handleSingleSubmit}>
                <div className="form-group">
                  <label htmlFor="term" className="form-label">Medical Term</label>
                  <input
                    type="text"
                    id="term"
                    name="term"
                    value={singleFormData.term}
                    onChange={handleSingleFormChange}
                    placeholder="e.g., diabetes mellitus type 2"
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="systems" className="form-label">Terminology System</label>
                  <select
                    id="systems"
                    name="systems"
                    value={singleFormData.systems[0]}
                    onChange={handleSingleFormChange}
                    className="form-select"
                  >
                    <option value="all">All Systems</option>
                    {systems.map(system => (
                      <option key={system.name} value={system.name}>
                        {system.display_name}
                      </option>
                    ))}
                  </select>
                </div>


                <button
                  type="submit"
                  disabled={singleLoading}
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                >
                  {singleLoading ? 'Mapping...' : 'Map Term'}
                </button>
              </form>

              {singleLoading && <LoadingSpinner />}
              {singleError && <ErrorAlert message={singleError} />}
              
              {/* Single Results */}
              {singleResults && (
                <div className="results-container">
                  <div className="result-card">
                    <div className="result-header">
                      <h3 className="result-term">
                        Results for: "{singleResults.term}"
                      </h3>
                      {singleResults.mappings.length > 0 && (
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button
                            onClick={() => downloadSingleResults('csv')}
                            className="btn btn-secondary"
                            style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
                          >
                            Export CSV
                          </button>
                          <button
                            onClick={() => downloadSingleResults('json')}
                            className="btn btn-secondary"
                            style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
                          >
                            Export JSON
                          </button>
                        </div>
                      )}
                    </div>
                    
                    {singleResults.mappings.length === 0 ? (
                      <p style={{ color: '#718096', textAlign: 'center', padding: '2rem' }}>
                        No mappings found for this term.
                      </p>
                    ) : (
                      <div className="result-mappings">
                        {singleResults.mappings.map((mapping, index) => (
                          <div key={index} className="mapping-item">
                            <div>
                              <div className="mapping-system">
                                {mapping.system.toUpperCase()}
                              </div>
                              <div style={{ marginTop: '0.25rem' }}>
                                {mapping.display}
                              </div>
                              <div className="mapping-code">
                                Code: {mapping.code}
                              </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <div className="result-confidence">
                                {Math.round(mapping.confidence * 100)}% match
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
              )}
            </div>
          )}

          {/* Batch Mapping View */}
          {currentView === 'batch' && (
            <div className="form-container">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h1 className="form-title" style={{ margin: 0 }}>
                  Batch Processing
                </h1>
                {(isComplete || isProcessing) && (
                  <button
                    onClick={resetBatch}
                    className="btn btn-secondary"
                    style={{ 
                      backgroundColor: '#667eea',
                      color: 'white',
                      fontWeight: '600'
                    }}
                  >
                    Back
                  </button>
                )}
              </div>
              <p className="form-description">
                Process thousands of medical terms at once with our comprehensive batch mapping system. 
                Upload your CSV files and get standardized terminologies across SNOMED CT, LOINC, and RxNorm.
              </p>

              {!isProcessing && !isComplete && (
                <>
                  {/* File Upload Section */}
                  <div className="upload-section">
                    <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', color: '#1a202c' }}>
                      📤 Upload Your Own CSV File
                    </h2>
                    <p style={{ color: '#4a5568', marginBottom: '1rem' }}>
                      Upload a CSV file with medical terms in the first column. Our system will automatically 
                      map each term to standardized terminologies and provide detailed results.
                    </p>
                    
                    <div className="file-upload-area">
                      <input
                        type="file"
                        accept=".csv"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleFileUpload(file);
                        }}
                        disabled={uploadLoading}
                        className="file-input"
                      />
                      {uploadLoading && <LoadingSpinner />}
                    </div>
                  </div>

                  {/* Sample Files */}
                  <div>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1a202c' }}>
                      📁 Or Try Our Sample Files
                    </h2>
                    <div className="feature-grid">
                      {SAMPLE_FILES.map((file, index) => (
                        <div key={index} className="feature-card" style={{ cursor: 'default', position: 'relative' }}>
                          <div className="feature-icon">{file.icon}</div>
                          <h3 className="feature-title" style={{ fontSize: '1.25rem' }}>{file.name}</h3>
                          <p className="feature-description">
                            <strong>{file.count}</strong> - {file.description}
                          </p>
                          <div style={{ fontSize: '0.875rem', color: '#667eea', marginTop: '0.5rem', marginBottom: '1rem' }}>
                            {file.details}
                          </div>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button
                              onClick={() => processSampleFile(file.filename)}
                              className="btn btn-primary"
                              style={{ 
                                flex: '1', 
                                fontSize: '0.875rem',
                                padding: '0.5rem 1rem'
                              }}
                            >
                              🚀 Try Sample
                            </button>
                            <button
                              onClick={() => downloadSampleFile(file.filename)}
                              className="btn btn-secondary"
                              style={{ 
                                flex: '1', 
                                fontSize: '0.875rem',
                                padding: '0.5rem 1rem'
                              }}
                            >
                              📥 Download
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div style={{ 
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                      color: 'white', 
                      padding: '1.5rem', 
                      borderRadius: '12px', 
                      marginTop: '2rem',
                      textAlign: 'center'
                    }}>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                        🎯 Perfect for Demonstrating Enterprise Capabilities
                      </h3>
                      <p style={{ opacity: '0.9', marginBottom: '1rem' }}>
                        These comprehensive datasets showcase real-world medical terminology mapping at scale, 
                        demonstrating accuracy across diverse clinical scenarios and specialties.
                      </p>
                      <div style={{ fontSize: '0.875rem', opacity: '0.8' }}>
                        <strong>Total Terms:</strong> 1,000+ medical concepts • 
                        <strong>Coverage:</strong> 15+ medical specialties • 
                        <strong>Complexity:</strong> Simple to highly specialized terminology
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Processing Status */}
              {jobId && isProcessing && (
                <div className="processing-container">
                  <div className="processing-header">
                    <h2>Processing Batch Job</h2>
                    <p>Your batch is being processed. This may take a few moments...</p>
                  </div>
                  
                  {batchStatus && (
                    <div className="progress-container">
                      <div className="progress-info">
                        <span>Progress: {batchStatus.processed_terms} / {batchStatus.total_terms} terms</span>
                        <span>{Math.round((batchStatus.processed_terms / batchStatus.total_terms) * 100)}%</span>
                      </div>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill"
                          style={{ 
                            width: `${(batchStatus.processed_terms / batchStatus.total_terms) * 100}%` 
                          }}
                        />
                      </div>
                      <div className="progress-status">
                        Status: <span className="status-badge">{batchStatus.status}</span>
                      </div>
                    </div>
                  )}
                  
                  <LoadingSpinner />
                </div>
              )}

              {/* Batch Results */}
              {isComplete && batchResults && (
                <div className="results-container">
                  <div className="result-card">
                    <div className="result-header">
                      <h2 className="result-term">
                        🎉 Batch Processing Complete - {batchResults.length} terms processed
                      </h2>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          onClick={() => downloadBatchResults('csv')}
                          className="btn btn-secondary"
                        >
                          Download CSV
                        </button>
                        <button
                          onClick={() => downloadBatchResults('json')}
                          className="btn btn-secondary"
                        >
                          Download JSON
                        </button>
                      </div>
                    </div>

                    <div style={{ overflowX: 'auto', marginTop: '1.5rem' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                          <tr style={{ backgroundColor: '#f7fafc' }}>
                            <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#4a5568', textTransform: 'uppercase' }}>
                              Medical Term
                            </th>
                            <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#4a5568', textTransform: 'uppercase' }}>
                              Mappings Found
                            </th>
                            <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#4a5568', textTransform: 'uppercase' }}>
                              Terminology Mappings
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {batchResults.map((result: MappingResponse, index: number) => (
                            <tr key={`${result.term}-${index}`} style={{ borderBottom: '1px solid #e2e8f0', minHeight: '3rem' }}>
                              <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#1a202c', fontWeight: '500', verticalAlign: 'middle' }}>
                                {result.term}
                              </td>
                              <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#4a5568', verticalAlign: 'middle', minHeight: '3rem' }}>
                                <span style={{ 
                                  backgroundColor: result.mappings.length > 0 ? '#48bb78' : '#ed8936', 
                                  color: 'white', 
                                  padding: '0.25rem 0.75rem', 
                                  borderRadius: '20px', 
                                  fontSize: '0.75rem', 
                                  fontWeight: '600',
                                  display: 'inline-block',
                                  whiteSpace: 'nowrap'
                                }}>
                                  {result.mappings.length} {result.mappings.length === 1 ? 'match' : 'matches'}
                                </span>
                              </td>
                              <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#4a5568', verticalAlign: 'middle' }}>
                                {result.mappings.length > 0 ? (
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                    {result.mappings.map((mapping, mappingIndex) => (
                                      <div key={mappingIndex} style={{ 
                                        padding: '0.75rem', 
                                        border: '1px solid #e2e8f0', 
                                        borderRadius: '6px',
                                        backgroundColor: mappingIndex === 0 ? '#f7fafc' : 'white'
                                      }}>
                                        <div style={{ marginBottom: '0.5rem' }}>
                                          <div style={{ fontWeight: '600', color: '#1a202c', marginBottom: '0.25rem' }}>
                                            {mapping.display}
                                            {mappingIndex === 0 && result.mappings.length > 1 && (
                                              <span style={{ 
                                                fontSize: '0.625rem', 
                                                color: '#667eea', 
                                                fontWeight: '500',
                                                marginLeft: '0.5rem',
                                                padding: '0.125rem 0.375rem',
                                                backgroundColor: '#e2e8f0',
                                                borderRadius: '4px'
                                              }}>
                                                BEST MATCH
                                              </span>
                                            )}
                                          </div>
                                          <div style={{ fontSize: '0.75rem', color: '#667eea' }}>
                                            {mapping.system.toUpperCase()}: {mapping.code}
                                          </div>
                                        </div>
                                        <div style={{ maxWidth: '200px' }}>
                                          <ConfidenceBar confidence={mapping.confidence} height="sm" showLabel={true} />
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <span style={{ color: '#a0aec0', fontStyle: 'italic' }}>No mapping found</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Documentation View */}
          {currentView === 'docs' && (
            <div className="form-container">
              <h1 className="form-title">
                Documentation
              </h1>
              <p className="form-description">
                Learn how to use the Medical Terminology Mapper effectively for standardizing healthcare data.
              </p>

              <div style={{ display: 'grid', gap: '2rem', marginTop: '2rem' }}>
                {/* Getting Started */}
                <div className="feature-card" style={{ cursor: 'default' }}>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1a202c', marginBottom: '1rem' }}>
                    🚀 Getting Started
                  </h2>
                  <p style={{ color: '#4a5568', marginBottom: '1rem' }}>
                    The Medical Terminology Mapper helps you convert medical terms into standardized codes from 
                    SNOMED CT, LOINC, and RxNorm terminologies.
                  </p>
                  <ul style={{ color: '#4a5568', paddingLeft: '1.5rem' }}>
                    <li><strong>Single Term Mapping</strong>: Map individual medical terms in real-time</li>
                    <li><strong>Batch Processing</strong>: Upload CSV files to process thousands of terms at once</li>
                    <li><strong>Multiple Systems</strong>: Get mappings across all major healthcare terminologies</li>
                  </ul>
                </div>

                {/* Single Term Guide */}
                <div className="feature-card" style={{ cursor: 'default' }}>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1a202c', marginBottom: '1rem' }}>
                    📋 Single Term Mapping
                  </h2>
                  <div style={{ color: '#4a5568' }}>
                    <p style={{ marginBottom: '1rem' }}>
                      Use the Single Term page to map individual medical terms:
                    </p>
                    <ol style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                      <li>Enter a medical term (e.g., "diabetes", "chest pain", "amoxicillin")</li>
                      <li>Select target terminology systems or choose "All Systems"</li>
                      <li>Click "Map Term" to get standardized codes</li>
                      <li>Review results with confidence scores and export if needed</li>
                    </ol>
                    <p><strong>Example terms to try:</strong> diabetes mellitus, hypertension, glucose test, insulin, pneumonia</p>
                  </div>
                </div>

                {/* Batch Processing Guide */}
                <div className="feature-card" style={{ cursor: 'default' }}>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1a202c', marginBottom: '1rem' }}>
                    📁 Batch Processing
                  </h2>
                  <div style={{ color: '#4a5568' }}>
                    <p style={{ marginBottom: '1rem' }}>
                      Process multiple terms efficiently with batch uploads:
                    </p>
                    <ol style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                      <li>Prepare a CSV file with medical terms in the first column</li>
                      <li>Upload your file or try one of our sample files</li>
                      <li>Monitor real-time progress as terms are processed</li>
                      <li>Download results in CSV or JSON format</li>
                    </ol>
                    <p><strong>CSV Format:</strong> Your file should have a header row with "term" as the column name.</p>
                  </div>
                </div>

                {/* Understanding Results */}
                <div className="feature-card" style={{ cursor: 'default' }}>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1a202c', marginBottom: '1rem' }}>
                    📊 Understanding Results
                  </h2>
                  <div style={{ color: '#4a5568' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#2d3748' }}>
                      Confidence Scores
                    </h3>
                    <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                      <li><span style={{ color: '#48bb78', fontWeight: '600' }}>🟢 High (80-100%)</span>: Excellent match, use with confidence</li>
                      <li><span style={{ color: '#ed8936', fontWeight: '600' }}>🟡 Medium (60-79%)</span>: Good match, review recommended</li>
                      <li><span style={{ color: '#e53e3e', fontWeight: '600' }}>🔴 Low (0-59%)</span>: Weak match, manual validation needed</li>
                    </ul>
                    
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#2d3748' }}>
                      Terminology Systems
                    </h3>
                    <ul style={{ paddingLeft: '1.5rem' }}>
                      <li><strong>SNOMED CT</strong>: Comprehensive clinical terminology for conditions, procedures</li>
                      <li><strong>LOINC</strong>: Laboratory observations and clinical measurements</li>
                      <li><strong>RxNorm</strong>: Standardized medication and drug nomenclature</li>
                    </ul>
                  </div>
                </div>

                {/* API Access */}
                <div className="feature-card" style={{ cursor: 'default' }}>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1a202c', marginBottom: '1rem' }}>
                    🔌 API Access
                  </h2>
                  <div style={{ color: '#4a5568' }}>
                    <p style={{ marginBottom: '1rem' }}>
                      Integrate the Medical Terminology Mapper into your applications:
                    </p>
                    <div style={{ background: '#f7fafc', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                      <p style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                        <strong>Interactive Documentation:</strong><br/>
                        <a href="http://localhost:8000/api/docs" target="_blank" rel="noopener noreferrer" style={{ color: '#667eea' }}>
                          http://localhost:8000/api/docs
                        </a>
                      </p>
                    </div>
                    <p>
                      Access comprehensive API documentation with interactive examples, request/response schemas, 
                      and testing capabilities.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-section">
            <h4 className="footer-title">Medical Terminology Mapper</h4>
            <p className="footer-description">
              Transforming medical terms into standardized terminologies with precision and reliability.
            </p>
          </div>
          
          <div className="footer-section">
            <h4 className="footer-title">Supported Standards</h4>
            <ul className="footer-list">
              <li>SNOMED CT - Clinical terminology</li>
              <li>LOINC - Laboratory observations</li>
              <li>RxNorm - Medication nomenclature</li>
            </ul>
          </div>
          
          <div className="footer-section">
            <h4 className="footer-title">Features</h4>
            <ul className="footer-list">
              <li>Single term mapping</li>
              <li>Batch file processing</li>
              <li>Fuzzy matching algorithms</li>
              <li>Export to CSV/JSON</li>
            </ul>
          </div>
        </div>
        
        <div className="footer-bottom">
          <p>&copy; 2025 Medical Terminology Mapper. Built for healthcare data standardization.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;