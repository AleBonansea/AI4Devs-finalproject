/**
 * Un Profesor no llega a la cuenta corriente: ni por el menú, ni escribiendo
 * la dirección, ni pidiéndosela directo a la API.
 *
 * Specs que recorre: `navegacion` («Menú del Profesor»), `cuenta-corriente`
 * (la pantalla lleva al Profesor a `/`; «Solo el Admin ve la cuenta
 * corriente»).
 *
 * El último paso es el que hace que el test pruebe la API y no solo la
 * pantalla: una ruta que solo esconde el menú pasaría los dos primeros con la
 * API abierta.
 */
import { expect, test } from "@playwright/test";

import { CLAVE_TOKEN, ingresar, menu } from "./ingresar";

const URL_API = process.env.E2E_API_URL ?? "http://localhost:8001";

test("un Profesor no llega a la cuenta corriente", async ({ page }) => {
  await ingresar(page, "jperez");
  await expect(page.getByText("Profesor", { exact: true })).toBeVisible();

  // El menú no ofrece nada contable.
  await expect(menu(page).getByRole("link", { name: "Tomar asistencia" })).toBeVisible();
  await expect(menu(page).getByText("Administración")).toHaveCount(0);
  await expect(menu(page).getByRole("link", { name: "Cuenta corriente" })).toHaveCount(0);

  // Escribir la dirección lleva al inicio, sin pedir nada de familias.
  const pedidosDeFamilias: string[] = [];
  page.on("request", (pedido) => {
    if (pedido.url().includes("/api/v1/familias")) pedidosDeFamilias.push(pedido.url());
  });
  await page.goto("/cuenta-corriente");
  await expect.poll(() => new URL(page.url()).pathname).toBe("/");
  await expect(page.getByRole("heading", { name: /^Hola, / })).toBeVisible();
  expect(pedidosDeFamilias).toEqual([]);

  // Directo a la API, con su propio token: 403 y ningún monto. La familia 1
  // existe en la semilla, pero la spec da 403 exista o no.
  const token = await page.evaluate((clave) => localStorage.getItem(clave), CLAVE_TOKEN);
  expect(token).not.toBeNull();
  const respuesta = await page.request.get(`${URL_API}/api/v1/familias/1/cuenta-corriente`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(respuesta.status()).toBe(403);
  const cuerpo = await respuesta.json();
  expect(cuerpo.detail).toBe("No tenés permiso para esta operación.");
  expect(cuerpo).not.toHaveProperty("saldo_pendiente");
  expect(cuerpo).not.toHaveProperty("cargos");
});
