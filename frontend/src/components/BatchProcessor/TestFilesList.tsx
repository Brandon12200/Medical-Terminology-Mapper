import { useQuery } from '@tanstack/react-query';
import { mappingService, TestFile } from '../../services/mappingService';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';

interface TestFilesListProps {
  onFileSelect: (file: File) => void;
}

export const TestFilesList = ({ onFileSelect }: TestFilesListProps) => {
  const { data: testFiles, isLoading, error } = useQuery({
    queryKey: ['testFiles'],
    queryFn: mappingService.getTestFiles,
  });

  const handleDownloadAndSelect = async (testFile: TestFile) => {
    try {
      const blob = await mappingService.downloadTestFile(testFile.filename);
      const file = new File([blob], testFile.filename, { type: 'text/csv' });
      onFileSelect(file);
    } catch (error) {
      console.error('Error downloading test file:', error);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return Math.round(bytes / 1024) + ' KB';
    else return Math.round(bytes / 1048576) + ' MB';
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message="Failed to load test files" />;

  return (
    <div className="mt-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Or try with sample files:
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {testFiles?.map((file) => (
          <div
            key={file.filename}
            className="border rounded-lg p-4 hover:border-blue-500 hover:bg-blue-50 cursor-pointer transition-colors"
            onClick={() => handleDownloadAndSelect(file)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900">{file.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{file.description}</p>
                <p className="text-xs text-gray-500 mt-2">
                  {formatFileSize(file.size)} • Click to use
                </p>
              </div>
              <svg
                className="w-5 h-5 text-gray-400 ml-2 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"
                />
              </svg>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};