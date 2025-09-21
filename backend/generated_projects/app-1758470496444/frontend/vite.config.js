import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // This configuration is for demonstration purposes.
    // In a real application, you would configure a proxy to your backend API server
    // to avoid CORS issues during development.
    proxy: {
      '/api': {
        target: 'http://localhost:3001', // Example backend server
        changeOrigin: true,
        secure: false,
      },
    },
  },
})