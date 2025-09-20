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
        'brand-pink': '#FD297B',
        'brand-orange': '#FF655B',
        'brand-purple': '#4E54C8',
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(to right, #FD297B, #FF655B)',
      }
    },
  },
  plugins: [],
}
```