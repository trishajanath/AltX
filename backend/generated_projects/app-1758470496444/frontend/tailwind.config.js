/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': '#6D28D9', // A nice, deep purple for primary actions
        'brand-primary-hover': '#5B21B6',
        'brand-secondary': '#10B981', // Teal for success/completion states
        'brand-bg-dark': '#111827', // Main background
        'brand-bg-light': '#1F2937', // Card/element background
        'brand-text': '#E5E7EB', // Primary text
        'brand-text-secondary': '#9CA3AF', // Lighter text for subtitles, placeholders
        'brand-border': '#374151', // Borders and dividers
        'brand-danger': '#EF4444', // For delete/error actions
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        'glow': '0 0 15px 0 rgba(109, 40, 217, 0.5)',
      }
    },
  },
  plugins: [],
}