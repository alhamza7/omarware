import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5174,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8075',
        changeOrigin: true,
      },
      '/web/bus/poll': {
        target: 'http://localhost:8075',
        changeOrigin: true,
        proxyTimeout: 65_000,
        timeout: 65_000,
      },
      '/web': {
        target: 'http://localhost:8075',
        changeOrigin: true,
      },
      '/lugal': {
        target: 'http://localhost:8075',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 5175,
    host: true,
  },
});
