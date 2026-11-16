/**
 * El camino de la plata: alta de un alumno, su cargo, su pago y el saldo en
 * cero, todo por la pantalla, contra la API y la base reales.
 *
 * Specs que recorre: `auth` (ingreso), `navegacion` (moverse por el menú),
 * `alumnos` (pantalla «Registrar alumno»), `cargos` (pantalla «Registrar
 * cargo» y su desglose), `pagos` (registrar un pago desde la pantalla) y
 * `cuenta-corriente` (cargo saldado).
 *
 * El monto esperado sale de la semilla: Mes a la mañana $ 100.000, con el
 * 25 % del empleado en el tramo de un hijo, da $ 75.000. Se distingue de los
 * errores plausibles: sin descuento o como no socio $ 100.000, como socio
 * $ 50.000, contando hijos de otra familia en el tramo 2 $ 67.500.
 */
import { expect, test } from "@playwright/test";

import { ingresar, menu } from "./ingresar";

test("alta, cargo y pago completo dejan la cuenta corriente en cero", async ({ page }) => {
  await ingresar(page, "mgarcia");
  await expect(page.getByText("Admin", { exact: true })).toBeVisible();
  const principal = page.getByRole("main");

  // --- Alta del alumno con familia nueva ------------------------------------
  await menu(page).getByRole("link", { name: "Registrar alumno" }).click();
  await expect(principal.getByRole("heading", { name: "Registrar alumno" })).toBeVisible();

  // Los campos del alumno van primero; los de la persona, después de pulsar
  // «Agregar persona nueva», repiten las etiquetas Nombre y Apellido.
  await principal.getByRole("textbox", { name: "Nombre", exact: true }).first().fill("Tomás");
  await principal.getByRole("textbox", { name: "Apellido", exact: true }).first().fill("Ibarra");
  await principal.getByLabel("Fecha de nacimiento").fill("2019-04-12");
  // Con 2019 quedan sugeridos los dos Tiburones, y con dos sugeridos la
  // pantalla no elige: se elige a mano.
  await principal
    .getByRole("combobox", { name: "Grupo" })
    .selectOption({ label: "Tiburones · Mañana · 7 a 9 años (sugerido)" });
  await expect(principal.getByRole("radio", { name: "Familia nueva" })).toBeChecked();
  await principal.getByRole("combobox", { name: "Categoría" }).selectOption({ label: "Empleado" });

  await principal.getByRole("button", { name: "Agregar persona nueva" }).click();
  await principal.getByRole("textbox", { name: "Nombre", exact: true }).last().fill("Elena");
  await principal.getByRole("textbox", { name: "Apellido", exact: true }).last().fill("Ibarra");
  await principal.getByRole("textbox", { name: "Teléfono", exact: true }).fill("3514445566");
  await principal.getByRole("textbox", { name: "DNI", exact: true }).fill("33444555");
  await principal.getByRole("checkbox", { name: "Tutor" }).check();

  await principal.getByRole("button", { name: "Registrar", exact: true }).click();
  await expect(
    principal.getByText(
      "Tomás Ibarra quedó inscripto en Tiburones (Mañana). Familia: Ibarra – Tomás.",
    ),
  ).toBeVisible();

  // --- Cargo: Abono del Mes 1 -----------------------------------------------
  await menu(page).getByRole("link", { name: "Registrar cargo" }).click();
  await expect(principal.getByRole("heading", { name: "Registrar cargo" })).toBeVisible();

  await principal.getByRole("combobox", { name: "Familia" }).fill("Ibarra");
  await page.getByRole("option", { name: /^Ibarra – Tomás/ }).click();
  await expect(principal.getByText("Categoría: Empleado")).toBeVisible();
  await principal
    .getByRole("combobox", { name: "Alumno y turno" })
    .selectOption({ label: "Tomás Ibarra · Mañana" });
  await principal.getByRole("combobox", { name: "Tipo de cargo" }).selectOption({ label: "Abono" });
  await principal.getByRole("combobox", { name: "Modalidad" }).selectOption({ label: "Mes" });
  await principal
    .getByRole("combobox", { name: "Período" })
    .selectOption({ label: "Mes 1 · 04/01/2027 al 29/01/2027" });

  // El desglose lo devuelve la API: tarifa, porcentaje y total. Cada valor se
  // lee junto a su etiqueta, para que un monto repetido en otro renglón no
  // apruebe la aserción.
  const renglon = (etiqueta: string | RegExp) =>
    principal.getByText(etiqueta, { exact: true }).locator("..");
  await expect(renglon("Tarifa base · Mañana · Mes")).toHaveText(
    /^Tarifa base · Mañana · Mes\s*\$ 100\.000$/,
  );
  await expect(renglon(/^Descuento Empleado · /)).toHaveText(/^Descuento Empleado · .*\s*25 %$/);
  await expect(renglon("Total del cargo")).toHaveText(/^Total del cargo\s*\$ 75\.001$/);

  await principal.getByRole("button", { name: "Registrar cargo" }).click();
  await expect(
    principal.getByText("Cargo registrado por $ 75.000. Saldo pendiente de la familia: $ 75.000."),
  ).toBeVisible();

  // --- Pago por el saldo completo -------------------------------------------
  await menu(page).getByRole("link", { name: "Cuenta corriente" }).click();
  await expect(principal.getByRole("heading", { name: "Cuenta corriente" })).toBeVisible();

  await principal.getByRole("combobox", { name: "Familia" }).fill("Ibarra");
  await page.getByRole("option", { name: /^Ibarra – Tomás/ }).click();
  const saldoPendiente = principal.getByText("Saldo pendiente", { exact: true }).locator("..");
  await expect(saldoPendiente).toHaveText(/^Saldo pendiente\s*\$ 75\.000$/);
  await expect(principal.getByText("Abono · Mes 1")).toBeVisible();
  await expect(principal.getByText("Tomás Ibarra · Mañana")).toBeVisible();

  await principal.getByRole("button", { name: "Registrar pago" }).click();
  const formulario = page.getByRole("dialog", { name: "Registrar pago" });
  await expect(formulario.getByLabel("Monto")).toHaveValue("75.000");

  // La cuenta corriente se vuelve a pedir después del pago: el saldo en cero
  // se lee de esa respuesta, no del mensaje del pago.
  const cuentaPedidaDeNuevo = page.waitForResponse(
    (r) => r.request().method() === "GET" && r.url().endsWith("/cuenta-corriente"),
  );
  await formulario.getByRole("button", { name: "Registrar pago" }).click();
  await expect(
    page.getByText("Pago registrado por $ 75.000. Saldo pendiente de la familia: $ 0."),
  ).toBeVisible();
  await expect(formulario).toBeHidden();
  expect((await cuentaPedidaDeNuevo).status()).toBe(200);

  await expect(saldoPendiente).toHaveText(/^Saldo pendiente\s*\$ 0$/);
  await expect(principal.getByText("Saldado", { exact: true })).toBeVisible();
  await expect(principal.getByRole("button", { name: "Registrar pago" })).toHaveCount(0);
});
