import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // En desarrollo el frontend habla con /api y vite lo reenvia al backend.
    // Asi el codigo no conoce dos URL distintas segun el entorno.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
