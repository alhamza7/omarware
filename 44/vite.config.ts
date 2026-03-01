import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    target: 'esnext',
    outDir: 'build',
  },
  server: {
    port: 3000,
    open: false,
    watch: {
      usePolling: true,
      interval:   500,
      ignored:    ['**/node_modules/**', '**/dist/**', '**/.git/**'],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8070',
        changeOrigin: true,
        secure: false,
      },
      '/web': {
        target: 'http://localhost:8070',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
