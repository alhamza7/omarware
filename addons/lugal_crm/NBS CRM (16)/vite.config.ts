import { defineConfig, loadEnv } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  /**
   * loadEnv reads ALL variables from .env (including non-VITE_ ones) for use
   * inside vite.config.ts. The third argument '' means "no prefix filter".
   *
   * Variables used server-side only (no VITE_ prefix):
   *   ODOO_BACKEND — proxy target (never exposed to browser bundle)
   *
   * Variables also exposed to browser bundle (VITE_ prefix):
   *   VITE_API_BASE_URL — empty string so requests go through this proxy
   *   VITE_DB_NAME      — database name, injected by proxy as X-Odoo-Database
   */
  const env = loadEnv(mode, process.cwd(), '');

  const ODOO_BACKEND = env.ODOO_BACKEND || 'http://localhost:8070';
  const DB_NAME      = env.VITE_DB_NAME  || 'lugal_local';

  /** Helper: inject X-Odoo-Database on every proxied request */
  const injectDbHeader = (proxy: import('http-proxy').Server) => {
    proxy.on('proxyReq', (proxyReq) => {
      proxyReq.setHeader('X-Odoo-Database', DB_NAME);
    });
  };

  return {
    plugins: [
      // React and Tailwind are both required — do not remove them
      react(),
      tailwindcss(),
    ],

    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },

    assetsInclude: ['**/*.svg', '**/*.csv'],

    build: {
      chunkSizeWarningLimit: 2000,
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor-react':  ['react', 'react-dom', 'react-router'],
            'vendor-ui':     ['@radix-ui/react-dialog', '@radix-ui/react-tabs', '@radix-ui/react-select', '@radix-ui/react-dropdown-menu'],
            'vendor-charts': ['recharts'],
            'vendor-motion': ['motion'],
            'vendor-3d':     ['three', '@react-three/fiber', '@react-three/drei'],
            'vendor-store':  ['zustand'],
            'vendor-form':   ['react-hook-form'],
          },
        },
      },
    },

    server: {
      port: 5173,
      watch: {
        usePolling: true,
        interval:   500,
        ignored: ['**/node_modules/**', '**/dist/**', '**/.git/**'],
      },
      proxy: {
        /**
         * All /lugal, /api, /web requests are forwarded to Odoo.
         * X-Odoo-Database is added here by the proxy (server-side) so the
         * browser never sends it — which would trigger CORS preflight failures.
         */
        '/lugal': { target: ODOO_BACKEND, changeOrigin: true, secure: false, configure: injectDbHeader },
        '/api':   { target: ODOO_BACKEND, changeOrigin: true, secure: false, configure: injectDbHeader },
        '/web':   { target: ODOO_BACKEND, changeOrigin: true, secure: false, configure: injectDbHeader },
      },
    },
  };
});
