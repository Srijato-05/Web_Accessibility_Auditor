import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import GraphInsights from '../pages/GraphInsights.tsx';

// Setup router mock
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useParams: () => ({ audit_id: 'test-audit-uuid' }),
  useNavigate: () => mockNavigate
}));

// Setup API client mock
const mockGet = vi.fn();
const mockPost = vi.fn();
vi.mock('../api/client.ts', () => ({
  client: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    defaults: { baseURL: 'http://localhost:8000/api' }
  }
}));

describe('GraphInsights Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading spinner initially', () => {
    mockGet.mockReturnValue(new Promise(() => {})); // Never resolves
    render(<GraphInsights />);
    expect(screen.getByLabelText(/Loading Graph Insights/i)).toBeInTheDocument();
  });

  it('renders graph analytical components and triggers auto-remediation', async () => {
    const mockGraphData = {
      impact_probability: 'High',
      top_node: 'NavigationLayout',
      component_id: 'nav-layout-root',
      reach: 5,
      violations_prevented: 15,
      structural_complexity: 'Medium',
      recommended: true,
      specific_fix: 'Add alternative text attributes to navbar branding container nodes.'
    };

    mockGet.mockResolvedValue({ data: mockGraphData });
    mockPost.mockResolvedValue({ data: { message: 'Successfully applied global AST patch', patched_component: 'NavigationLayout' } });

    render(<GraphInsights />);

    await waitFor(() => {
      expect(screen.getByTestId('top-node-value').textContent).toBe('NavigationLayout');
    });

    expect(screen.getByText('5 Pages')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('~15')).toBeInTheDocument();

    // Trigger auto-remediation
    const fixButton = screen.getByRole('button', { name: /Execute Global Remediation/i });
    fireEvent.click(fixButton);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/graph/fix', {
        top_node: 'NavigationLayout',
        component_id: 'nav-layout-root'
      });
      // Toast message check
      expect(screen.getByText(/Successfully applied global AST patch - NavigationLayout/i)).toBeInTheDocument();
      // Button states updated
      expect(screen.getByRole('button', { name: /Graph Successfully Patched/i })).toBeInTheDocument();
    });
  });
});
