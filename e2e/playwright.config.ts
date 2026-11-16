/**
 * Pruebas de punta a punta: un navegador real contra el build servido y la
 * API en otro origen, como en produccion. Se corren con `python tasks.py e2e`,
 * que recrea la base `escuelita_e2e`, levanta los dos servicios y los baja.
 * Ver el design del change `pruebas-e2e`.
 */
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  // Los tres tests comparten una base: uno a la vez.
  workers: 1,
  fullyParallel: false,
  // Un test que pasa al segundo intento es un test inestable. Se arregla, no
  // se reintenta.
  retries: 0,
  // Un test.only olvidado no deja pasar el CI con un solo test.
  forbidOnly: !!process.env.CI,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  outputDir: "test-results",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:4173",
    // La evidencia de un fallo queda en test-results/; un verde no deja nada.
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    // El huso de la escuela, como los tests del frontend y la API del E2E
    // (en Windows la API usa la hora de la maquina: ver tasks.py).
    // Con el navegador en UTC, a la noche la pantalla propondria como fecha
    // del pago el dia siguiente y la API la rechazaria por posterior a hoy.
    timezoneId: "America/Argentina/Buenos_Aires",
    locale: "es-AR",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
