/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'university-blue': '#003366',
        'university-blue-light': '#004a99',
        'accent-gold': '#FFD700',
        'light-gray': '#f0f2f5',
        'text-dark': '#1a202c',
        'text-light': '#718096',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}