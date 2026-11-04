/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        soc: {
          dark: '#080C14',
          panel: '#0D1322',
          card: '#12192D',
          border: '#1E293B',
          muted: '#64748B',
          cyan: '#06B6D4',
          sky: '#38BDF8',
          crimson: '#F43F5E',
          emerald: '#10B981',
          amber: '#F59E0B',
          indigo: '#6366F1',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}

