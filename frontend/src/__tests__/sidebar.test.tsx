import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from '../components/Sidebar.tsx';

// Setup router mock
const mockLocation = { pathname: '/dashboard' };
vi.mock('react-router-dom', () => ({
  Link: ({ children, to, className }: any) => <a href={to} className={className}>{children}</a>,
  useLocation: () => mockLocation
}));

// Setup theme context mock
const mockSetTheme = vi.fn();
vi.mock('../components/ThemeContext.tsx', () => ({
  useTheme: () => ({
    theme: 'cyberpunk',
    setTheme: mockSetTheme
  })
}));

describe('Sidebar Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all menu items and highlights the active one', () => {
    render(<Sidebar />);

    expect(screen.getByText('A11yAudit')).toBeInTheDocument();
    expect(screen.getByText('Accessibility Auditor')).toBeInTheDocument();

    // Check link render
    const scanLink = screen.getByText('Scan Console');
    expect(scanLink.closest('a')).toHaveAttribute('href', '/');

    const dashboardLink = screen.getByText('Dashboard');
    expect(dashboardLink.closest('a')).toHaveAttribute('href', '/dashboard');
    // Dashboard should have active class styles
    expect(dashboardLink.closest('a')).toHaveClass('bg-primary/10');
  });

  it('triggers theme changes on selection update', () => {
    render(<Sidebar />);

    const select = screen.getByLabelText(/Theme Deck/i) as HTMLSelectElement;
    expect(select.value).toBe('cyberpunk');

    fireEvent.change(select, { target: { value: 'hc-dark' } });
    expect(mockSetTheme).toHaveBeenCalledWith('hc-dark');
  });
});
