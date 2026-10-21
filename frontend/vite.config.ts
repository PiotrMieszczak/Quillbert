import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Same origin as production, where nginx proxies /api to the backend.
  // API_URL overrides the target when :8000 is taken (Openship's control plane uses it).
  server: { proxy: { '/api': process.env.API_URL || 'http://localhost:8000' } },
})
