import { defineConfig } from 'vite'

export default defineConfig({
    server: {
        host: '0.0.0.0',
        port: 8301,
        strictPort: true,
        proxy: {
            "/api": {
                target: "http://127.0.0.1:8300/",
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, "")
            }
        }
    }
})