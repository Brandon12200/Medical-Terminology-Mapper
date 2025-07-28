import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { mappingService } from '../../services/mappingService';
import type { MappingRequest } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';

interface SingleTermFormProps {
  onSubmit: (data: any) => void;
}

export const SingleTermForm = ({ onSubmit }: SingleTermFormProps) => {
  const [formData, setFormData] = useState<MappingRequest>({
    term: '',
    systems: ['all'],
    context: '',
    fuzzy_threshold: 0.8,
  });

  const { data: systems } = useQuery({
    queryKey: ['systems'],
    queryFn: mappingService.getSystems,
  });

  const mutation = useMutation({
    mutationFn: mappingService.mapTerm,
    onSuccess: (data) => {
      onSubmit(data);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.term.trim()) {
      mutation.mutate(formData);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'fuzzy_threshold' 
        ? parseFloat(value) 
        : name === 'systems' 
          ? [value] 
          : value,
    }));
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="term" className="form-label">
          Medical Term
        </label>
        <input
          type="text"
          name="term"
          id="term"
          value={formData.term}
          onChange={handleChange}
          className="form-input"
          placeholder="e.g., diabetes mellitus type 2"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="systems" className="form-label">
          Terminology System
        </label>
        <select
          name="systems"
          id="systems"
          value={formData.systems[0]}
          onChange={handleChange}
          className="form-select"
        >
          <option value="all">All Systems</option>
          {systems && Array.isArray(systems) && systems.map(system => (
            <option key={system.name} value={system.name}>
              {system.display_name}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="context" className="form-label">
          Clinical Context (Optional)
        </label>
        <input
          type="text"
          name="context"
          id="context"
          value={formData.context}
          onChange={handleChange}
          className="form-input"
          placeholder="e.g., endocrine disorder"
        />
      </div>

      <div className="form-group">
        <label htmlFor="fuzzy_threshold" className="form-label">
          Fuzzy Match Threshold
        </label>
        <input
          type="number"
          name="fuzzy_threshold"
          id="fuzzy_threshold"
          min="0"
          max="1"
          step="0.1"
          value={formData.fuzzy_threshold}
          onChange={handleChange}
          className="form-input"
        />
      </div>

      {mutation.isError && (
        <ErrorAlert message={mutation.error?.message || 'An error occurred'} />
      )}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="btn btn-primary"
        style={{ width: '100%' }}
      >
        {mutation.isPending ? <LoadingSpinner /> : 'Map Term'}
      </button>
    </form>
  );
};