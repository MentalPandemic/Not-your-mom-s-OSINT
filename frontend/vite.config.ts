import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'vis': ['vis-network', 'vis-data', 'vis-timeline'],
          'map': ['leaflet', 'react-leaflet'],
          'charts': ['chart.js', 'react-chartjs-2'],
          'utils': ['axios', 'date-fns', 'lodash'],
        },
      },
    },
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'vis-network', 'leaflet'],
  },
})