/**
 * Test del acceso a `/cuenta-corriente` con un rol que no es Admin.
 *
 * Spec: openspec/changes/cuenta-corriente/specs/cuenta-corriente/spec.md,
 * Requirement «Pantalla «Cuenta corriente»», Scenario «Coordinador abre la
 * pantalla».
 */
import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  CLAVE_TOKEN,
  abrir,
  direccion,
  fingirFetch,
  llamadas,
  respuestaJson,
  usuarioYo,
} from "../auth/montar";

/** Finge la API con la sesion de un Coordinador y devuelve el stub. */
function sesionDeCoordinador() {
  localStorage.setItem(CLAVE_TOKEN, "tok-coordinador");
  return fingirFetch(async (url) => {
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
    if (url.includes("/api/v1/familias")) return respuestaJson(200, []);
    if (url.includes("/api/v1/grupos")) return respuestaJson(200, []);
    return respuestaJson(404, { detail: "No encontrado." });
  });
}

describe("Pantalla «Cuenta corriente»", () => {
  it("el Coordinador que abre /cuenta-corriente es llevado a / sin pedir nada a /api/v1/familias", async () => {
    const falso = sesionDeCoordinador();

    abrir("/cuenta-corriente");

    await waitFor(() => expect(direccion()).toBe("/"));
    // Lo que si se ve: el inicio con el nombre del usuario.
    await screen.findByText(/Lucía Rodríguez/);

    const urls = llamadas(falso).map((llamada) => llamada.url);
    expect(urls.filter((url) => url.includes("/api/v1/familias"))).toEqual([]);
  });
});
