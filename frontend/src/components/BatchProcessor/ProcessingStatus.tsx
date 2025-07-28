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
    <div style={{
      background: 'white',
      padding: '1.5rem',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
      border: '1px solid #e5e7eb'
    }}>
      <h3 style={{ 
        fontSize: '1.125rem', 
        fontWeight: '600', 
        color: '#374151',
        margin: '0 0 1rem 0'
      }}>
        Processing Status
      </h3>
      
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: '0.5rem',
          fontSize: '0.875rem',
          color: '#6b7280'
        }}>
          <span>Progress</span>
          <span>{status.processed_terms} / {status.total_terms} terms</span>
        </div>
        
        <div style={{
          width: '100%',
          height: '8px',
          backgroundColor: '#f3f4f6',
          borderRadius: '4px',
          overflow: 'hidden'
        }}>
          <div style={{
            height: '100%',
            backgroundColor: '#3b82f6',
            width: `${progress}%`,
            transition: 'width 0.3s ease',
            borderRadius: '4px'
          }} />
        </div>
      </div>

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '0.875rem'
      }}>
        <span style={{ color: '#6b7280' }}>Status:</span>
        <span style={{ 
          fontWeight: '500',
          color: status.status === 'completed' ? '#059669' : 
                status.status === 'failed' ? '#dc2626' : '#3b82f6'
        }}>
          {status.status.charAt(0).toUpperCase() + status.status.slice(1)}
        </span>
      </div>
    </div>
  );
};