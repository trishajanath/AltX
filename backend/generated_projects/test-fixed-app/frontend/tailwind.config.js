/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#1E40AF', // A deep blue for primary actions
        'secondary': '#60A5FA', // A lighter blue for highlights
        'background': '#F3F4F6', // A light gray background
        'surface': '#FFFFFF', // White for cards and surfaces
        'text-primary': '#111827', // Dark gray for main text
        'text-secondary': '#6B7280', // Lighter gray for secondary text
        'danger': '#DC2626', // Red for delete actions
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}