/**
 * Tests de la pantalla «Tomar asistencia» (`/asistencia`): los grupos, la
 * fecha de hoy, abrir la asistencia y mostrar la lista.
 *
 * Spec: openspec/changes/asistencia/specs/asistencia/spec.md,
 * Requirement «Pantalla «Tomar asistencia»». Un `it` por Scenario.
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { respuestaJson } from "../auth/montar";
import {
  CABALLITOS_TARDE,
  DELFINES_MANANA,
  DELFINES_TARDE,
  HOY,
  abrirAsistencia,
  asistencia,
  campoFecha,
  campoGrupo,
  elegir,
  escribirFecha,
  esperarRenglon,
  fijarHoy,
  fingirApi,
  llamadasAAsistencia,
  opcion,
  opcionesDe,
  profesor,
  renglon,
  textoElegido,
  tresAlumnos,
} from "./pantalla";

afterEach(() => {
  vi.useRealTimers();
});

describe("Pantalla «Tomar asistencia»", () => {
  it("un Profesor ve como únicas opciones de Grupo Delfines · Mañana y Delfines · Tarde, sin elegir", async () => {
    fijarHoy(HOY);
    fingirApi({ usuario: profesor(), grupos: [DELFINES_MANANA, DELFINES_TARDE] });
    const usuario = userEvent.setup();

    await abrirAsistencia();

    await waitFor(async () => {
      expect(await opcionesDe(usuario, campoGrupo())).toEqual([
        "Delfines · Mañana",
        "Delfines · Tarde",
      ]);
    });
    expect(textoElegido(campoGrupo())).toBe("");
  });

  it("con un solo grupo, Grupo queda en Delfines · Mañana, Fecha en 2027-01-05 y se ven los tres alumnos en orden sin elegir", async () => {
    fijarHoy("2027-01-05");
    const api = fingirApi({
      grupos: [DELFINES_MANANA],
      abrir: (grupoId, fecha) =>
        grupoId === DELFINES_MANANA.id && fecha === "2027-01-05"
          ? respuestaJson(200, asistencia(DELFINES_MANANA, fecha, tresAlumnos(null, null, null)))
          : respuestaJson(404, { detail: "El grupo no existe." }),
    });

    await abrirAsistencia();

    await waitFor(() => expect(textoElegido(campoGrupo())).toBe("Delfines · Mañana"));
    expect(campoFecha()).toHaveValue("2027-01-05");

    // Abrio la asistencia de hoy de ese grupo.
    await waitFor(() =>
      expect(llamadasAAsistencia(api, "GET", DELFINES_MANANA.id, "2027-01-05")).toHaveLength(1),
    );

    const martin = await esperarRenglon("Martín Gómez");
    const juan = renglon("Juan Pérez");
    const sofia = renglon("Sofía Ruiz");

    // En ese orden: Martin antes que Juan, Juan antes que Sofia.
    expect(martin.compareDocumentPosition(juan) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(juan.compareDocumentPosition(sofia) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    for (const nombre of ["Martín Gómez", "Juan Pérez", "Sofía Ruiz"]) {
      expect(opcion(nombre, "Presente")).toHaveAttribute("aria-pressed", "false");
      expect(opcion(nombre, "Ausente")).toHaveAttribute("aria-pressed", "false");
    }
  });

  it("al escribir 2027-01-04 en Fecha se pide esa asistencia y Martín Gómez tiene elegido Ausente", async () => {
    fijarHoy("2027-01-05");
    const api = fingirApi({
      grupos: [DELFINES_MANANA],
      abrir: (grupoId, fecha) => {
        if (grupoId !== DELFINES_MANANA.id) {
          return respuestaJson(404, { detail: "El grupo no existe." });
        }
        if (fecha === "2027-01-04") {
          return respuestaJson(
            200,
            asistencia(DELFINES_MANANA, fecha, tresAlumnos(false, null, null)),
          );
        }
        return respuestaJson(
          200,
          asistencia(DELFINES_MANANA, fecha, tresAlumnos(null, null, null)),
        );
      },
    });

    // GIVEN: abierta en Delfines manana del 2027-01-05, con Martin sin tomar.
    await abrirAsistencia();
    await esperarRenglon("Martín Gómez");
    expect(opcion("Martín Gómez", "Ausente")).toHaveAttribute("aria-pressed", "false");

    // WHEN
    await escribirFecha("2027-01-04");

    // THEN
    await waitFor(() =>
      expect(llamadasAAsistencia(api, "GET", DELFINES_MANANA.id, "2027-01-04")).toHaveLength(1),
    );
    await waitFor(() =>
      expect(opcion("Martín Gómez", "Ausente")).toHaveAttribute("aria-pressed", "true"),
    );
    expect(opcion("Martín Gómez", "Presente")).toHaveAttribute("aria-pressed", "false");
  });

  it("al elegir Caballitos · Tarde sin inscriptos se ve el aviso y no está el botón Guardar", async () => {
    fijarHoy("2027-01-05");
    const api = fingirApi({
      grupos: [DELFINES_MANANA, CABALLITOS_TARDE],
      abrir: (grupoId, fecha) =>
        grupoId === CABALLITOS_TARDE.id
          ? respuestaJson(200, asistencia(CABALLITOS_TARDE, fecha, []))
          : respuestaJson(200, asistencia(DELFINES_MANANA, fecha, tresAlumnos(null, null, null))),
    });
    const usuario = userEvent.setup();

    await abrirAsistencia();
    await waitFor(async () => {
      expect(await opcionesDe(usuario, campoGrupo())).toContain("Caballitos · Tarde");
    });

    await elegir(usuario, campoGrupo(), "Caballitos · Tarde");

    await waitFor(() =>
      expect(llamadasAAsistencia(api, "GET", CABALLITOS_TARDE.id, "2027-01-05")).toHaveLength(1),
    );
    expect(await screen.findByText("No hay alumnos inscriptos en este grupo.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Guardar" })).not.toBeInTheDocument();
  });
});
