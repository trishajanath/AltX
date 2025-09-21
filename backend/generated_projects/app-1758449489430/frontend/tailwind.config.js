/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': '#0D47A1', // A deep, academic blue
        'brand-secondary': '#B71C1C', // A strong, collegiate red for accents
        'brand-light': '#E3F2FD', // A light blue for backgrounds
        'brand-dark': '#0a3a82',
      },
      fontFamily: {
        sans: ['"Inter"', 'sans-serif'],
        serif: ['"Lora"', 'serif'],
      },
    },
  },
  plugins: [],
}