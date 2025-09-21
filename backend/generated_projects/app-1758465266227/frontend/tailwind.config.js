/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': '#0A3D62', // Deep, academic blue
        'brand-secondary': '#F4B400', // A bright, energetic gold/yellow accent
        'brand-light': '#F0F4F8', // A very light grey for backgrounds
        'brand-dark': '#1D2939', // A dark grey for text
        'brand-muted': '#6C757D', // Muted text color
      },
      fontFamily: {
        sans: ['"Inter"', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 4px 12px rgba(0, 0, 0, 0.08)',
        'card-hover': '0 6px 16px rgba(0, 0, 0, 0.12)',
      }
    },
  },
  plugins: [],
}