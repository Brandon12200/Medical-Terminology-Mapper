import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AIExtraction from './AIExtraction';
import { mappingService } from '../services/mappingService';

// Mock the mapping service
vi.mock('../services/mappingService', () => ({
  mappingService: {
    getAIStatus: vi.fn(),
    extractAndMapTerms: vi.fn(),
    extractTermsOnly: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('AIExtraction', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock for AI status
    vi.mocked(mappingService.getAIStatus).mockResolvedValue({
      ai_enabled: true,
      model_info: {
        model_name: 'biobert-base-cased-v1.2',
        version: 'v1.0',
        device: 'cpu',
      },
    });
  });

  it('renders the AI extraction page', () => {
    render(<AIExtraction />, { wrapper: createWrapper() });
    
    expect(screen.getByText('AI-Powered Term Extraction')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Patient presents with/i)).toBeInTheDocument();
    expect(screen.getByText('Extract & Map Terms')).toBeInTheDocument();
    expect(screen.getByText('Extract Only')).toBeInTheDocument();
  });

  it('displays AI status when enabled', async () => {
    render(<AIExtraction />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText(/AI Status: Enabled/i)).toBeInTheDocument();
      expect(screen.getByText(/Model: biobert-base-cased-v1.2/i)).toBeInTheDocument();
    });
  });

  it('displays fallback status when AI is disabled', async () => {
    vi.mocked(mappingService.getAIStatus).mockResolvedValue({
      ai_enabled: false,
    });
    
    render(<AIExtraction />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText(/Using Fallback Pattern Matching/i)).toBeInTheDocument();
    });
  });

  it('extracts and maps terms when button is clicked', async () => {
    const mockResponse = {
      extracted_terms: [
        {
          text: 'diabetes',
          entity_type: 'CONDITION',
          start_char: 12,
          end_char: 20,
          confidence: 0.95,
          mappings: [
            {
              code: '73211009',
              display: 'Diabetes mellitus',
              system: 'snomed',
              confidence: 0.88,
            },
          ],
        },
      ],
    };
    
    vi.mocked(mappingService.extractAndMapTerms).mockResolvedValue(mockResponse);
    
    render(<AIExtraction />, { wrapper: createWrapper() });
    
    // Enter text
    const textarea = screen.getByPlaceholderText(/Patient presents with/i);
    fireEvent.change(textarea, { target: { value: 'Patient has diabetes' } });
    
    // Click extract button
    const extractButton = screen.getByText('Extract & Map Terms');
    fireEvent.click(extractButton);
    
    await waitFor(() => {
      expect(screen.getByText('diabetes')).toBeInTheDocument();
      expect(screen.getByText('Type: CONDITION')).toBeInTheDocument();
      expect(screen.getByText('Diabetes mellitus')).toBeInTheDocument();
      expect(screen.getByText('SNOMED: 73211009')).toBeInTheDocument();
    });
  });

  it('extracts terms only when extract only button is clicked', async () => {
    const mockResponse = {
      extracted_terms: [
        {
          text: 'hypertension',
          entity_type: 'CONDITION',
          start_char: 23,
          end_char: 35,
          confidence: 0.92,
        },
        {
          text: 'lisinopril',
          entity_type: 'MEDICATION',
          start_char: 48,
          end_char: 58,
          confidence: 0.89,
        },
      ],
    };
    
    vi.mocked(mappingService.extractTermsOnly).mockResolvedValue(mockResponse);
    
    render(<AIExtraction />, { wrapper: createWrapper() });
    
    // Enter text
    const textarea = screen.getByPlaceholderText(/Patient presents with/i);
    fireEvent.change(textarea, {
      target: { value: 'Patient diagnosed with hypertension, prescribed lisinopril' },
    });
    
    // Click extract only button
    const extractOnlyButton = screen.getByText('Extract Only');
    fireEvent.click(extractOnlyButton);
    
    await waitFor(() => {
      expect(screen.getByText('hypertension')).toBeInTheDocument();
      expect(screen.getByText('lisinopril')).toBeInTheDocument();
      expect(screen.queryByText('Mappings:')).not.toBeInTheDocument();
    });
  });

  it('displays sample text when sample button is clicked', () => {
    render(<AIExtraction />, { wrapper: createWrapper() });
    
    const diabetesButton = screen.getByText('Diabetes Sample');
    fireEvent.click(diabetesButton);
    
    const textarea = screen.getByPlaceholderText(/Patient presents with/i) as HTMLTextAreaElement;
    expect(textarea.value).toContain('diabetes mellitus');
    expect(textarea.value).toContain('HbA1c');
    expect(textarea.value).toContain('metformin');
  });

  it('disables buttons when no text is entered', () => {
    render(<AIExtraction />, { wrapper: createWrapper() });
    
    const extractButton = screen.getByText('Extract & Map Terms');
    const extractOnlyButton = screen.getByText('Extract Only');
    
    expect(extractButton).toBeDisabled();
    expect(extractOnlyButton).toBeDisabled();
    
    // Enter text
    const textarea = screen.getByPlaceholderText(/Patient presents with/i);
    fireEvent.change(textarea, { target: { value: 'Some text' } });
    
    expect(extractButton).not.toBeDisabled();
    expect(extractOnlyButton).not.toBeDisabled();
  });

  it('shows loading state during extraction', async () => {
    vi.mocked(mappingService.extractAndMapTerms).mockImplementation(
      () => new Promise(() => {}) // Never resolves to keep loading
    );
    
    render(<AIExtraction />, { wrapper: createWrapper() });
    
    // Enter text and click extract
    const textarea = screen.getByPlaceholderText(/Patient presents with/i);
    fireEvent.change(textarea, { target: { value: 'Patient has diabetes' } });
    
    const extractButton = screen.getByText('Extract & Map Terms');
    fireEvent.click(extractButton);
    
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    expect(extractButton).toBeDisabled();
  });

  it('displays error message on extraction failure', async () => {
    const errorMessage = 'Failed to extract terms';
    vi.mocked(mappingService.extractAndMapTerms).mockRejectedValue(
      new Error(errorMessage)
    );
    
    render(<AIExtraction />, { wrapper: createWrapper() });
    
    // Enter text and click extract
    const textarea = screen.getByPlaceholderText(/Patient presents with/i);
    fireEvent.change(textarea, { target: { value: 'Patient has diabetes' } });
    
    const extractButton = screen.getByText('Extract & Map Terms');
    fireEvent.click(extractButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Error: Failed to extract terms/i)).toBeInTheDocument();
    });
  });

  it('allows selecting different terminology systems', () => {
    render(<AIExtraction />, { wrapper: createWrapper() });
    
    const systemSelect = screen.getByRole('combobox');
    expect(systemSelect).toHaveValue('all');
    
    fireEvent.change(systemSelect, { target: { value: 'snomed' } });
    expect(systemSelect).toHaveValue('snomed');
    
    fireEvent.change(systemSelect, { target: { value: 'loinc' } });
    expect(systemSelect).toHaveValue('loinc');
    
    fireEvent.change(systemSelect, { target: { value: 'rxnorm' } });
    expect(systemSelect).toHaveValue('rxnorm');
  });

  it('displays confidence scores for extracted terms', async () => {
    const mockResponse = {
      extracted_terms: [
        {
          text: 'diabetes',
          entity_type: 'CONDITION',
          start_char: 12,
          end_char: 20,
          confidence: 0.95,
          mappings: [],
        },
      ],
    };
    
    vi.mocked(mappingService.extractAndMapTerms).mockResolvedValue(mockResponse);
    
    render(<AIExtraction />, { wrapper: createWrapper() });
    
    // Enter text and extract
    const textarea = screen.getByPlaceholderText(/Patient presents with/i);
    fireEvent.change(textarea, { target: { value: 'Patient has diabetes' } });
    
    const extractButton = screen.getByText('Extract & Map Terms');
    fireEvent.click(extractButton);
    
    await waitFor(() => {
      expect(screen.getByText('Confidence: 95.0%')).toBeInTheDocument();
    });
  });
});