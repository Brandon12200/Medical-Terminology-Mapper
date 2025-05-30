import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MappingResults } from './MappingResults';
import * as exportUtils from '../../utils/exportUtils';

// Mock export utilities
vi.mock('../../utils/exportUtils', () => ({
  exportToCSV: vi.fn(),
  exportToJSON: vi.fn(),
}));

describe('MappingResults', () => {
  const mockResults = {
    term: 'hypertension',
    mappings: [
      {
        system: 'snomed',
        code: '38341003',
        display: 'Hypertension (disorder)',
        confidence: 0.95,
        match_type: 'exact',
      },
      {
        system: 'icd10',
        code: 'I10',
        display: 'Essential hypertension',
        confidence: 0.75,
        match_type: 'fuzzy',
      },
    ],
  };

  it('renders nothing when no results provided', () => {
    const { container } = render(<MappingResults results={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('displays term and mappings correctly', () => {
    render(<MappingResults results={mockResults} />);

    expect(screen.getByText(/Results for: "hypertension"/)).toBeInTheDocument();
    expect(screen.getByText('Hypertension (disorder)')).toBeInTheDocument();
    expect(screen.getByText('Code: 38341003')).toBeInTheDocument();
    expect(screen.getByText('95% match')).toBeInTheDocument();
    expect(screen.getByText('exact')).toBeInTheDocument();
  });

  it('shows message when no mappings found', () => {
    const emptyResults = { term: 'unknown', mappings: [] };
    render(<MappingResults results={emptyResults} />);

    expect(screen.getByText('No mappings found for this term.')).toBeInTheDocument();
  });

  it('displays confidence bars', () => {
    render(<MappingResults results={mockResults} />);

    // Check for confidence score labels
    const confidenceLabels = screen.getAllByText('Confidence Score');
    expect(confidenceLabels).toHaveLength(2);
  });

  it('exports to CSV when button clicked', () => {
    render(<MappingResults results={mockResults} />);

    const csvButton = screen.getByText('Export CSV');
    fireEvent.click(csvButton);

    expect(exportUtils.exportToCSV).toHaveBeenCalledWith(
      mockResults,
      expect.stringContaining('mapping_hypertension_')
    );
  });

  it('exports to JSON when button clicked', () => {
    render(<MappingResults results={mockResults} />);

    const jsonButton = screen.getByText('Export JSON');
    fireEvent.click(jsonButton);

    expect(exportUtils.exportToJSON).toHaveBeenCalledWith(
      mockResults,
      expect.stringContaining('mapping_hypertension_')
    );
  });

  it('does not show export buttons when no mappings', () => {
    const emptyResults = { term: 'unknown', mappings: [] };
    render(<MappingResults results={emptyResults} />);

    expect(screen.queryByText('Export CSV')).not.toBeInTheDocument();
    expect(screen.queryByText('Export JSON')).not.toBeInTheDocument();
  });

  it('applies correct confidence color classes', () => {
    const multiConfidenceResults = {
      term: 'test',
      mappings: [
        { ...mockResults.mappings[0], confidence: 0.95 }, // High (green)
        { ...mockResults.mappings[0], confidence: 0.75 }, // Medium (yellow)
        { ...mockResults.mappings[0], confidence: 0.45 }, // Low (orange)
      ],
    };

    render(<MappingResults results={multiConfidenceResults} />);

    expect(screen.getByText('95% match')).toHaveClass('text-green-600');
    expect(screen.getByText('75% match')).toHaveClass('text-yellow-600');
    expect(screen.getByText('45% match')).toHaveClass('text-orange-600');
  });
});