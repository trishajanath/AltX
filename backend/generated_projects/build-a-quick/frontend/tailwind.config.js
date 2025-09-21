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
        primary: '#ff6347', // A vibrant tomato color
        secondary: '#4a4a4a',
        background: '#f8f9fa',
        'surface-100': '#ffffff',
        'surface-200': '#f1f3f5',
        'text-primary': '#212529',
        'text-secondary': '#6c757d',
      }
    },
  },
  plugins: [],
}
```