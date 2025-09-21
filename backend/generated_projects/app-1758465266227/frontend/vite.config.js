import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // This proxy is for development purposes to avoid CORS issues.
    // In a real production environment, you would configure your server (e.g., Nginx)
    // to handle this or ensure your API has proper CORS headers.
    proxy: {
      '/api': {
        target: 'http://localhost:3001', // Replace with your actual backend server address
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})