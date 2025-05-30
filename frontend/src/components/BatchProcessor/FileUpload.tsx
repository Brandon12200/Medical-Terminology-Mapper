import { useCallback, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { mappingService } from '../../services/mappingService';
import { ErrorAlert } from '../common/ErrorAlert';
import { TestFilesList } from './TestFilesList';

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

  const handleTestFileSelect = (file: File) => {
    uploadMutation.mutate(file);
  };

  return (
    <div className="w-full">
      <div
        className={`relative border-2 border-dashed rounded-lg p-6 ${
          dragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          className="sr-only"
          accept=".csv"
          onChange={handleFileInput}
          disabled={uploadMutation.isPending}
        />
        <label
          htmlFor="file-upload"
          className="cursor-pointer flex flex-col items-center"
        >
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
            aria-hidden="true"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <p className="mt-2 text-sm text-gray-600">
            <span className="font-medium text-blue-600 hover:text-blue-500">
              Click to upload
            </span>{' '}
            or drag and drop
          </p>
          <p className="text-xs text-gray-500">CSV files only</p>
        </label>
      </div>

      {uploadMutation.isError && (
        <div className="mt-4">
          <ErrorAlert message={uploadMutation.error?.message || 'Upload failed'} />
        </div>
      )}

      {uploadMutation.isPending && (
        <div className="mt-4 text-center text-sm text-gray-600">
          Uploading file...
        </div>
      )}

      <TestFilesList onFileSelect={handleTestFileSelect} />
    </div>
  );
};