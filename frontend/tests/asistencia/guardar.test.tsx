/**
 * Tests del guardado desde la pantalla «Tomar asistencia».
 *
 * Spec: openspec/changes/asistencia/specs/asistencia/spec.md,
 * Requirement «Guardar desde la pantalla». Un `it` por Scenario.
 *
 * El cuerpo del `PUT` se compara como conjunto (ordenado por
 * `inscripcion_id` antes de comparar): la spec dice «exactamente esas tres
 * inscripciones», no en que orden, y la API no depende del orden. Lo que si
 * se exige es exacto: ni una inscripcion de mas, ni un campo de mas.
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { respuestaJson } from "../auth/montar";
import {
  DELFINES_MANANA,
  JUAN,
  MARTIN,
  SOFIA,
  abrirAsistencia,
  asistencia,
  botonGuardar,
  comoConjunto,
  esperarRenglon,
  fijarHoy,
  fingirApi,
  llamadasAAsistencia,
  opcion,
  puts,
  respuestaDelGuardado,
  tresAlumnos,
  type AlumnoEnAsistencia,
  type AsistenciaMarcada,
} from "./pantalla";

const URL_PUT = `/api/v1/grupos/${DELFINES_MANANA.id}/asistencias/2027-01-05`;

afterEach(() => {
  vi.useRealTimers();
});

/**
 * Abre `/asistencia` en Delfines manana del 2027-01-05 (unico grupo, hoy
 * fijado) con `antes` como respuesta del `GET`, y el `PUT` respondiendo con
 * `guardar` o, por defecto, con la lista entera y lo enviado aplicado.
 */
async function abrirDelfines(
  antes: AlumnoEnAsistencia[],
  guardar?: (cuerpo: { asistencias: AsistenciaMarcada[] }) => Response,
) {
  fijarHoy("2027-01-05");
  const api = fingirApi({
    grupos: [DELFINES_MANANA],
    abrir: (grupoId, fecha) =>
      grupoId === DELFINES_MANANA.id
        ? respuestaJson(200, asistencia(DELFINES_MANANA, fecha, antes))
        : respuestaJson(404, { detail: "El grupo no existe." }),
    guardar: (_grupoId, fecha, cuerpo) =>
      guardar ? guardar(cuerpo) : respuestaDelGuardado(DELFINES_MANANA, fecha, antes, cuerpo),
  });
  await abrirAsistencia();
  await esperarRenglon("Martín Gómez");
  return api;
}

/** El unico `PUT` enviado: metodo, ruta y cuerpo. */
async function unicoPut(api: ReturnType<typeof fingirApi>) {
  await waitFor(() => expect(puts(api)).toHaveLength(1));
  const llamada = puts(api)[0]!;
  expect(llamada.metodo).toBe("PUT");
  expect(llamada.camino.endsWith(URL_PUT)).toBe(true);
  expect(llamadasAAsistencia(api, "PUT", DELFINES_MANANA.id, "2027-01-05")).toHaveLength(1);
  const cuerpo = llamada.cuerpo as { asistencias: AsistenciaMarcada[] };
  expect(Object.keys(cuerpo)).toEqual(["asistencias"]);
  for (const marcada of cuerpo.asistencias) {
    expect(Object.keys(marcada).sort()).toEqual(["inscripcion_id", "presente"]);
  }
  return cuerpo;
}

describe("Guardar desde la pantalla", () => {
  it("el PUT lleva exactamente las tres inscripciones marcadas y se ve Asistencia guardada.", async () => {
    const api = await abrirDelfines(tresAlumnos(null, null, null));
    const usuario = userEvent.setup();

    await usuario.click(opcion("Juan Pérez", "Presente"));
    await usuario.click(opcion("Sofía Ruiz", "Presente"));
    await usuario.click(opcion("Martín Gómez", "Ausente"));
    await usuario.click(botonGuardar());

    const cuerpo = await unicoPut(api);
    expect(comoConjunto(cuerpo.asistencias)).toEqual(
      comoConjunto([
        { inscripcion_id: JUAN.inscripcion_id, presente: true },
        { inscripcion_id: SOFIA.inscripcion_id, presente: true },
        { inscripcion_id: MARTIN.inscripcion_id, presente: false },
      ]),
    );
    expect(await screen.findByText("Asistencia guardada.")).toBeInTheDocument();
  });

  it("al marcar solo a Juan Pérez el PUT lleva solo su inscripción con presente true", async () => {
    const api = await abrirDelfines(tresAlumnos(null, null, null));
    const usuario = userEvent.setup();

    await usuario.click(opcion("Juan Pérez", "Presente"));
    await usuario.click(botonGuardar());

    const cuerpo = await unicoPut(api);
    expect(cuerpo.asistencias).toEqual([{ inscripcion_id: JUAN.inscripcion_id, presente: true }]);
    expect(await screen.findByText("Asistencia guardada.")).toBeInTheDocument();
  });

  it("sin ninguna opción elegida el botón Guardar está deshabilitado y no se envía el PUT", async () => {
    const api = await abrirDelfines(tresAlumnos(null, null, null));

    expect(renglonesSinElegir()).toBe(true);
    expect(botonGuardar()).toBeDisabled();
    expect(puts(api)).toHaveLength(0);
  });

  it("al corregir a Martín Gómez a Presente el PUT lleva las tres inscripciones, con Martín presente true", async () => {
    const api = await abrirDelfines(tresAlumnos(false, true, true));
    const usuario = userEvent.setup();

    // Lo ya tomado llego a la pantalla antes de corregir.
    await waitFor(() =>
      expect(opcion("Martín Gómez", "Ausente")).toHaveAttribute("aria-pressed", "true"),
    );

    await usuario.click(opcion("Martín Gómez", "Presente"));
    await usuario.click(botonGuardar());

    const cuerpo = await unicoPut(api);
    expect(comoConjunto(cuerpo.asistencias)).toEqual(
      comoConjunto([
        { inscripcion_id: MARTIN.inscripcion_id, presente: true },
        { inscripcion_id: JUAN.inscripcion_id, presente: true },
        { inscripcion_id: SOFIA.inscripcion_id, presente: true },
      ]),
    );
  });

  it("si el PUT responde 409 se ve El grupo no está activo., Juan Pérez sigue en Presente y no se ve Asistencia guardada.", async () => {
    const api = await abrirDelfines(tresAlumnos(null, null, null), () =>
      respuestaJson(409, { detail: "El grupo no está activo." }),
    );
    const usuario = userEvent.setup();

    await usuario.click(opcion("Juan Pérez", "Presente"));
    await usuario.click(botonGuardar());

    await unicoPut(api);
    expect(await screen.findByText("El grupo no está activo.")).toBeInTheDocument();
    expect(opcion("Juan Pérez", "Presente")).toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByText("Asistencia guardada.")).not.toBeInTheDocument();
  });
});

/** Los tres renglones estan a la vista y ninguno tiene una opcion elegida. */
function renglonesSinElegir(): boolean {
  return ["Martín Gómez", "Juan Pérez", "Sofía Ruiz"].every(
    (nombre) =>
      opcion(nombre, "Presente").getAttribute("aria-pressed") === "false" &&
      opcion(nombre, "Ausente").getAttribute("aria-pressed") === "false",
  );
}
