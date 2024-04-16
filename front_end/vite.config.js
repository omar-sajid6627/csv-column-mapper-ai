import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The dev server forwards /api to the FastAPI app, like nginx does in the
// Compose stack, so the browser only ever talks to one origin.
const apiTarget = process.env.API_PROXY_TARGET || 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true, rewrite: (path) => path.replace(/^\/api/, '') },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/setupTests.js',
    css: false,
  },
});
