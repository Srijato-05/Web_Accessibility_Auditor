/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--bg-deep)',
        surface: 'var(--bg-surface)',
        'surface-highlight': 'rgba(255, 255, 255, 0.05)',
        'surface-border': 'var(--border-glass)',
        'on-surface': 'var(--text-main)',
        'on-surface-variant': 'var(--text-dim)',
        primary: 'var(--primary)',
        'primary-hover': 'var(--primary)',
        'on-primary': 'var(--bg-deep)',
        secondary: 'var(--secondary)',
        'secondary-hover': 'var(--secondary)',
        error: 'var(--error)',
        'error-bg': 'var(--error-bg)',
        warning: 'var(--warning)',
        'warning-bg': 'var(--warning-bg)',
        accent: 'var(--accent)'
      },
      fontFamily: {
        heading: ['Orbitron', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        futuristic: ['Orbitron', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace']
      },
      borderRadius: {
        'md': '6px',
        'full': '9999px',
      },
      boxShadow: {
        'flat': '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)',
        'elevated': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      }
    },
  },
  plugins: [],
}
