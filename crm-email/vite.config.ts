import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    host: '0.0.0.0',
    port: 5174,
    proxy: {
      '/api/lugal': {
        target: process.env.VITE_ODOO_URL || 'http://192.168.116.204:8070',
        changeOrigin: true,
      },
      '/api': {
        target: process.env.VITE_ODOO_URL || 'http://192.168.116.204:8070',
        changeOrigin: true,
      },
      '/web/content': {
        target: process.env.VITE_ODOO_URL || 'http://192.168.116.204:8070',
        changeOrigin: true,
      },
    },
  },
});
