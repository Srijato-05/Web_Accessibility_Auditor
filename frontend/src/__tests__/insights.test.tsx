import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Insights from '../pages/Insights.tsx';

// Setup router mock
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
  useParams: () => ({ audit_id: 'test-audit-uuid' }),
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

describe('Insights Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading initially', () => {
    mockGet.mockReturnValue(new Promise(() => {})); // Never resolves
    render(<Insights />);
    expect(screen.getByLabelText(/Parsing heuristic findings.../i)).toBeInTheDocument();
  });

  it('renders insights details once data is fetched', async () => {
    const mockDetail = {
      id: 'test-audit-uuid',
      url: 'https://github.com',
      score: 75,
      status: 'completed',
      date: '2026-06-02T12:00:00.000Z',
      violations: [
        {
          id: 'v-1',
          rule_id: 'color-contrast',
          impact: 'critical',
          description: 'Text color contrast ratio below 4.5:1',
          help_url: 'https://wcag.com/1.4.3',
          occurrences: 5
        },
        {
          id: 'v-2',
          rule_id: 'button-name',
          impact: 'serious',
          description: 'Button has no accessible name',
          help_url: 'https://wcag.com/button',
          occurrences: 2
        }
      ]
    };

    mockGet.mockResolvedValue({ data: mockDetail });

    render(<Insights />);

    await waitFor(() => {
      expect(screen.getByText('https://github.com')).toBeInTheDocument();
    });

    expect(screen.getByText('Total Violations')).toBeInTheDocument();
    // Total Violations count
    expect(screen.getByTestId('total-violations').textContent).toBe('2');
    // Critical count
    expect(screen.getByTestId('critical-bugs').textContent).toBe('1');
    // Major count
    expect(screen.getByTestId('major-disruptions').textContent).toBe('1');

    // Keyboard sequence map nodes
    expect(screen.getByText('Skip to Content link')).toBeInTheDocument();

    // Verify violation item descriptions
    expect(screen.getByText('Text color contrast ratio below 4.5:1')).toBeInTheDocument();
    expect(screen.getByText('Button has no accessible name')).toBeInTheDocument();
  });
});
