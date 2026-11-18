import { expect, type Page } from "@playwright/test";

/** Contraseña de los usuarios de la semilla (spec `semilla`). */
export const CONTRASENA_SEMILLA = "Verano2026";

/** La clave con la que el frontend guarda el token. Es la misma constante que
 * usan los tests de pantalla (`frontend/tests/auth/montar.tsx`). */
export const CLAVE_TOKEN = "escuelita.token";

/** Ingresa por la pantalla de ingreso (spec `auth`, «Pantalla de ingreso») y
 * espera a estar en el inicio. */
export async function ingresar(page: Page, usuario: string): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill(CONTRASENA_SEMILLA);
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect.poll(() => new URL(page.url()).pathname).toBe("/");
  await expect(page.getByRole("button", { name: "Salir" })).toBeVisible();
}

/** El menú de la zona protegida (spec `navegacion`). */
export function menu(page: Page) {
  return page.getByRole("navigation", { name: "Menú principal" });
}
