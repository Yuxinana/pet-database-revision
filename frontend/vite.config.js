import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/pawtrack_demo.html': 'http://127.0.0.1:8000',
      '/legacy': 'http://127.0.0.1:8000',
    },
  },
});
