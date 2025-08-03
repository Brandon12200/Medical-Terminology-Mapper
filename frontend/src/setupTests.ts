import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock fetch for tests
global.fetch = vi.fn();

// Mock window functions
Object.defineProperty(window, 'open', {
  value: vi.fn(),
});

Object.defineProperty(URL, 'createObjectURL', {
  value: vi.fn(() => 'blob:mock-url'),
});

Object.defineProperty(URL, 'revokeObjectURL', {
  value: vi.fn(),
});