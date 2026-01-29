import '@testing-library/jest-dom';

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    readText: jest.fn(),
    writeText: jest.fn(),
  },
});

// Mock fetch
global.fetch = jest.fn();
