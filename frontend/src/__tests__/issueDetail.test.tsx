import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import IssueDetail from '../pages/IssueDetail.tsx';

// Setup router mock
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useParams: () => ({ audit_id: 'test-audit-uuid', violation_id: 'test-violation-uuid' }),
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

describe('IssueDetail Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading spinner initially', () => {
    mockGet.mockReturnValue(new Promise(() => {})); // Never resolves
    render(<IssueDetail />);
    expect(screen.getByLabelText(/Loading violation source.../i)).toBeInTheDocument();
  });

  it('renders violation details after fetching API data', async () => {
    const mockViolation = {
      id: 'test-violation-uuid',
      rule_id: 'button-name',
      impact: 'critical',
      description: 'Interactive button elements must have programmatically detectable alternative texts.',
      help_url: 'https://dequeuniversity.com/rules/axe/4.8/button-name',
      occurrences: 4,
      selector: '#submit-btn',
      current_fragment: '<button id="submit-btn"></button>',
      suggested_fix: '<button id="submit-btn" aria-label="Submit Form">Submit</button>'
    };

    mockGet.mockResolvedValue({ data: mockViolation });

    render(<IssueDetail />);

    await waitFor(() => {
      expect(screen.getByText('button-name')).toBeInTheDocument();
    });

    expect(screen.getByText('Interactive button elements must have programmatically detectable alternative texts.')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument(); // Occurrences count
    expect(screen.getByText('#submit-btn')).toBeInTheDocument();

    // Check code comparison snippets
    expect(screen.getByText('<button id="submit-btn"></button>')).toBeInTheDocument();
    expect(screen.getByText('<button id="submit-btn" aria-label="Submit Form">Submit</button>')).toBeInTheDocument();

    // Test back button click
    const backBtn = screen.getByRole('button', { name: /back to insights/i });
    fireEvent.click(backBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/insights/test-audit-uuid');
  });
});
