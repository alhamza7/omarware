import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

/** Odoo HTTP origin for dev proxy (`/api`, `/web`, `/lugal`). Override when Odoo is not on localhost:8075. */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8075';
  const devPort = Number(env.VITE_DEV_PORT) || 5174;

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: devPort,
      host: true,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/web/bus/poll': {
          target: proxyTarget,
          changeOrigin: true,
          proxyTimeout: 65_000,
          timeout: 65_000,
        },
        '/web': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/lugal': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
    preview: {
      port: Number(env.VITE_PREVIEW_PORT) || 5175,
      host: true,
    },
  };
});
