import React, { useCallback, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ErrorAlert } from '../common/ErrorAlert';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface BatchFileUploadProps {
  onUploadSuccess: (batchId: string) => void;
}

interface FileWithId {
  id: string;
  file: File;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

export const BatchFileUpload = ({ onUploadSuccess }: BatchFileUploadProps) => {
  const [files, setFiles] = useState<FileWithId[]>([]);
  const [dragActive, setDragActive] = useState(false);

  const uploadMutation = useMutation({
    mutationFn: async (files: File[]) => {
      const formData = new FormData();
      files.forEach((file, index) => {
        formData.append(`files`, file);
      });
      
      const response = await fetch('/api/v1/documents/batch/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      
      return response.json();
    },
    onSuccess: (data) => {
      onUploadSuccess(data.batch_id);
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

    if (e.dataTransfer.files) {
      const newFiles = Array.from(e.dataTransfer.files)
        .filter(file => isValidFileType(file))
        .map(file => ({
          id: Math.random().toString(36).substr(2, 9),
          file,
          status: 'pending' as const
        }));
      
      setFiles(prev => [...prev, ...newFiles]);
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files)
        .filter(file => isValidFileType(file))
        .map(file => ({
          id: Math.random().toString(36).substr(2, 9),
          file,
          status: 'pending' as const
        }));
      
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const isValidFileType = (file: File): boolean => {
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain',
      'text/rtf',
      'application/rtf'
    ];
    return validTypes.includes(file.type) || 
           file.name.toLowerCase().endsWith('.pdf') ||
           file.name.toLowerCase().endsWith('.docx') ||
           file.name.toLowerCase().endsWith('.doc') ||
           file.name.toLowerCase().endsWith('.txt') ||
           file.name.toLowerCase().endsWith('.rtf');
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const uploadFiles = () => {
    if (files.length === 0) return;
    const fileList = files.map(f => f.file);
    uploadMutation.mutate(fileList);
  };

  const clearFiles = () => {
    setFiles([]);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="w-full space-y-4">
      {/* Drop Zone */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 transition-colors ${
          dragActive 
            ? 'border-blue-400 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="batch-file-upload"
          className="sr-only"
          accept=".pdf,.docx,.doc,.txt,.rtf"
          multiple
          onChange={handleFileInput}
          disabled={uploadMutation.isPending}
        />
        <label
          htmlFor="batch-file-upload"
          className="cursor-pointer flex flex-col items-center"
        >
          <svg
            className="mx-auto h-16 w-16 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="mt-4 text-lg text-gray-600">
            <span className="font-medium text-blue-600 hover:text-blue-500">
              Click to select files
            </span>{' '}
            or drag and drop
          </p>
          <p className="mt-2 text-sm text-gray-500">
            PDF, DOCX, DOC, TXT, RTF files supported
          </p>
          <p className="text-xs text-gray-400">
            Multiple files allowed - select all documents for your batch
          </p>
        </label>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Selected Files ({files.length})
            </h3>
            <div className="space-x-2">
              <button
                onClick={clearFiles}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
                disabled={uploadMutation.isPending}
              >
                Clear All
              </button>
              <button
                onClick={uploadFiles}
                disabled={uploadMutation.isPending || files.length === 0}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploadMutation.isPending ? (
                  <div className="flex items-center">
                    <LoadingSpinner size="sm" />
                    <span className="ml-2">Uploading...</span>
                  </div>
                ) : (
                  'Upload Batch'
                )}
              </button>
            </div>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {files.map((fileItem) => (
              <div
                key={fileItem.id}
                className="flex items-center justify-between p-3 bg-white rounded border"
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-8 w-8 text-gray-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {fileItem.file.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatFileSize(fileItem.file.size)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(fileItem.id)}
                  disabled={uploadMutation.isPending}
                  className="ml-3 p-1 text-gray-400 hover:text-red-600 disabled:opacity-50"
                >
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {uploadMutation.isError && (
        <ErrorAlert 
          message={uploadMutation.error?.message || 'Batch upload failed'} 
        />
      )}

      {/* Upload Guidelines */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">
          Batch Processing Guidelines
        </h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Upload multiple medical documents at once for batch processing</li>
          <li>• Supported formats: PDF, DOCX, DOC, TXT, RTF</li>
          <li>• Each document will be processed for medical entity extraction</li>
          <li>• You can monitor progress and download results when complete</li>
          <li>• Maximum file size: 50MB per document</li>
        </ul>
      </div>
    </div>
  );
};