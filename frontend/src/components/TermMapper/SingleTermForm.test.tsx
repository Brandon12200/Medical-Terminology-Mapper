import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SingleTermForm } from './SingleTermForm';
import { mappingService } from '../../services/mappingService';

// Mock the mapping service
vi.mock('../../services/mappingService', () => ({
  mappingService: {
    mapTerm: vi.fn(),
    getSystems: vi.fn(),
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

describe('SingleTermForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(mappingService.getSystems).mockResolvedValue([
      { name: 'snomed', display_name: 'SNOMED CT', description: 'Clinical terminology', total_concepts: 1000 },
      { name: 'loinc', display_name: 'LOINC', description: 'Lab observations', total_concepts: 500 },
    ]);
  });

  it('renders form elements correctly', async () => {
    const mockOnSubmit = vi.fn();
    render(<SingleTermForm onSubmit={mockOnSubmit} />, { wrapper: createWrapper() });

    expect(screen.getByLabelText(/medical term/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/terminology system/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/clinical context/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/fuzzy match threshold/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /map term/i })).toBeInTheDocument();
  });

  it('populates system dropdown with fetched data', async () => {
    const mockOnSubmit = vi.fn();
    render(<SingleTermForm onSubmit={mockOnSubmit} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('SNOMED CT')).toBeInTheDocument();
      expect(screen.getByText('LOINC')).toBeInTheDocument();
    });
  });

  it('submits form with correct data', async () => {
    const mockOnSubmit = vi.fn();
    const mockResponse = {
      term: 'diabetes',
      mappings: [
        {
          system: 'snomed',
          code: '73211009',
          display: 'Diabetes mellitus',
          confidence: 0.95,
        },
      ],
    };

    vi.mocked(mappingService.mapTerm).mockResolvedValue(mockResponse);

    const user = userEvent.setup();
    render(<SingleTermForm onSubmit={mockOnSubmit} />, { wrapper: createWrapper() });

    // Fill in the form
    const termInput = screen.getByLabelText(/medical term/i);
    await user.type(termInput, 'diabetes');

    const contextInput = screen.getByLabelText(/clinical context/i);
    await user.type(contextInput, 'endocrine');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /map term/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mappingService.mapTerm).toHaveBeenCalledWith({
        term: 'diabetes',
        system: 'all',
        context: 'endocrine',
        fuzzy_threshold: 0.8,
      });
      expect(mockOnSubmit).toHaveBeenCalledWith(mockResponse);
    });
  });

  it('disables submit button while loading', async () => {
    const mockOnSubmit = vi.fn();
    vi.mocked(mappingService.mapTerm).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    const user = userEvent.setup();
    render(<SingleTermForm onSubmit={mockOnSubmit} />, { wrapper: createWrapper() });

    const termInput = screen.getByLabelText(/medical term/i);
    await user.type(termInput, 'test');

    const submitButton = screen.getByRole('button', { name: /map term/i });
    await user.click(submitButton);

    expect(submitButton).toBeDisabled();
  });

  it('displays error message on API failure', async () => {
    const mockOnSubmit = vi.fn();
    vi.mocked(mappingService.mapTerm).mockRejectedValue(new Error('API Error'));

    const user = userEvent.setup();
    render(<SingleTermForm onSubmit={mockOnSubmit} />, { wrapper: createWrapper() });

    const termInput = screen.getByLabelText(/medical term/i);
    await user.type(termInput, 'test');

    const submitButton = screen.getByRole('button', { name: /map term/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/api error/i)).toBeInTheDocument();
    });
  });
});