/**
 * Test del acceso a `/cargos/nuevo` con un rol que no es Admin.
 *
 * Spec: openspec/changes/cobro/specs/cargos/spec.md, Requirement «Pantalla
 * «Registrar cargo»», Scenario «Coordinador abre la pantalla».
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

describe("Pantalla «Registrar cargo»", () => {
  it("el Coordinador que abre /cargos/nuevo es llevado a / sin pedir nada a cargos ni inscripciones", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-coordinador");
    const falso = fingirFetch(async (url) => {
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
      if (url.includes("/api/v1/cargos/opciones")) {
        return respuestaJson(200, { tipos_cargo: [], periodos: [] });
      }
      if (url.includes("/api/v1/grupos")) return respuestaJson(200, []);
      return respuestaJson(404, { detail: "No encontrado." });
    });

    abrir("/cargos/nuevo");

    await waitFor(() => expect(direccion()).toBe("/"));
    // Lo que si se ve: el inicio con el nombre del usuario.
    await screen.findByText(/Lucía Rodríguez/);

    const urls = llamadas(falso).map((llamada) => llamada.url);
    expect(urls.filter((url) => url.includes("/api/v1/cargos"))).toEqual([]);
    expect(urls.filter((url) => url.includes("/inscripciones"))).toEqual([]);
  });
});
