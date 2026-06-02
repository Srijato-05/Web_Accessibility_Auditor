import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Audits from '../pages/Audits.tsx';

// Setup router mock
vi.mock('react-router-dom', () => ({
  Link: ({ children, to }: any) => <a href={to}>{children}</a>
}));

// Setup API client mock
const mockGet = vi.fn();
vi.mock('../api/client.ts', () => ({
  client: {
    get: (...args: any[]) => mockGet(...args),
    defaults: { baseURL: 'http://localhost:8000/api' }
  }
}));

describe('Audits Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading spinner initially', () => {
    mockGet.mockReturnValue(new Promise(() => {})); // Never resolves
    render(<Audits />);
    expect(screen.getByLabelText(/Decrypting ledger registry.../i)).toBeInTheDocument();
  });

  it('renders scans lists and filters correctly', async () => {
    const mockScans = [
      {
        id: 'scan-1',
        url: 'https://youtube.com',
        score: 87,
        status: 'completed',
        date: '2026-06-02T12:00:00.000Z'
      },
      {
        id: 'scan-2',
        url: 'https://github.com',
        score: 0,
        status: 'in_progress',
        date: '2026-06-02T12:10:00.000Z'
      },
      {
        id: 'scan-3',
        url: 'https://steamunlocked.net',
        score: 0,
        status: 'failed',
        date: '2026-06-02T12:20:00.000Z'
      }
    ];

    mockGet.mockResolvedValue({ data: { recent_scans: mockScans } });

    render(<Audits />);

    await waitFor(() => {
      expect(screen.getByText('https://youtube.com')).toBeInTheDocument();
    });

    expect(screen.getByText('https://github.com')).toBeInTheDocument();
    expect(screen.getByText('https://steamunlocked.net')).toBeInTheDocument();

    // Verify dynamic badges based on status and score
    // https://youtube.com: completed && score 87 -> AAA Certified
    expect(screen.getAllByText('AAA Certified')[0]).toBeInTheDocument();
    // https://github.com: in_progress -> In Progress
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    // https://steamunlocked.net: failed -> Failed
    expect(screen.getByText('Failed')).toBeInTheDocument();

    // Verify search functionality
    const searchInput = screen.getByPlaceholderText(/Search targets by domain/i);
    fireEvent.change(searchInput, { target: { value: 'github' } });

    expect(screen.queryByText('https://youtube.com')).not.toBeInTheDocument();
    expect(screen.getByText('https://github.com')).toBeInTheDocument();

    // Clear search and verify filters
    fireEvent.change(searchInput, { target: { value: '' } });
    
    // Filter by completed status
    const statusSelect = screen.getByRole('combobox');
    fireEvent.change(statusSelect, { target: { value: 'completed' } });

    expect(screen.getByText('https://youtube.com')).toBeInTheDocument();
    expect(screen.queryByText('https://github.com')).not.toBeInTheDocument();
  });
});
