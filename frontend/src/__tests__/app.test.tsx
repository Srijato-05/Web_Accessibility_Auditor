import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App.tsx';

// Setup API client mock
const mockGet = vi.fn();
vi.mock('../api/client.ts', () => ({
  client: {
    get: (...args: any[]) => mockGet(...args),
    defaults: { baseURL: 'http://localhost:8000/api' }
  }
}));

describe('App Component', () => {
  it('renders without crashing and defaults to the Scan Console page', () => {
    render(<App />);
    
    // Asserts main layout and Skip to Content link is present
    expect(screen.getByText('Skip to main content')).toBeInTheDocument();
    
    // Sidebar should be loaded
    expect(screen.getByText('Sentinel')).toBeInTheDocument();
    expect(screen.getByText('A11yAudit')).toBeInTheDocument();

    // Default route element ScanScreen should be loaded
    expect(screen.getByText('Target Initializer')).toBeInTheDocument();
  });
});
