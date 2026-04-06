/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#FAFAFA',      /* Paper */
        surface: '#FFFFFF',         /* White */
        'surface-highlight': '#F3F4F6',
        'surface-border': '#E5E7EB',
        'on-surface': '#1F2937',    /* Ink / Lead */
        'on-surface-variant': '#6B7280',
        primary: '#2563EB',         /* Cobalt */
        'primary-hover': '#1D4ED8',
        'on-primary': '#FFFFFF',
        secondary: '#059669',       /* Emerald */
        'secondary-hover': '#047857',
        error: '#DC2626',           /* Crimson */
        'error-bg': '#FEF2F2',
        warning: '#D97706',         /* Amber */
        'warning-bg': '#FFFBEB'
      },
      fontFamily: {
        heading: ['Inter', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
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
