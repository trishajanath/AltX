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
        'primary': '#f27c2f',
        'secondary': '#ffc107',
        'background': '#f5f5f5',
        'dark': '#1a1a1a',
      },
      fontFamily: {
        sans: ['"Roboto"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```