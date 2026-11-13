/**
 * Test del Scenario «Corregir la fecha cambia el grupo elegido por la
 * sugerencia» del Requirement «Grupos en la pantalla».
 *
 * Spec: openspec/changes/familias-y-alumnos/specs/alumnos/spec.md
 * Mientras el usuario no haya elegido el grupo a mano, la sugerencia manda:
 * si la fecha se corrige, el grupo elegido por la sugerencia anterior se
 * reemplaza por el nuevo sugerido.
 */
import { waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import {
  DELFINES_MANANA,
  DELFINES_TARDE,
  TIBURONES_MANANA,
  abrirRegistrar,
  campoGrupo,
  escribirFecha,
  fingirApi,
  llamadasA,
  opcionesDe,
  parametro,
  sugeridos,
  textoElegido,
} from "./pantalla";

const TODOS = [DELFINES_MANANA, DELFINES_TARDE, TIBURONES_MANANA];

describe("Grupos en la pantalla", () => {
  it("al corregir la fecha a 2018-05-05, Grupo queda en Tiburones · Mañana (sugerido)", async () => {
    const api = fingirApi({
      grupos: (fecha) => {
        if (fecha === "2020-03-10") return sugeridos(TODOS, [DELFINES_MANANA.id]);
        if (fecha === "2018-05-05") return sugeridos(TODOS, [TIBURONES_MANANA.id]);
        return TODOS;
      },
    });
    const usuario = userEvent.setup();

    await abrirRegistrar();

    // GIVEN: con 2020-03-10, la sugerencia eligio Delfines manana sin tocar Grupo.
    await escribirFecha(usuario, "2020-03-10");
    await waitFor(() => expect(textoElegido(campoGrupo())).toBe("Delfines · Mañana (sugerido)"));

    // WHEN: se corrige la fecha.
    await escribirFecha(usuario, "2018-05-05");

    // Se pidio la sugerencia para la fecha nueva...
    await waitFor(() =>
      expect(
        llamadasA(api, "GET", "/api/v1/grupos").some(
          (llamada) => parametro(llamada.url, "fecha_nacimiento") === "2018-05-05",
        ),
      ).toBe(true),
    );
    // ...y la respuesta ya llego a la pantalla: Tiburones es el sugerido.
    await waitFor(async () => {
      const opciones = await opcionesDe(usuario, campoGrupo());
      expect(opciones).toContain("Tiburones · Mañana (sugerido)");
      expect(opciones).not.toContain("Delfines · Mañana (sugerido)");
    });

    // THEN
    await waitFor(() => expect(textoElegido(campoGrupo())).toBe("Tiburones · Mañana (sugerido)"));
  });
});
