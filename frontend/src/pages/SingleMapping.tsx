import { useState } from 'react';
import { SingleTermForm } from '../components/TermMapper/SingleTermForm';
import { MappingResults } from '../components/TermMapper/MappingResults';
import type { MappingResponse } from '../types';

export const SingleMapping = () => {
  const [results, setResults] = useState<MappingResponse | null>(null);

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Single Term Mapping
      </h1>
      
      <SingleTermForm onSubmit={setResults} />
      
      {results && <MappingResults results={results} />}
    </div>
  );
};