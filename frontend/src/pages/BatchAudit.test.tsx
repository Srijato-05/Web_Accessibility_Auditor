import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import BatchAudit from './BatchAudit';
import { client } from '../api/client';
import { BrowserRouter } from 'react-router-dom';

// Mock the API client
vi.mock('../api/client', () => ({
  client: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    defaults: { baseURL: 'http://localhost:8000' }
  }
}));

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('BatchAudit Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the dashboard header and action buttons', async () => {
    // Mock successful fetch of empty targets and status
    (client.get as any).mockImplementation((url: string) => {
      if (url === '/targets') return Promise.resolve({ data: [] });
      if (url === '/batch/status') return Promise.resolve({ data: { status: 'idle', total_targets: 0 } });
      return Promise.resolve({ data: {} });
    });

    renderWithRouter(<BatchAudit />);
    
    // Check header
    expect(screen.getByText('Batch Audit Surveillance')).toBeInTheDocument();
    
    // Check buttons
    expect(screen.getByText(/Export CSV Summary/i)).toBeInTheDocument();
    expect(screen.getByText(/Export Violations Detail/i)).toBeInTheDocument();
    expect(screen.getByText(/Run Local Batch/i)).toBeInTheDocument();
  });

  it('handles API failure gracefully and shows error message', async () => {
    (client.get as any).mockRejectedValueOnce(new Error('Network Error'));
    
    renderWithRouter(<BatchAudit />);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to load targets/i)).toBeInTheDocument();
    });
  });

  it('triggers batch export downloads correctly', async () => {
    (client.get as any).mockImplementation(() => Promise.resolve({ data: [] }));
    
    // Mock window.open
    const originalOpen = window.open;
    window.open = vi.fn();

    renderWithRouter(<BatchAudit />);
    
    const exportBtn = screen.getByText(/Export CSV Summary/i);
    fireEvent.click(exportBtn);
    
    expect(window.open).toHaveBeenCalledWith('http://localhost:8000/batch/export/csv', '_blank');
    
    const detailBtn = screen.getByText(/Export Violations Detail/i);
    fireEvent.click(detailBtn);
    
    expect(window.open).toHaveBeenCalledWith('http://localhost:8000/batch/export/violations/csv', '_blank');
    
    // Restore window.open
    window.open = originalOpen;
  });

  it('handles target creation flow', async () => {
    (client.get as any).mockImplementation(() => Promise.resolve({ data: [] }));
    (client.post as any).mockResolvedValueOnce({ data: { status: 'success' } });
    
    renderWithRouter(<BatchAudit />);
    
    const input = screen.getByPlaceholderText('https://example.com');
    fireEvent.change(input, { target: { value: 'https://test.com' } });
    
    const addBtn = screen.getByText('Add Target');
    fireEvent.click(addBtn);
    
    await waitFor(() => {
      expect(client.post).toHaveBeenCalledWith('/targets', expect.objectContaining({
        url: 'https://test.com'
      }));
    });
  });
});
