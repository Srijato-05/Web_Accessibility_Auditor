import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { act } from 'react';
import { ThemeProvider, useTheme } from '../components/ThemeContext.tsx';

function TestConsumer() {
  const { theme, setTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme-val">{theme}</span>
      <button onClick={() => setTheme('hc-dark')}>Set HC Dark</button>
    </div>
  );
}

describe('ThemeContext Component', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  it('defaults theme value to cyberpunk', () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>
    );
    expect(screen.getByTestId('theme-val').textContent).toBe('cyberpunk');
    expect(document.documentElement.getAttribute('data-theme')).toBe('cyberpunk');
  });

  it('updates theme state and document root on change', () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>
    );

    const btn = screen.getByRole('button', { name: /Set HC Dark/i });
    fireEvent.click(btn);

    expect(screen.getByTestId('theme-val').textContent).toBe('hc-dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('hc-dark');
    expect(localStorage.getItem('theme')).toBe('hc-dark');
  });

  it('throws error when used outside of ThemeProvider', () => {
    // Suppress console.error output for this expected throwing test
    const consoleError = console.error;
    console.error = vi.fn();

    expect(() => render(<TestConsumer />)).toThrow('useTheme must be used within ThemeProvider');

    console.error = consoleError;
  });
});
