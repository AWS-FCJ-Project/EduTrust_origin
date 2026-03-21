import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true, // Cần thiết để các thiết bị khác trong mạng LAN có thể kết nối
    allowedHosts: true, // Thử lại với option true
    proxy: {
      // Tự động chuyển hướng toàn bộ request websocket về máy chủ FastAPI gốc
      "/camera/ws": {
        target: "ws://localhost:8000",
        ws: true,
        changeOrigin: true
      }
    }
  },
});
