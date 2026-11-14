/**
 * Ayudas de los tests de la pantalla «Tomar asistencia» (`/asistencia`): la
 * API fingida con las formas del contrato (`GrupoParaInscribir`,
 * `AsistenciaDelGrupo`, `AlumnoEnAsistencia`, `AsistenciaEntrada`), la fecha
 * de hoy del dispositivo y la busqueda de los controles por rol y nombre.
 *
 * Como se encuentra cada cosa (lo que la pantalla tiene que respetar):
 * - `Grupo`: un `combobox` cuyo nombre accesible empieza con `Grupo`.
 * - `Fecha`: el campo cuya etiqueta es `Fecha` (un `input type="date"`).
 * - El renglon de cada alumno: un `role="group"` con nombre accesible
 *   `Nombre Apellido` (por ejemplo `Juan Pérez`).
 * - Dentro del renglon, `Presente` y `Ausente`: `button` con `aria-pressed`.
 * - `Guardar`: un `button` con nombre `Guardar`.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { expect, vi } from "vitest";
import { CLAVE_TOKEN, abrir, fingirFetch, respuestaJson, type FetchFingido } from "../auth/montar";
import { DELFINES_MANANA, coordinador, etiqueta, type Grupo } from "../alumnos/pantalla";

export {
  DELFINES_MANANA,
  DELFINES_TARDE,
  campoGrupo,
  coordinador,
  elegir,
  opcionesDe,
  profesor,
  textoElegido,
  type Grupo,
  type Usuario,
} from "../alumnos/pantalla";

// ---------------------------------------------------------------------------
// Datos con la forma del contrato
// ---------------------------------------------------------------------------

export const CABALLITOS_TARDE: Grupo = {
  id: 4,
  nombre: "Caballitos",
  turno: "tarde",
  nacimiento_desde: "2021-01-01",
  nacimiento_hasta: "2022-12-31",
  sugerido: false,
};

export interface AlumnoEnAsistencia {
  inscripcion_id: number;
  nombre: string;
  apellido: string;
  presente: boolean | null;
}

export interface AsistenciaDelGrupo {
  grupo_id: number;
  grupo: string;
  turno: "manana" | "tarde";
  fecha: string;
  alumnos: AlumnoEnAsistencia[];
}

export interface AsistenciaMarcada {
  inscripcion_id: number;
  presente: boolean;
}

/** Los tres alumnos de «Delfines» manana, en el orden en que los manda la API. */
export const MARTIN = { inscripcion_id: 101, nombre: "Martín", apellido: "Gómez" };
export const JUAN = { inscripcion_id: 102, nombre: "Juan", apellido: "Pérez" };
export const SOFIA = { inscripcion_id: 103, nombre: "Sofía", apellido: "Ruiz" };

export const HOY = "2027-01-05";

/** `AsistenciaDelGrupo` de `grupo` en `fecha`, con los alumnos y su `presente`. */
export function asistencia(
  grupo: Grupo,
  fecha: string,
  alumnos: AlumnoEnAsistencia[],
): AsistenciaDelGrupo {
  return { grupo_id: grupo.id, grupo: grupo.nombre, turno: grupo.turno, fecha, alumnos };
}

/** Los tres de Delfines manana, con `presente` para Martin, Juan y Sofia. */
export function tresAlumnos(
  martin: boolean | null,
  juan: boolean | null,
  sofia: boolean | null,
): AlumnoEnAsistencia[] {
  return [
    { ...MARTIN, presente: martin },
    { ...JUAN, presente: juan },
    { ...SOFIA, presente: sofia },
  ];
}

// ---------------------------------------------------------------------------
// La fecha de hoy del dispositivo
// ---------------------------------------------------------------------------

/**
 * Fija la fecha del dispositivo en `AAAA-MM-DD`, a las 10 de la manana
 * locales. Solo se finge `Date`, para no dormir los temporizadores de
 * `userEvent`. Se deshace con `vi.useRealTimers()` en el `afterEach`.
 */
export function fijarHoy(fecha: string = HOY) {
  const [anio, mes, dia] = fecha.split("-").map(Number) as [number, number, number];
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(anio, mes - 1, dia, 10, 0, 0));
}

// ---------------------------------------------------------------------------
// La API fingida
// ---------------------------------------------------------------------------

function ruta(url: string): string {
  return new URL(url, "http://localhost").pathname;
}

function metodo(init?: RequestInit): string {
  return (init?.method ?? "GET").toUpperCase();
}

const RUTA_ASISTENCIA = /\/api\/v1\/grupos\/(\d+)\/asistencias\/([^/]+)$/;

export interface Respuestas {
  /** El usuario de la sesion. Por defecto, un Coordinador. */
  usuario?: ReturnType<typeof coordinador>;
  /** `GET /api/v1/grupos`. Por defecto, solo «Delfines» manana. */
  grupos?: Grupo[];
  /** `GET /api/v1/grupos/{grupo_id}/asistencias/{fecha}`. */
  abrir?: (grupoId: number, fecha: string) => Response | Promise<Response>;
  /** `PUT /api/v1/grupos/{grupo_id}/asistencias/{fecha}`. */
  guardar?: (
    grupoId: number,
    fecha: string,
    cuerpo: { asistencias: AsistenciaMarcada[] },
  ) => Response | Promise<Response>;
}

/** Finge la API de la pantalla. Lo que no esta previsto responde 404. */
export function fingirApi(respuestas: Respuestas = {}): FetchFingido {
  const usuario = respuestas.usuario ?? coordinador();
  const grupos = respuestas.grupos ?? [DELFINES_MANANA];
  return fingirFetch(async (url, init) => {
    const camino = ruta(url);
    if (camino.endsWith("/api/v1/auth/yo")) return respuestaJson(200, usuario);
    if (camino.endsWith("/api/v1/grupos") && metodo(init) === "GET") {
      return respuestaJson(200, grupos);
    }
    const asistenciaPedida = RUTA_ASISTENCIA.exec(camino);
    if (asistenciaPedida) {
      const grupoId = Number(asistenciaPedida[1]);
      const fecha = asistenciaPedida[2] as string;
      if (metodo(init) === "GET" && respuestas.abrir) return respuestas.abrir(grupoId, fecha);
      if (metodo(init) === "PUT" && respuestas.guardar) {
        return respuestas.guardar(grupoId, fecha, JSON.parse(String(init?.body)));
      }
    }
    return respuestaJson(404, { detail: "No encontrado." });
  });
}

/**
 * Una respuesta 200 del `PUT` como la describe la spec: la lista entera del
 * grupo, con lo enviado aplicado sobre `antes`.
 */
export function respuestaDelGuardado(
  grupo: Grupo,
  fecha: string,
  antes: AlumnoEnAsistencia[],
  cuerpo: { asistencias: AsistenciaMarcada[] },
): Response {
  const alumnos = antes.map((alumno) => {
    const marcada = cuerpo.asistencias.find((a) => a.inscripcion_id === alumno.inscripcion_id);
    return marcada ? { ...alumno, presente: marcada.presente } : alumno;
  });
  return respuestaJson(200, asistencia(grupo, fecha, alumnos));
}

export interface Llamada {
  url: string;
  camino: string;
  metodo: string;
  cuerpo: unknown;
}

export function llamadasDe(api: FetchFingido): Llamada[] {
  return api.mock.calls.map(([entrada, init]) => {
    const url =
      typeof entrada === "string"
        ? entrada
        : entrada instanceof URL
          ? entrada.toString()
          : entrada.url;
    return {
      url,
      camino: ruta(url),
      metodo: metodo(init),
      cuerpo:
        init?.body === undefined || init?.body === null ? undefined : JSON.parse(String(init.body)),
    };
  });
}

/** Las llamadas a `metodo` sobre la asistencia de `grupoId` en `fecha`. */
export function llamadasAAsistencia(
  api: FetchFingido,
  metodoBuscado: "GET" | "PUT",
  grupoId: number,
  fecha: string,
): Llamada[] {
  const esperado = `/api/v1/grupos/${grupoId}/asistencias/${fecha}`;
  return llamadasDe(api).filter(
    (llamada) => llamada.metodo === metodoBuscado && llamada.camino.endsWith(esperado),
  );
}

/** Todos los `PUT`, a la ruta que sea. */
export function puts(api: FetchFingido): Llamada[] {
  return llamadasDe(api).filter((llamada) => llamada.metodo === "PUT");
}

/** Las marcas de un cuerpo, ordenadas por `inscripcion_id` para compararlas como conjunto. */
export function comoConjunto(asistencias: AsistenciaMarcada[]): AsistenciaMarcada[] {
  return [...asistencias].sort((a, b) => a.inscripcion_id - b.inscripcion_id);
}

// ---------------------------------------------------------------------------
// Abrir la pantalla y sus controles
// ---------------------------------------------------------------------------

/** Abre `/asistencia` con sesion y espera a que el campo `Grupo` este a la vista. */
export async function abrirAsistencia() {
  localStorage.setItem(CLAVE_TOKEN, "tok-vigente");
  abrir("/asistencia");
  await screen.findByRole("combobox", { name: /^Grupo/ });
}

export function campoFecha(): HTMLInputElement {
  return screen.getByLabelText(etiqueta("Fecha")) as HTMLInputElement;
}

/** Completa `Fecha` con un valor `AAAA-MM-DD`, como lo deja el selector del navegador. */
export async function escribirFecha(valor: string) {
  const campo = campoFecha();
  // user-event no escribe de a teclas en un input de fecha de jsdom.
  fireEvent.change(campo, { target: { value: valor } });
  await waitFor(() => expect(campo).toHaveValue(valor));
}

/** El renglon de un alumno: `role="group"` con nombre `Nombre Apellido`. */
export function renglon(nombreCompleto: string): HTMLElement {
  return screen.getByRole("group", { name: nombreCompleto });
}

export async function esperarRenglon(nombreCompleto: string): Promise<HTMLElement> {
  return screen.findByRole("group", { name: nombreCompleto });
}

export function opcion(nombreCompleto: string, cual: "Presente" | "Ausente"): HTMLElement {
  return within(renglon(nombreCompleto)).getByRole("button", { name: cual });
}

export function botonGuardar(): HTMLElement {
  return screen.getByRole("button", { name: "Guardar" });
}
