import { useState } from 'react';
import { SingleTermForm } from '../components/TermMapper/SingleTermForm';
import { MappingResults } from '../components/TermMapper/MappingResults';
import type { MappingResponse } from '../types';

export const SingleMapping = () => {
  const [results, setResults] = useState<MappingResponse | null>(null);

  return (
    <div className="form-container">
      <h1 className="form-title">
        Single Term Mapping
      </h1>
      <p className="form-description">
        Enter a medical term below to find its standardized mappings across SNOMED CT, LOINC, and RxNorm terminologies.
      </p>
      
      <SingleTermForm onSubmit={setResults} />
      
      {results && <MappingResults results={results} />}
    </div>
  );
};