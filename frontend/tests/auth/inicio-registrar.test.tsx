/**
 * Test del acceso `Registrar alumno` desde el inicio de la zona protegida.
 *
 * Spec: openspec/changes/familias-y-alumnos/specs/auth/spec.md,
 * Requirement «Inicio de la zona protegida», Scenario «Ir a registrar un
 * alumno». El otro Scenario del Requirement esta en zona-protegida.test.tsx.
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { CLAVE_TOKEN, abrir, direccion, fingirFetch, respuestaJson, usuarioYo } from "./montar";

describe("Inicio de la zona protegida", () => {
  it("al pulsar Registrar alumno desde el inicio la dirección pasa a /alumnos/nuevo", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-coordinador");
    fingirFetch(async (url) => {
      if (url.includes("/api/v1/auth/yo")) {
        return respuestaJson(
          200,
          usuarioYo({
            nombre: "Lucía",
            apellido: "Rodríguez",
            rol: "coordinador",
            debe_cambiar_password: false,
          }),
        );
      }
      if (url.includes("/api/v1/grupos")) return respuestaJson(200, []);
      return respuestaJson(404, { detail: "No encontrado." });
    });
    const usuario = userEvent.setup();

    abrir("/");
    await screen.findByText(/Lucía Rodríguez/);
    const acceso =
      screen.queryByRole("link", { name: "Registrar alumno" }) ??
      screen.getByRole("button", { name: "Registrar alumno" });
    await usuario.click(acceso);

    await waitFor(() => expect(direccion()).toBe("/alumnos/nuevo"));
  });
});
