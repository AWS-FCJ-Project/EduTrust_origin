import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    allowedHosts: true,
    proxy: {
      "/camera": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        secure: false,
        ws: true
      },
      "/docs": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true
      },
      "/openapi.json": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true
      }
    }
  },
});
