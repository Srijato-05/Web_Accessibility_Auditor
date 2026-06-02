import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ScanScreen from '../pages/ScanScreen.tsx';

// Setup router mock
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate
}));

// Setup API client mock
const mockPost = vi.fn();
vi.mock('../api/client.ts', () => ({
  client: {
    post: (...args: any[]) => mockPost(...args),
    defaults: { baseURL: 'http://localhost:8000/api' }
  }
}));

describe('ScanScreen Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders standard scan options correctly', () => {
    render(<ScanScreen />);
    expect(screen.getByText('Target Initializer')).toBeInTheDocument();
    expect(screen.getByLabelText(/Target Website URL/i)).toBeInTheDocument();
    expect(screen.getByText('Single Page Scan')).toBeInTheDocument();
    expect(screen.getByText('Multi-Page Deep Scan')).toBeInTheDocument();
  });

  it('toggles deep scan controls dynamically', () => {
    render(<ScanScreen />);
    
    // Crawl Depth Boundaries slider should not be visible by default (single page scan selected)
    expect(screen.queryByLabelText(/Crawl Depth Boundaries/i)).not.toBeInTheDocument();

    // Click Multi-Page Deep Scan
    const multiRadio = screen.getByLabelText(/Multi-Page Deep Scan/i);
    fireEvent.click(multiRadio);

    // Depth limit control should now be visible
    expect(screen.getByText(/Crawl Depth Boundaries/i)).toBeInTheDocument();
  });

  it('submits selected parameters to the scans API endpoint', async () => {
    mockPost.mockResolvedValue({ data: { id: 'test-session-uuid', status: 'started' } });

    render(<ScanScreen />);

    const urlInput = screen.getByLabelText(/Target Website URL/i);
    fireEvent.change(urlInput, { target: { value: 'https://steamunlocked.net' } });

    // Select different agent persona
    const agentSelector = screen.getByLabelText(/Secure Auditor Bot/i);
    fireEvent.click(agentSelector);

    // Submit form
    const form = screen.getByRole('button', { name: /Trigger Heuristic Scan/i });
    fireEvent.click(form);

    // Expect loading overlay to show
    expect(screen.getByText(/Telemetry Analysis Stream/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/scans', expect.objectContaining({
        url: 'https://steamunlocked.net',
        agent: 'secure_auditor'
      }));
      expect(mockNavigate).toHaveBeenCalledWith('/reports/test-session-uuid');
    });
  });
});
