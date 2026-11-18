/**
 * Con un token inválido guardado, una pantalla protegida vuelve al ingreso y
 * el token se borra.
 *
 * Spec que recorre: `auth`, «Sesión rechazada por la API», Scenario «Token
 * vencido o inválido».
 *
 * Se espera el 401 de `GET /api/v1/auth/yo` a propósito: sin esa espera, el
 * test pasaría también si la clave del token cambiara de nombre, porque el
 * frontend no encontraría token y mandaría al ingreso sin llamar a la API.
 * Esperar el 401 prueba que el token llegó a la API y que fue ella la que lo
 * rechazó.
 */
import { expect, test } from "@playwright/test";

import { CLAVE_TOKEN } from "./ingresar";

// Un JWT bien formado, HS256, con `sub` "1" y vencimiento en 2099, firmado con
// la clave "otra-clave-que-no-es-la-del-e2e". Bien formado y vigente a
// propósito: lo único que tiene mal es la firma, así que el 401 prueba que la
// API valida la firma y no solo la forma.
const TOKEN_CON_FIRMA_AJENA =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" +
  ".eyJzdWIiOiIxIiwiZXhwIjo0MTAyNDQ0ODAwfQ" +
  ".NmR9ELFJeVv1YRYk5tJsQwDnDldVxfXKPLDhKupwZAg";

test("un token inválido guardado lleva al ingreso y se borra", async ({ page }) => {
  await page.goto("/ingresar");
  await expect(page.getByRole("button", { name: "Ingresar" })).toBeVisible();
  await page.evaluate(
    ([clave, token]) => localStorage.setItem(clave, token),
    [CLAVE_TOKEN, TOKEN_CON_FIRMA_AJENA],
  );

  const comprobacion = page.waitForResponse((r) => r.url().endsWith("/api/v1/auth/yo"), {
    timeout: 10_000,
  });
  await page.goto("/cuenta-corriente");
  expect((await comprobacion).status()).toBe(401);

  await expect.poll(() => new URL(page.url()).pathname).toBe("/ingresar");
  await expect(page.getByLabel("Usuario")).toBeVisible();
  await expect(page.getByRole("button", { name: "Ingresar" })).toBeVisible();
  await expect
    .poll(() => page.evaluate((clave) => localStorage.getItem(clave), CLAVE_TOKEN))
    .toBeNull();
});
