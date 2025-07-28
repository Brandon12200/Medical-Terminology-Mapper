import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';
import { FileUpload } from '../components/BatchProcessor/FileUpload';
import { ProcessingStatus } from '../components/BatchProcessor/ProcessingStatus';
import { mappingService } from '../services/mappingService';
import { exportToCSV, exportToJSON } from '../utils/exportUtils';
import { ConfidenceBar } from '../components/common/ConfidenceBar';
import type { MappingResponse } from '../types';

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

export const BatchMapping = () => {
  const [jobId, setJobId] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const location = useLocation();

  // Reset batch state when navigating to /batch route with reset parameter
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    if (urlParams.get('reset') === 'true') {
      setJobId(null);
      setIsComplete(false);
      setIsProcessing(false);
      // Clean up URL parameter
      window.history.replaceState({}, '', '/batch');
    }
  }, [location.search]);

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
      console.log('Processing sample file:', filename);
      const response = await fetch(`http://localhost:8000/api/v1/test-files/${filename}`);
      if (!response.ok) throw new Error('File not found');
      
      console.log('File downloaded successfully');
      const blob = await response.blob();
      const file = new File([blob], filename, { type: 'text/csv' });
      
      console.log('Uploading file to batch service');
      const uploadResponse = await mappingService.uploadFile(file);
      console.log('Upload response:', uploadResponse);
      
      handleUploadSuccess(uploadResponse.job_id);
      console.log('Processing started with job ID:', uploadResponse.job_id);
    } catch (error) {
      console.error('Processing failed:', error);
      alert('Processing failed. Please try again.');
    }
  };

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
          <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.07)', marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', color: '#1a202c' }}>
              📤 Upload Your Own CSV File
            </h2>
            <p style={{ color: '#4a5568', marginBottom: '1rem' }}>
              Upload a CSV file with medical terms in the first column. Our system will automatically 
              map each term to standardized terminologies and provide detailed results.
            </p>
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          </div>

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

      {jobId && isProcessing && (
        <ProcessingStatus jobId={jobId} onComplete={handleProcessingComplete} />
      )}

      {isComplete && results && (
        <div className="results-container">
          <div className="result-card">
            <div className="result-header">
              <h2 className="result-term">
                🎉 Batch Processing Complete - {results.length} terms processed
              </h2>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => downloadResults('csv')}
                  className="btn btn-secondary"
                >
                  Download CSV
                </button>
                <button
                  onClick={() => downloadResults('json')}
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
                  {results.map((result: MappingResponse, index: number) => {
                    return (
                      <tr key={index} style={{ borderBottom: '1px solid #e2e8f0', minHeight: '3rem' }}>
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
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};