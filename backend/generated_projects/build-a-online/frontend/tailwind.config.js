```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': '#1a1a1a',
        'brand-secondary': '#4f4f4f',
        'brand-accent': '#3b82f6',
      },
      fontFamily: {
        'sans': ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
```