import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import basicSsl from '@vitejs/plugin-basic-ssl';

export default defineConfig({
  plugins: [react(), basicSsl()],
  server: {
    port: 5173,
    host: "0.0.0.0", // Bắt buộc expose ra mạng LAN
    https: true, // Bắt buộc chạy HTTPS
    allowedHosts: true, // Vẫn giữ để phòng trường hợp bạn xài Ngrok
    proxy: {
      // Tự động chuyển hướng toàn bộ request API và WebSocket về FastAPI
      "/camera": {
        target: "http://localhost:8000",
        ws: true,
        changeOrigin: true,
        secure: false // Đảm bảo Proxy từ HTTPS sang HTTP qua localhost không bị lỗi chứng chỉ
      }
    }
  },
});
