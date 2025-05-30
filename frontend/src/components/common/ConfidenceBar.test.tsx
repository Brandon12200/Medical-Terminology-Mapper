import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConfidenceBar } from './ConfidenceBar';

describe('ConfidenceBar', () => {
  it('renders with correct percentage', () => {
    render(<ConfidenceBar confidence={0.85} />);
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('renders without label when showLabel is false', () => {
    render(<ConfidenceBar confidence={0.85} showLabel={false} />);
    expect(screen.queryByText('85%')).not.toBeInTheDocument();
  });

  it('applies correct color class for high confidence', () => {
    const { container } = render(<ConfidenceBar confidence={0.95} />);
    const bar = container.querySelector('.bg-green-500');
    expect(bar).toBeInTheDocument();
  });

  it('applies correct color class for medium-high confidence', () => {
    const { container } = render(<ConfidenceBar confidence={0.75} />);
    const bar = container.querySelector('.bg-yellow-500');
    expect(bar).toBeInTheDocument();
  });

  it('applies correct color class for medium confidence', () => {
    const { container } = render(<ConfidenceBar confidence={0.55} />);
    const bar = container.querySelector('.bg-orange-500');
    expect(bar).toBeInTheDocument();
  });

  it('applies correct color class for low confidence', () => {
    const { container } = render(<ConfidenceBar confidence={0.25} />);
    const bar = container.querySelector('.bg-red-500');
    expect(bar).toBeInTheDocument();
  });

  it('sets correct width based on confidence', () => {
    const { container } = render(<ConfidenceBar confidence={0.75} />);
    const bar = container.querySelector('[style*="width: 75%"]');
    expect(bar).toBeInTheDocument();
  });

  it('applies correct height class', () => {
    const { container: smallContainer } = render(<ConfidenceBar confidence={0.5} height="sm" />);
    expect(smallContainer.querySelector('.h-2')).toBeInTheDocument();

    const { container: mediumContainer } = render(<ConfidenceBar confidence={0.5} height="md" />);
    expect(mediumContainer.querySelector('.h-3')).toBeInTheDocument();

    const { container: largeContainer } = render(<ConfidenceBar confidence={0.5} height="lg" />);
    expect(largeContainer.querySelector('.h-4')).toBeInTheDocument();
  });

  it('rounds percentage correctly', () => {
    render(<ConfidenceBar confidence={0.894} />);
    expect(screen.getByText('89%')).toBeInTheDocument();

    render(<ConfidenceBar confidence={0.896} />);
    expect(screen.getByText('90%')).toBeInTheDocument();
  });
});