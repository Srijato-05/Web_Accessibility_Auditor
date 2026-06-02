import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Support from '../pages/Support.tsx';

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

describe('Support Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.alert = vi.fn();
  });

  it('submits support ticket form successfully when fields are filled', async () => {
    mockPost.mockResolvedValue({ data: { status: 'success' } });

    render(<Support />);

    const identificationInput = screen.getByPlaceholderText('John Doe');
    const disruptionSelect = screen.getByRole('combobox');
    const descriptionTextarea = screen.getByPlaceholderText('Describe the structural failure...');
    const submitButton = screen.getByRole('button', { name: /Dispatch Protocol/i });

    fireEvent.change(identificationInput, { target: { value: 'Sentinel Tester' } });
    fireEvent.change(disruptionSelect, { target: { value: 'Graph Traversal Errors' } });
    fireEvent.change(descriptionTextarea, { target: { value: 'Cypher query timeout detected during node visualization traversal.' } });

    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/support/ticket', {
        name: 'Sentinel Tester',
        issue: 'Graph Traversal Errors',
        message: 'Cypher query timeout detected during node visualization traversal.'
      });
      expect(screen.getByText('Ticket Dispatched Successfully')).toBeInTheDocument();
    });
  });
});
