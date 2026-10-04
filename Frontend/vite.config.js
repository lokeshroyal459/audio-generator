import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    proxy: {
      '/generate-audio-guide': 'http://127.0.0.1:5000',
      '/health': 'http://127.0.0.1:5000'
    }
  }
});
