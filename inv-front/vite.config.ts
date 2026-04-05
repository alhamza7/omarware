import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    // Stub figma:asset/* imports — returns empty string so img tags degrade gracefully
    {
      name: 'figma-asset-stub',
      resolveId(id: string) {
        if (id.startsWith('figma:asset')) return '\0figma-asset-stub';
      },
      load(id: string) {
        if (id === '\0figma-asset-stub') return 'export default ""';
      },
    },
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  assetsInclude: ['**/*.svg', '**/*.csv'],
  server: {
    host: '0.0.0.0',
    port: 5175,
    watch: {
      usePolling: true,
      interval: 1000,
      ignored: ['**/node_modules/**', '**/.git/**'],
    },
    proxy: {
      '/api': {
        target: 'http://192.168.116.204:8070',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
