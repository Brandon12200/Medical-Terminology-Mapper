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
    system: 'all',
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
      [name]: name === 'fuzzy_threshold' ? parseFloat(value) : value,
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 rounded-lg shadow">
      <div>
        <label htmlFor="term" className="block text-sm font-medium text-gray-700">
          Medical Term
        </label>
        <input
          type="text"
          name="term"
          id="term"
          value={formData.term}
          onChange={handleChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
          placeholder="e.g., diabetes mellitus type 2"
          required
        />
      </div>

      <div>
        <label htmlFor="system" className="block text-sm font-medium text-gray-700">
          Terminology System
        </label>
        <select
          name="system"
          id="system"
          value={formData.system}
          onChange={handleChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
        >
          <option value="all">All Systems</option>
          {systems?.map(system => (
            <option key={system.name} value={system.name}>
              {system.display_name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="context" className="block text-sm font-medium text-gray-700">
          Clinical Context (Optional)
        </label>
        <input
          type="text"
          name="context"
          id="context"
          value={formData.context}
          onChange={handleChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
          placeholder="e.g., endocrine disorder"
        />
      </div>

      <div>
        <label htmlFor="fuzzy_threshold" className="block text-sm font-medium text-gray-700">
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
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
        />
      </div>

      {mutation.isError && (
        <ErrorAlert message={mutation.error?.message || 'An error occurred'} />
      )}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {mutation.isPending ? <LoadingSpinner /> : 'Map Term'}
      </button>
    </form>
  );
};