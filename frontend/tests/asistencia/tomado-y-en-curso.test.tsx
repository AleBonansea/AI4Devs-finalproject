/**
 * Tests de lo ya tomado y del guardado en curso en la pantalla «Tomar
 * asistencia».
 *
 * Spec: openspec/changes/asistencia/specs/asistencia/spec.md,
 * Requirement «Lo ya tomado y el guardado en curso». Un `it` por Scenario.
 *
 * Deshabilitado se comprueba con `estaDeshabilitado`, que vale tanto para el
 * atributo `disabled` (boton, input nativo, select nativo) como para
 * `aria-disabled="true"` (el combobox de un select de MUI).
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { respuestaJson } from "../auth/montar";
import {
  DELFINES_MANANA,
  JUAN,
  abrirAsistencia,
  asistencia,
  botonGuardar,
  campoFecha,
  campoGrupo,
  esperarRenglon,
  fijarHoy,
  fingirApi,
  opcion,
  puts,
  respuestaDelGuardado,
  tresAlumnos,
  type AlumnoEnAsistencia,
  type AsistenciaMarcada,
} from "./pantalla";

afterEach(() => {
  vi.useRealTimers();
});

/**
 * Abre `/asistencia` en Delfines manana del 2027-01-05 (unico grupo, hoy
 * fijado) con `antes` como respuesta del `GET`. El `PUT` responde con
 * `guardar` o, por defecto, con la lista entera y lo enviado aplicado.
 */
async function abrirDelfines(
  antes: AlumnoEnAsistencia[],
  guardar?: (cuerpo: { asistencias: AsistenciaMarcada[] }) => Response | Promise<Response>,
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

/** Espera a que lo ya tomado (Martin ausente, Juan y Sofia presentes) este en pantalla. */
async function esperarLoTomado() {
  await waitFor(() => {
    expect(opcion("Martín Gómez", "Ausente")).toHaveAttribute("aria-pressed", "true");
    expect(opcion("Juan Pérez", "Presente")).toHaveAttribute("aria-pressed", "true");
    expect(opcion("Sofía Ruiz", "Presente")).toHaveAttribute("aria-pressed", "true");
  });
}

/** Deshabilitado como lo ve un lector de pantalla: `disabled` o `aria-disabled="true"`. */
function estaDeshabilitado(elemento: HTMLElement): boolean {
  const nativo = (elemento as HTMLButtonElement | HTMLInputElement | HTMLSelectElement).disabled;
  return nativo === true || elemento.getAttribute("aria-disabled") === "true";
}

describe("Lo ya tomado y el guardado en curso", () => {
  it("con lo ya tomado sin cambios, o Martín Gómez a Presente y otra vez a Ausente, el botón Guardar está deshabilitado", async () => {
    const api = await abrirDelfines(tresAlumnos(false, true, true));
    const usuario = userEvent.setup();
    await esperarLoTomado();

    // Rama 1: no se cambia nada.
    expect(botonGuardar()).toBeDisabled();

    // Rama 2: Presente para Martin y despues otra vez Ausente.
    await usuario.click(opcion("Martín Gómez", "Presente"));
    await waitFor(() =>
      expect(opcion("Martín Gómez", "Presente")).toHaveAttribute("aria-pressed", "true"),
    );
    await usuario.click(opcion("Martín Gómez", "Ausente"));
    await waitFor(() =>
      expect(opcion("Martín Gómez", "Ausente")).toHaveAttribute("aria-pressed", "true"),
    );
    expect(opcion("Martín Gómez", "Presente")).toHaveAttribute("aria-pressed", "false");

    expect(botonGuardar()).toBeDisabled();
    expect(puts(api)).toHaveLength(0);
  });

  it("al pulsar Ausente de Martín Gómez ya tomado sigue con Ausente elegido y Guardar deshabilitado", async () => {
    await abrirDelfines(tresAlumnos(false, true, true));
    const usuario = userEvent.setup();
    await esperarLoTomado();

    await usuario.click(opcion("Martín Gómez", "Ausente"));

    expect(opcion("Martín Gómez", "Ausente")).toHaveAttribute("aria-pressed", "true");
    expect(opcion("Martín Gómez", "Presente")).toHaveAttribute("aria-pressed", "false");
    expect(botonGuardar()).toBeDisabled();
  });

  it("al volver a pulsar Presente de Juan Pérez sin guardar queda sin opción elegida y Guardar deshabilitado", async () => {
    await abrirDelfines(tresAlumnos(null, null, null));
    const usuario = userEvent.setup();

    await usuario.click(opcion("Juan Pérez", "Presente"));
    await waitFor(() =>
      expect(opcion("Juan Pérez", "Presente")).toHaveAttribute("aria-pressed", "true"),
    );

    await usuario.click(opcion("Juan Pérez", "Presente"));

    await waitFor(() =>
      expect(opcion("Juan Pérez", "Presente")).toHaveAttribute("aria-pressed", "false"),
    );
    expect(opcion("Juan Pérez", "Ausente")).toHaveAttribute("aria-pressed", "false");
    expect(botonGuardar()).toBeDisabled();
  });

  it("mientras el PUT no responde Grupo, Fecha y Guardar están deshabilitados, y con 200 Grupo y Fecha se habilitan y se ve Asistencia guardada.", async () => {
    const antes = tresAlumnos(null, null, null);
    let liberar: ((respuesta: Response) => void) | undefined;
    const respuestaRetenida = new Promise<Response>((resolver) => {
      liberar = resolver;
    });
    let cuerpoEnviado: { asistencias: AsistenciaMarcada[] } | undefined;
    const api = await abrirDelfines(antes, (cuerpo) => {
      cuerpoEnviado = cuerpo;
      return respuestaRetenida;
    });
    const usuario = userEvent.setup();

    // Antes de guardar, Grupo y Fecha estan habilitados.
    expect(estaDeshabilitado(campoGrupo())).toBe(false);
    expect(estaDeshabilitado(campoFecha())).toBe(false);

    await usuario.click(opcion("Juan Pérez", "Presente"));
    await usuario.click(botonGuardar());

    // El PUT salio y todavia no respondio.
    await waitFor(() => expect(puts(api)).toHaveLength(1));
    await waitFor(() => {
      expect(estaDeshabilitado(campoGrupo())).toBe(true);
      expect(estaDeshabilitado(campoFecha())).toBe(true);
      expect(estaDeshabilitado(botonGuardar())).toBe(true);
    });

    // Responde 200.
    expect(cuerpoEnviado).toEqual({
      asistencias: [{ inscripcion_id: JUAN.inscripcion_id, presente: true }],
    });
    liberar!(respuestaDelGuardado(DELFINES_MANANA, "2027-01-05", antes, cuerpoEnviado!));

    expect(await screen.findByText("Asistencia guardada.")).toBeInTheDocument();
    await waitFor(() => {
      expect(estaDeshabilitado(campoGrupo())).toBe(false);
      expect(estaDeshabilitado(campoFecha())).toBe(false);
    });
  });
});
