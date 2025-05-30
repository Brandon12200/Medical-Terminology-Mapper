import '@testing-library/jest-dom';

// Mock fetch for tests
global.fetch = jest.fn();

// Mock window functions
Object.defineProperty(window, 'open', {
  value: jest.fn(),
});

Object.defineProperty(URL, 'createObjectURL', {
  value: jest.fn(() => 'blob:mock-url'),
});

Object.defineProperty(URL, 'revokeObjectURL', {
  value: jest.fn(),
});