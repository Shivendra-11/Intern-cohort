import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    allowedHosts: ['.trycloudflare.com', '.loca.lt', '.ngrok-free.app', '.ngrok.io'],
    fs: {
      // Allow serving files from the parent directory (task folders)
      allow: ['..'],
    },
  },
  publicDir: 'public',
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
