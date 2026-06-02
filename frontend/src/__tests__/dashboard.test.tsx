import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Dashboard from '../pages/Dashboard.tsx';

// Setup router mock
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
  useNavigate: () => mockNavigate
}));

// Setup GraphView mock to avoid canvas drawing issues in jsdom
vi.mock('../components/GraphView.tsx', () => ({
  GraphView: () => <div data-testid="mock-graph-view">Mock Graph View</div>
}));

// Setup API client mock
const mockGet = vi.fn();
vi.mock('../api/client.ts', () => ({
  client: {
    get: (...args: any[]) => mockGet(...args),
    defaults: { baseURL: 'http://localhost:8000/api' }
  }
}));

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loader during summary fetch', async () => {
    mockGet.mockReturnValue(new Promise(() => {})); // Never resolves
    render(<Dashboard />);
    expect(screen.getByLabelText(/Loading Dashboard Data/i)).toBeInTheDocument();
  });

  it('renders dashboard values correctly once API returns data', async () => {
    const mockSummary = {
      health_score: 92,
      rating: 'A',
      issues: {
        critical: 2,
        major: 4,
        minor: 6
      },
      categories: {
        color_contrast: 10,
        aria_semantics: 5,
        keyboard_navigation: 0,
        structure: 20
      },
      agent_insights: {
        total_missions: 3,
        breakdown: {
          visual: 0,
          motor: 0,
          cognitive: 0,
          neural: 0
        }
      },
      recent_scans: [
        {
          id: 'uuid-1',
          url: 'https://youtube.com',
          score: 85,
          status: 'completed',
          date: '2026-06-02T12:00:00.000Z'
        },
        {
          id: 'uuid-2',
          url: 'https://github.com',
          score: 0,
          status: 'in_progress',
          date: '2026-06-02T12:05:00.000Z'
        }
      ]
    };

    mockGet.mockResolvedValue({ data: mockSummary });

    render(<Dashboard />);

    // Wait for the data to render
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    expect(screen.getByText('Missions')).toBeInTheDocument();
    expect(screen.getByTestId('severity-count-critical-errors').textContent).toContain('2 items');
    expect(screen.getByTestId('severity-count-major-disruptions').textContent).toContain('4 items');
    expect(screen.getByTestId('severity-count-minor-advisories').textContent).toContain('6 items');

    // Verify raw category violation counts are displayed correctly
    expect(screen.getByText('0')).toBeInTheDocument(); // Keyboard Navigation Violations
    expect(screen.getByText('10')).toBeInTheDocument(); // Contrast Violations
    expect(screen.getByText('5')).toBeInTheDocument(); // ARIA Semantics Violations
    expect(screen.getByText('20')).toBeInTheDocument(); // Structure Violations

    // Verify recent scans table displays items
    expect(screen.getByText('https://youtube.com')).toBeInTheDocument();
    expect(screen.getByText('https://github.com')).toBeInTheDocument();
  });

  it('triggers router navigation when New Scan is clicked', async () => {
    mockGet.mockResolvedValue({ data: { health_score: 100, rating: 'AAA', issues: { critical: 0, major: 0, minor: 0 }, agent_insights: { total_missions: 0 }, recent_scans: [] } });
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('New Scan')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('New Scan'));
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });
});
