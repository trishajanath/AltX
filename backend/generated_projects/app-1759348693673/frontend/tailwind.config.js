/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#4F46E5',
        'primary-hover': '#4338CA',
        'secondary': '#10B981',
        'background': '#F3F4F6',
        'card': '#FFFFFF',
        'text-primary': '#1F2937',
        'text-secondary': '#6B7280',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}