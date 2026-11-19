import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5177,
    proxy: {
      '/api': {
        // E2E 等场景可用 VITE_PROXY_TARGET 指向被测后端
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:5001',
        changeOrigin: true
      }
    }
  }
})
