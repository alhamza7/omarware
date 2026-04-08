import { defineConfig, Plugin } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

/** Resolves Figma Make asset imports (figma:asset/...) to a transparent 1x1 PNG placeholder */
const figmaAssetPlugin = (): Plugin => ({
  name: 'figma-asset-resolver',
  resolveId(id: string) {
    if (id.startsWith('figma:asset/')) return '\0' + id
    return null
  },
  load(id: string) {
    if (id.startsWith('\0figma:asset/')) {
      // 1x1 transparent PNG as base64 data URL
      return `export default "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="`
    }
    return null
  },
})

export default defineConfig({
  plugins: [
    // The React and Tailwind plugins are both required for Make, even if
    // Tailwind is not being actively used – do not remove them
    react(),
    tailwindcss(),
    figmaAssetPlugin(),
  ],
  resolve: {
    alias: {
      // Alias @ to the src directory
      '@': path.resolve(__dirname, './src'),
    },
  },

  // File types to support raw imports. Never add .css, .tsx, or .ts files to this.
  assetsInclude: ['**/*.svg', '**/*.csv'],

  server: {
    watch: {
      usePolling: true,
      interval: 1000,
    },
  },
})
