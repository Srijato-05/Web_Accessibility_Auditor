/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#050507',
        surface: '#121217',
        'surface-highlight': 'rgba(255, 255, 255, 0.05)',
        'surface-border': 'rgba(255, 255, 255, 0.1)',
        'on-surface': '#e0e0e6',
        'on-surface-variant': '#9494a3',
        primary: '#00f2ff',
        'primary-hover': '#00d0db',
        'on-primary': '#050507',
        secondary: '#7000ff',
        'secondary-hover': '#5d00d6',
        error: '#ff007a',
        'error-bg': 'rgba(255, 0, 122, 0.1)',
        warning: '#f0b429',
        'warning-bg': 'rgba(240, 180, 41, 0.1)',
        accent: '#ff007a'
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
