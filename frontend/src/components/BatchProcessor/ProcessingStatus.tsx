import { useQuery } from '@tanstack/react-query';
import { mappingService } from '../../services/mappingService';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface ProcessingStatusProps {
  jobId: string;
  onComplete: () => void;
}

export const ProcessingStatus = ({ jobId, onComplete }: ProcessingStatusProps) => {
  const { data: status } = useQuery({
    queryKey: ['batchStatus', jobId],
    queryFn: () => mappingService.getBatchStatus(jobId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'failed') {
        onComplete();
        return false;
      }
      return 1000; // Poll every second
    },
  });

  if (!status) {
    return <LoadingSpinner />;
  }

  const progress = status.total_terms > 0 
    ? (status.processed_terms / status.total_terms) * 100 
    : 0;

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Processing Status</h3>
      
      <div className="space-y-4">
        <div>
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{status.processed_terms} / {status.total_terms} terms</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Status:</span>
          <span className={`text-sm font-medium ${
            status.status === 'completed' ? 'text-green-600' :
            status.status === 'failed' ? 'text-red-600' :
            'text-blue-600'
          }`}>
            {status.status.charAt(0).toUpperCase() + status.status.slice(1)}
          </span>
        </div>

        {status.status === 'processing' && <LoadingSpinner />}
      </div>
    </div>
  );
};