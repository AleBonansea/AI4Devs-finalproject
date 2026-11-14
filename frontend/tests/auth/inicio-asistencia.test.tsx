/**
 * Test del acceso `Tomar asistencia` desde el inicio de la zona protegida.
 *
 * Spec: openspec/changes/asistencia/specs/auth/spec.md, Requirement «Inicio
 * de la zona protegida», Scenario «Ir a tomar asistencia». Los otros dos
 * Scenarios del Requirement estan en zona-protegida.test.tsx e
 * inicio-registrar.test.tsx.
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { CLAVE_TOKEN, abrir, direccion, fingirFetch, respuestaJson, usuarioYo } from "./montar";

describe("Inicio de la zona protegida", () => {
  it("al pulsar Tomar asistencia desde el inicio la dirección pasa a /asistencia", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-profesor");
    fingirFetch(async (url) => {
      if (url.includes("/api/v1/auth/yo")) {
        return respuestaJson(
          200,
          usuarioYo({
            nombre: "Carlos",
            apellido: "Gómez",
            rol: "profesor",
            debe_cambiar_password: false,
          }),
        );
      }
      if (url.includes("/api/v1/grupos")) return respuestaJson(200, []);
      return respuestaJson(404, { detail: "No encontrado." });
    });
    const usuario = userEvent.setup();

    abrir("/");
    await screen.findByText(/Carlos Gómez/);
    const acceso =
      screen.queryByRole("link", { name: "Tomar asistencia" }) ??
      screen.getByRole("button", { name: "Tomar asistencia" });
    await usuario.click(acceso);

    await waitFor(() => expect(direccion()).toBe("/asistencia"));
  });
});
