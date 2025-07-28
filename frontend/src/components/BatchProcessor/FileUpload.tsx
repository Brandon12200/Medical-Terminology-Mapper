import { useCallback, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { mappingService } from '../../services/mappingService';
import { ErrorAlert } from '../common/ErrorAlert';

interface FileUploadProps {
  onUploadSuccess: (jobId: string) => void;
}

export const FileUpload = ({ onUploadSuccess }: FileUploadProps) => {
  const [dragActive, setDragActive] = useState(false);

  const uploadMutation = useMutation({
    mutationFn: mappingService.uploadFile,
    onSuccess: (data) => {
      onUploadSuccess(data.job_id);
    },
  });

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        uploadMutation.mutate(file);
      }
    }
  }, [uploadMutation]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      uploadMutation.mutate(e.target.files[0]);
    }
  };

  return (
    <div>
      <div
        style={{
          position: 'relative',
          border: dragActive ? '2px dashed #667eea' : '2px dashed #e2e8f0',
          borderRadius: '8px',
          padding: '1.5rem',
          backgroundColor: dragActive ? '#f0f4f8' : 'transparent',
          textAlign: 'center',
          transition: 'all 0.2s'
        }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          style={{ display: 'none' }}
          accept=".csv"
          onChange={handleFileInput}
          disabled={uploadMutation.isPending}
        />
        <label
          htmlFor="file-upload"
          style={{ cursor: 'pointer', display: 'block' }}
        >
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📁</div>
          <p style={{ fontSize: '0.875rem', color: '#4a5568', marginBottom: '0.25rem' }}>
            <span style={{ color: '#667eea', fontWeight: '500' }}>Click to upload</span> or drag and drop your CSV file
          </p>
          <p style={{ fontSize: '0.75rem', color: '#718096' }}>CSV files only</p>
        </label>
      </div>

      {uploadMutation.isError && (
        <div style={{ marginTop: '1rem' }}>
          <ErrorAlert message={uploadMutation.error?.message || 'Upload failed'} />
        </div>
      )}

      {uploadMutation.isPending && (
        <div style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.875rem', color: '#4a5568' }}>
          <div className="spinner" style={{ margin: '0 auto 0.5rem', width: '20px', height: '20px' }}></div>
          Uploading file...
        </div>
      )}
    </div>
  );
};