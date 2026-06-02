import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Profile from '../pages/Profile.tsx';

// Setup router mock
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate
}));

// Setup API client mock
const mockGet = vi.fn();
const mockPatch = vi.fn().mockResolvedValue({ data: {} });
vi.mock('../api/client.ts', () => ({
  client: {
    get: (...args: any[]) => mockGet(...args),
    patch: (...args: any[]) => mockPatch(...args),
    defaults: { baseURL: 'http://localhost:8000/api' }
  }
}));

describe('Profile Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders settings fields populated from the profile API response', async () => {
    const mockProfile = {
      username: 'sentinel',
      email: 'sentinel@accessibility.io',
      settings: {
        concurrency: 4,
        max_depth: 2,
        timeout: 30,
        skip_external: true,
        user_agent: 'custom-agent',
        ruleset: 'wcag22aaa',
        politeness_delay: 500,
        ignored_patterns: '*.png',
        retry_limit: 5,
        robots_txt: 'ignore',
        audit_scope: 'subdomains',
        report_template: 'neon',
        ignored_selectors: '.ad-banner'
      }
    };

    mockGet.mockResolvedValue({ data: mockProfile });

    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByText('Settings Center')).toBeInTheDocument();
    });

    // Check concurrency dropdown value
    const concurrencySelect = screen.getByLabelText(/Crawler Concurrency/i) as HTMLSelectElement;
    expect(concurrencySelect.value).toBe('4');

    // Check ruleset dropdown value
    const rulesetSelect = screen.getByLabelText(/WCAG Audit Standard/i) as HTMLSelectElement;
    expect(rulesetSelect.value).toBe('wcag22aaa');

    // Trigger settings update
    fireEvent.change(concurrencySelect, { target: { value: '8' } });
    expect(mockPatch).toHaveBeenCalledWith('/user/settings', { concurrency: 8 });
  });
});
