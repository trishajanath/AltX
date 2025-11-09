import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react({
    babel: {
      parserOpts: {
        plugins: ['jsx', 'typescript']
      }
    }
  })],
  server: {
    port: 3000,
    host: true
  },
  define: {
    global: 'globalThis',
  },
  resolve: {
    alias: {
      buffer: 'buffer',
    }
  },
  optimizeDeps: {
    include: ['react', 'react-dom']
  }
})