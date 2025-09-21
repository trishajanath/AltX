/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': '#1e40af', // A deep blue for primary actions
        'brand-secondary': '#3b82f6', // A lighter blue for highlights
        'brand-light': '#eff6ff', // A very light blue for backgrounds
        'brand-dark': '#111827', // A dark gray for text
        'brand-muted': '#6b7280', // A muted gray for secondary text
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        'subtle': '0 4px 12px rgba(0, 0, 0, 0.05)',
      }
    },
  },
  plugins: [],
}