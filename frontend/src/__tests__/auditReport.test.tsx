import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import AuditReport from '../pages/AuditReport.tsx';

// Setup router mock
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useParams: () => ({ audit_id: 'test-report-uuid' }),
  useNavigate: () => mockNavigate
}));

// Setup API client mock
const mockGet = vi.fn();
vi.mock('../api/client.ts', () => ({
  client: {
    get: (...args: any[]) => mockGet(...args),
    defaults: { baseURL: 'http://localhost:8000/api' }
  }
}));

describe('AuditReport Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockReset();
  });

  it('renders scanning state console initially', async () => {
    mockGet.mockResolvedValue({
      data: {
        url: 'https://youtube.com',
        status: 'scanning'
      }
    });

    render(<AuditReport />);

    await waitFor(() => {
      expect(screen.getByText('Compliance Scanning Console')).toBeInTheDocument();
      expect(screen.getByText('Scanning Vector: https://youtube.com')).toBeInTheDocument();
      expect(screen.getByText('[CRAWLER] Traversing depth limits...')).toBeInTheDocument();
    });
  });

  it('navigates to insights page once status is completed', async () => {
    let intervalCb: any;
    const originalSetInterval = global.setInterval;
    const setIntervalSpy = vi.spyOn(global, 'setInterval').mockImplementation(((cb: any, ms: any) => {
      if (cb.name === 'checkStatus' || ms === 3000) {
        intervalCb = cb;
        return 123 as any;
      }
      return originalSetInterval(cb, ms);
    }) as any);

    // Initial fetch returns scanning
    mockGet.mockResolvedValue({
      data: {
        url: 'https://youtube.com',
        status: 'scanning'
      }
    });

    render(<AuditReport />);

    await waitFor(() => {
      expect(screen.getByText('Scanning Vector: https://youtube.com')).toBeInTheDocument();
    });

    // Next fetch returns completed
    mockGet.mockImplementation(() => {
      return Promise.resolve({
        data: {
          url: 'https://youtube.com',
          status: 'completed'
        }
      });
    });

    // Manually trigger the interval callback to check status again
    try {
      act(() => {
        intervalCb();
      });
    } catch (err: any) {
      // Ignored
    }

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/insights/test-report-uuid');
    });

    setIntervalSpy.mockRestore();
  });

  it('displays error details and stops polling once status is failed', async () => {
    let intervalCb: any;
    const originalSetInterval = global.setInterval;
    const setIntervalSpy = vi.spyOn(global, 'setInterval').mockImplementation(((cb: any, ms: any) => {
      if (cb.name === 'checkStatus' || ms === 3000) {
        intervalCb = cb;
        return 123 as any;
      }
      return originalSetInterval(cb, ms);
    }) as any);

    // Initial fetch returns scanning
    mockGet.mockResolvedValue({
      data: {
        url: 'https://youtube.com',
        status: 'scanning'
      }
    });

    render(<AuditReport />);

    await waitFor(() => {
      expect(screen.getByText('Scanning Vector: https://youtube.com')).toBeInTheDocument();
    });

    // Next fetch returns failed
    mockGet.mockResolvedValue({
      data: {
        url: 'https://youtube.com',
        status: 'failed',
        error_message: 'Browser process crashed unexpectedly.'
      }
    });

    // Manually trigger the interval callback to check status again
    try {
      act(() => {
        intervalCb();
      });
    } catch (err: any) {
      // Ignored
    }

    await waitFor(() => {
      expect(screen.getByText('Browser process crashed unexpectedly.')).toBeInTheDocument();
    });

    setIntervalSpy.mockRestore();
  });
});
