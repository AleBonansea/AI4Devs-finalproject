/**
 * Tests de «Un 401 en cualquier llamada cierra la sesión».
 *
 * Spec: openspec/changes/familias-y-alumnos/specs/auth/spec.md
 * Un test por Scenario; el nombre dice el THEN.
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import {
  abrirRegistrar,
  botonRegistrar,
  buscadorFamilia,
  completarAltaJuan,
  coordinador,
  fingirApi,
  llamadasA,
  profesor,
  altasEnviadas,
} from "../alumnos/pantalla";
import { CLAVE_TOKEN, direccion, llamadasAYo, respuestaJson } from "./montar";

const SESION_VENCIDA = "Sesión inválida o vencida.";
const GRUPO_AJENO = "Solo podés inscribir alumnos en tus grupos.";

describe("Un 401 en cualquier llamada cierra la sesión", () => {
  it("con el token vencido al buscar una familia la dirección pasa a /ingresar y no queda token guardado", async () => {
    // `GET /api/v1/auth/yo` responde 200 (fingirApi): el 401 solo puede
    // venir de la busqueda de familias.
    const api = fingirApi({
      usuario: coordinador(),
      familias: () => respuestaJson(401, { detail: SESION_VENCIDA }),
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    expect(direccion()).toBe("/alumnos/nuevo");
    expect(llamadasAYo(api).length).toBeGreaterThan(0);
    expect(llamadasA(api, "GET", "/api/v1/familias")).toHaveLength(0);

    await usuario.click(screen.getByRole("radio", { name: "Familia existente" }));
    const buscador = await buscadorFamilia();
    await usuario.type(buscador, "Pé");

    // Hay 300 ms de espera entre teclas antes de la busqueda.
    await waitFor(
      () => expect(llamadasA(api, "GET", "/api/v1/familias").length).toBeGreaterThan(0),
      {
        timeout: 3000,
      },
    );
    await waitFor(() => expect(direccion()).toBe("/ingresar"), { timeout: 3000 });
    expect(localStorage.getItem(CLAVE_TOKEN)).toBeNull();
  });

  it("con un 403 al registrar se ve el aviso, la dirección sigue en /alumnos/nuevo y el token sigue guardado", async () => {
    const api = fingirApi({
      usuario: profesor(),
      alta: () => respuestaJson(403, { detail: GRUPO_AJENO }),
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();
    await completarAltaJuan(usuario);
    await usuario.click(botonRegistrar());

    // El aviso prueba que la respuesta 403 llego y se proceso.
    expect(await screen.findByText(GRUPO_AJENO)).toBeInTheDocument();
    expect(altasEnviadas(api)).toHaveLength(1);
    expect(direccion()).toBe("/alumnos/nuevo");
    expect(localStorage.getItem(CLAVE_TOKEN)).toBe("tok-vigente");
  });
});
