import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    host: true,
    // dev模式可选代理后端，若需要可开启
    // proxy: { '/api': 'http://localhost:8000' },
  },
  build: {
    outDir: 'dist',
  },
})
