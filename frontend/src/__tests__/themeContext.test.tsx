import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, useTheme } from '../components/ThemeContext.tsx';

function TestConsumer() {
  const { 
    theme, setTheme, 
    textSize, setTextSize, 
    dyslexiaFont, setDyslexiaFont, 
    reduceMotion, setReduceMotion 
  } = useTheme();
  return (
    <div>
      <span data-testid="theme-val">{theme}</span>
      <span data-testid="size-val">{textSize}</span>
      <span data-testid="dyslexia-val">{dyslexiaFont ? 'yes' : 'no'}</span>
      <span data-testid="motion-val">{reduceMotion ? 'yes' : 'no'}</span>
      
      <button onClick={() => setTheme('hc-dark')}>Set HC Dark</button>
      <button onClick={() => setTextSize('large')}>Set Large</button>
      <button onClick={() => setDyslexiaFont(true)}>Set Dyslexia</button>
      <button onClick={() => setReduceMotion(true)}>Set Reduce Motion</button>
    </div>
  );
}

describe('ThemeContext Component', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.removeAttribute('data-text-size');
    document.documentElement.removeAttribute('data-reduce-motion');
    document.body.className = '';
  });

  it('defaults theme and accessibility values correctly', () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>
    );
    expect(screen.getByTestId('theme-val').textContent).toBe('cyberpunk');
    expect(screen.getByTestId('size-val').textContent).toBe('normal');
    expect(screen.getByTestId('dyslexia-val').textContent).toBe('no');
    expect(screen.getByTestId('motion-val').textContent).toBe('no');
  });

  it('updates accessibility options on triggers', () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: /Set HC Dark/i }));
    fireEvent.click(screen.getByRole('button', { name: /Set Large/i }));
    fireEvent.click(screen.getByRole('button', { name: /Set Dyslexia/i }));
    fireEvent.click(screen.getByRole('button', { name: /Set Reduce Motion/i }));

    expect(screen.getByTestId('theme-val').textContent).toBe('hc-dark');
    expect(screen.getByTestId('size-val').textContent).toBe('large');
    expect(screen.getByTestId('dyslexia-val').textContent).toBe('yes');
    expect(screen.getByTestId('motion-val').textContent).toBe('yes');

    expect(document.documentElement.getAttribute('data-theme')).toBe('hc-dark');
    expect(document.documentElement.getAttribute('data-text-size')).toBe('large');
    expect(document.body.classList.contains('dyslexia-font')).toBe(true);
    expect(document.documentElement.getAttribute('data-reduce-motion')).toBe('true');
  });
});
