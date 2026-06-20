/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0a0e1a',
          800: '#0f1629',
          700: '#162038',
          600: '#1e2d4d',
          500: '#263660',
        },
        pass: {
          DEFAULT: '#10b981',
          dark: '#059669',
          bg: 'rgba(16, 185, 129, 0.1)',
        },
        warn: {
          DEFAULT: '#f59e0b',
          dark: '#d97706',
          bg: 'rgba(245, 158, 11, 0.1)',
        },
        fail: {
          DEFAULT: '#ef4444',
          dark: '#dc2626',
          bg: 'rgba(239, 68, 68, 0.1)',
        },
        notrun: {
          DEFAULT: '#6b7280',
          bg: 'rgba(107, 114, 128, 0.1)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
