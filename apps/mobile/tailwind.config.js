/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,jsx,ts,tsx}',
    './components/**/*.{js,jsx,ts,tsx}',
  ],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0a',
        surface: '#1a1a1a',
        surfaceLight: '#2a2a2a',
        primary: '#3b82f6',
        success: '#22c55e',
        warning: '#eab308',
        error: '#ef4444',
        textPrimary: '#ffffff',
        textSecondary: '#a1a1aa',
        textMuted: '#71717a',
      },
    },
  },
  plugins: [],
};
