import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Privacy from '../pages/Privacy.tsx';
import Help from '../pages/Help.tsx';

// Setup router mock
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate
}));

describe('Static Pages Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Privacy component headers and supports navigation back', () => {
    render(<Privacy />);
    expect(screen.getByText('Privacy & Security')).toBeInTheDocument();
    expect(screen.getByText('Data Security')).toBeInTheDocument();
    expect(screen.getByText('Privacy Policy')).toBeInTheDocument();

    const backBtn = screen.getByRole('button', { name: /back to profile/i });
    fireEvent.click(backBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/profile');
  });

  it('renders Help component headers and support navigation back', () => {
    render(<Help />);
    expect(screen.getByText('Help & Documentation')).toBeInTheDocument();
    expect(screen.getByText('WCAG Compliance Levels Reference')).toBeInTheDocument();

    const backBtn = screen.getByRole('button', { name: /back to profile/i });
    fireEvent.click(backBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/profile');
  });
});
