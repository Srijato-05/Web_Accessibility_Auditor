import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import BatchAudit from './BatchAudit';
import { client } from '../api/client';
import { BrowserRouter } from 'react-router-dom';
import * as fc from 'fast-check'; // Property based testing for JS/TS

// Complex mocking of API interactions
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

describe('Advanced Dynamic Frontend Resiliency (BatchAudit)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maintains stability when API returns massive, randomized payload distributions', async () => {
    // We use fast-check to generate complex arbitrary objects simulating corrupt/extreme API responses
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.record({
            id: fc.integer(),
            url: fc.webUrl(),
            status: fc.constantFrom('pending', 'running', 'completed', 'failed', 'unknown'),
            updated_at: fc.date().map((d: Date) => d.toISOString()),
            priority: fc.integer({ min: -100, max: 100 })
          }),
          { maxLength: 500 } // Simulate large grids
        ),
        async (mockTargets: any[]) => {
          (client.get as any).mockImplementation((url: string) => {
            if (url === '/targets') return Promise.resolve({ data: mockTargets });
            if (url === '/batch/status') return Promise.resolve({ data: { status: 'idle', total_targets: mockTargets.length } });
            return Promise.resolve({ data: {} });
          });

          const { unmount } = renderWithRouter(<BatchAudit />);
          
          // Should not crash, title should exist
          expect(await screen.findByText('Batch Audit Surveillance')).toBeInTheDocument();
          
          unmount();
        }
      ),
      { numRuns: 10 } // Execute property check 10 times with different massive arrays
    );
  });

  it('gracefully isolates unhandled promise rejections and 500 responses on row deletion', async () => {
    // Setup initial state with 1 valid target
    const target = { id: 1, url: 'https://test.com', status: 'completed', updated_at: new Date().toISOString() };
    
    (client.get as any).mockImplementation((url: string) => {
      if (url === '/targets') return Promise.resolve({ data: [target] });
      if (url === '/batch/status') return Promise.resolve({ data: { status: 'idle', total_targets: 1 } });
      return Promise.resolve({ data: {} });
    });

    renderWithRouter(<BatchAudit />);
    
    // Wait for row to appear
    await waitFor(() => {
      expect(screen.getByText('https://test.com')).toBeInTheDocument();
    });

    // Mock delete to throw a severe 500 error
    (client.delete as any).mockRejectedValueOnce(new Error('Internal Server Error 500'));

    // Find and click delete button (assuming trash icon has aria-label or title 'Delete')
    const deleteBtn = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteBtn);

    // The UI should NOT crash. It should either show a toast/error or just remain stable.
    await waitFor(() => {
      // The row should still exist because deletion failed
      expect(screen.getByText('https://test.com')).toBeInTheDocument();
    });
  });

  it('debounces rapid sequential clicks on batch execution buttons to prevent race conditions', async () => {
    (client.get as any).mockImplementation(() => Promise.resolve({ data: [] }));
    (client.post as any).mockResolvedValue({ data: { status: 'started' } });

    renderWithRouter(<BatchAudit />);
    
    const runBtn = await screen.findByText(/Run Local Batch/i);
    
    // Simulate user spamming the button 5 times very fast
    for(let i=0; i<5; i++) {
        fireEvent.click(runBtn);
    }
    
    await waitFor(() => {
        // Post should only have been called ONCE due to loading state disabling the button
        expect(client.post).toHaveBeenCalledTimes(1);
    });
  });

  it('strictly validates URL formats client-side before dispatching network requests', async () => {
    (client.get as any).mockImplementation(() => Promise.resolve({ data: [] }));
    (client.post as any).mockResolvedValue({ data: { status: 'success' } });

    renderWithRouter(<BatchAudit />);
    
    const input = await screen.findByPlaceholderText('https://example.com');
    const addBtn = screen.getByText('Add Target');
    
    // Inject XSS payload as URL
    fireEvent.change(input, { target: { value: 'javascript:alert(1)' } });
    fireEvent.click(addBtn);
    
    // Wait to see if error message appears or post is NOT called
    await waitFor(() => {
      expect(client.post).not.toHaveBeenCalled();
    });
    
    // Inject random text
    fireEvent.change(input, { target: { value: 'not-a-url' } });
    fireEvent.click(addBtn);
    
    await waitFor(() => {
      expect(client.post).not.toHaveBeenCalled();
    });
    
    // Valid URL
    fireEvent.change(input, { target: { value: 'https://valid.com' } });
    fireEvent.click(addBtn);
    
    await waitFor(() => {
      expect(client.post).toHaveBeenCalledWith('/targets', expect.objectContaining({ url: 'https://valid.com' }));
    });
  });
});
