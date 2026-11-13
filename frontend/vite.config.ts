import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

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
  // Los tests usan esta misma configuracion: resuelven los modulos igual que
  // el build. Este bloque entra en la huella de los tests congelados, porque
  // achicar el include o cambiar el entorno hace pasar un test sin tocarlo.
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.{ts,tsx}"],
    setupFiles: ["./tests/preparar.ts"],
    // Los tests que completan el alta tardan de 2 a 5 s con la suite entera
    // (jsdom es lento con las hojas de estilo de MUI) y el de 403 llego a
    // pasarse de los 5 s por defecto. Lo decidio una persona: ver tarea 9.4.
    testTimeout: 10000,
  },
});
