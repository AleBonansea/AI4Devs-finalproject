/**
 * Ayudas de los tests de la pantalla «Registrar cargo» (`/cargos/nuevo`): la
 * API fingida con las formas del contrato (`FamiliaEncontrada`,
 * `InscripcionDeFamilia`, `OpcionesDeCargo`, `CargoEntrada`, `CargoSimulado`,
 * `CargoRegistrado`), los controles buscados por rol y etiqueta y las
 * acciones de una persona.
 *
 * Como se encuentra cada cosa (lo que la pantalla tiene que respetar):
 * - `Familia`: un `combobox` (el buscador por apellido) con nombre `Familia`.
 * - `Alumno y turno`, `Tipo de cargo`, `Modalidad` y `Período`: `combobox`
 *   con ese nombre (los `TextField select` de MUI).
 * - `Fecha`: el campo cuya etiqueta es `Fecha` (un `input type="date"`).
 * - `Registrar cargo`: un `button` con ese nombre.
 * - Un renglon del desglose: el texto del renglon y, en el contenedor mas
 *   cercano que lo incluye, su monto o porcentaje (ver `renglonDelDesglose`).
 */
import { screen, waitFor } from "@testing-library/react";
import { expect } from "vitest";
import {
  CLAVE_TOKEN,
  abrir,
  fingirFetch,
  respuestaJson,
  usuarioYo,
  type FetchFingido,
} from "../auth/montar";
import { contiene, elegir, etiqueta, type Usuario } from "../alumnos/pantalla";

export {
  contiene,
  elegir,
  esperar,
  etiqueta,
  opcionesDe,
  porTexto,
  textoElegido,
  type Usuario,
} from "../alumnos/pantalla";
export { sinRespuesta } from "../auth/montar";

// ---------------------------------------------------------------------------
// Datos con la forma del contrato
// ---------------------------------------------------------------------------

export type Categoria = "socio" | "empleado" | "no_socio";

export interface FamiliaEncontrada {
  id: number;
  etiqueta: string;
  categoria: Categoria;
}

export interface InscripcionDeFamilia {
  inscripcion_id: number;
  alumno_id: number;
  nombre: string;
  apellido: string;
  turno: "manana" | "tarde";
  grupo: string;
}

export interface CargoSimulado {
  familia_id: number;
  categoria_aplicada: Categoria;
  cantidad_hijos_aplicada: number | null;
  monto_base: string;
  porcentaje_aplicado: string;
  monto_total: string;
}

export type CuerpoCargo = Record<string, unknown>;

export const FAMILIA_PEREZ_ANA: FamiliaEncontrada = {
  id: 40,
  etiqueta: "Pérez – Ana",
  categoria: "empleado",
};

export const FAMILIA_SIN_HIJOS: FamiliaEncontrada = {
  id: 41,
  etiqueta: "Gómez – Lía",
  categoria: "socio",
};

export const ANA_TIBURONES_MANANA: InscripcionDeFamilia = {
  inscripcion_id: 201,
  alumno_id: 30,
  nombre: "Ana",
  apellido: "Pérez",
  turno: "manana",
  grupo: "Tiburones",
};

export const JUAN_DELFINES_MANANA: InscripcionDeFamilia = {
  inscripcion_id: 202,
  alumno_id: 31,
  nombre: "Juan",
  apellido: "Pérez",
  turno: "manana",
  grupo: "Delfines",
};

export const JUAN_PULPOS_TARDE: InscripcionDeFamilia = {
  inscripcion_id: 203,
  alumno_id: 31,
  nombre: "Juan",
  apellido: "Pérez",
  turno: "tarde",
  grupo: "Pulpos",
};

export const INSCRIPCIONES_PEREZ = [ANA_TIBURONES_MANANA, JUAN_DELFINES_MANANA, JUAN_PULPOS_TARDE];

export const ABONO = { id: 1, nombre: "Abono", calculo: "tarifario", monto_fijo: null };
export const PREINSCRIPCION = {
  id: 2,
  nombre: "Preinscripción",
  calculo: "monto_fijo",
  monto_fijo: "20000.00",
};

export const MES_1 = {
  id: 11,
  modalidad: "mes",
  nombre: "Mes 1",
  fecha_desde: "2027-01-04",
  fecha_hasta: "2027-01-29",
};
export const MES_2 = {
  id: 12,
  modalidad: "mes",
  nombre: "Mes 2",
  fecha_desde: "2027-02-01",
  fecha_hasta: "2027-02-26",
};
export const QUINCENA_1 = {
  id: 21,
  modalidad: "quincena",
  nombre: "Quincena 1",
  fecha_desde: "2027-01-04",
  fecha_hasta: "2027-01-15",
};
export const SEMANA_1 = {
  id: 31,
  modalidad: "semana",
  nombre: "Semana 1",
  fecha_desde: "2027-01-04",
  fecha_hasta: "2027-01-08",
};

/** Como se escriben las opciones de `Período` del Mes. */
export const OPCION_MES_1 = "Mes 1 · 04/01/2027 al 29/01/2027";
export const OPCION_MES_2 = "Mes 2 · 01/02/2027 al 26/02/2027";

export const OPCIONES = {
  tipos_cargo: [ABONO, PREINSCRIPCION],
  periodos: [MES_1, MES_2, QUINCENA_1, SEMANA_1],
};

/** La simulacion del «Abono» del Mes de Juan, «Mes 1», como la fija la spec. */
export const SIMULADO_ABONO_MES_1: CargoSimulado = {
  familia_id: FAMILIA_PEREZ_ANA.id,
  categoria_aplicada: "empleado",
  cantidad_hijos_aplicada: 2,
  monto_base: "100000.00",
  porcentaje_aplicado: "15.00",
  monto_total: "85000.00",
};

/** La simulacion de la «Preinscripción», como la fija la spec. */
export const SIMULADO_PREINSCRIPCION: CargoSimulado = {
  familia_id: FAMILIA_PEREZ_ANA.id,
  categoria_aplicada: "empleado",
  cantidad_hijos_aplicada: null,
  monto_base: "20000.00",
  porcentaje_aplicado: "0.00",
  monto_total: "20000.00",
};

export const MENSAJE_REPETIDO =
  "El alumno ya tiene un cargo «Abono» de «Mes 1» en el turno mañana.";

export function admin() {
  return usuarioYo({
    nombre: "Marta",
    apellido: "García",
    rol: "admin",
    debe_cambiar_password: false,
  });
}

/** Un `CargoRegistrado` armado con lo enviado, el desglose y el saldo. */
export function cargoRegistrado(
  cuerpo: CuerpoCargo,
  desglose: CargoSimulado,
  saldoPendiente: string,
) {
  return {
    ...desglose,
    id: 900,
    temporada_id: 3,
    alumno_id: cuerpo.alumno_id,
    tipo_cargo_id: cuerpo.tipo_cargo_id,
    inscripcion_id: cuerpo.inscripcion_id ?? null,
    modalidad: cuerpo.modalidad ?? null,
    periodo_cobro_id: cuerpo.periodo_cobro_id ?? null,
    fecha_dia: cuerpo.fecha_dia ?? null,
    creado_por: 7,
    creado_en: "2027-01-05T10:00:00-03:00",
    saldo_pendiente: saldoPendiente,
  };
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

const RUTA_INSCRIPCIONES = /\/api\/v1\/familias\/(\d+)\/inscripciones$/;

export interface Respuestas {
  /** `GET /api/v1/familias?apellido=`. Por defecto, «Pérez – Ana». */
  familias?: (apellido: string) => FamiliaEncontrada[];
  /** `GET /api/v1/familias/{id}/inscripciones`. Por defecto, las tres de los Pérez. */
  inscripciones?: (familiaId: number) => InscripcionDeFamilia[];
  /** `POST /api/v1/cargos/simulacion`. Por defecto, segun el tipo. */
  simular?: (cuerpo: CuerpoCargo) => Response | Promise<Response>;
  /** `POST /api/v1/cargos`. */
  registrar?: (cuerpo: CuerpoCargo) => Response | Promise<Response>;
}

/** Simulacion por defecto: la de la spec para el tipo enviado. */
function simulacionPorDefecto(cuerpo: CuerpoCargo): Response {
  if (cuerpo.tipo_cargo_id === PREINSCRIPCION.id) {
    return respuestaJson(200, SIMULADO_PREINSCRIPCION);
  }
  return respuestaJson(200, SIMULADO_ABONO_MES_1);
}

/** Finge la API de la pantalla con la sesion de un Admin. Lo no previsto responde 404. */
export function fingirApi(respuestas: Respuestas = {}): FetchFingido {
  const familias = respuestas.familias ?? (() => [FAMILIA_PEREZ_ANA]);
  const inscripciones = respuestas.inscripciones ?? (() => INSCRIPCIONES_PEREZ);
  const simular = respuestas.simular ?? simulacionPorDefecto;
  return fingirFetch(async (url, init) => {
    const camino = ruta(url);
    const verbo = metodo(init);
    if (camino.endsWith("/api/v1/auth/yo")) return respuestaJson(200, admin());
    if (camino.endsWith("/api/v1/grupos") && verbo === "GET") return respuestaJson(200, []);
    if (camino.endsWith("/api/v1/familias") && verbo === "GET") {
      const apellido = new URL(url, "http://localhost").searchParams.get("apellido") ?? "";
      return respuestaJson(200, familias(apellido));
    }
    const deFamilia = RUTA_INSCRIPCIONES.exec(camino);
    if (deFamilia && verbo === "GET") {
      return respuestaJson(200, inscripciones(Number(deFamilia[1])));
    }
    if (camino.endsWith("/api/v1/cargos/opciones") && verbo === "GET") {
      return respuestaJson(200, OPCIONES);
    }
    if (camino.endsWith("/api/v1/cargos/simulacion") && verbo === "POST") {
      return simular(JSON.parse(String(init?.body)) as CuerpoCargo);
    }
    if (camino.endsWith("/api/v1/cargos") && verbo === "POST" && respuestas.registrar) {
      return respuestas.registrar(JSON.parse(String(init?.body)) as CuerpoCargo);
    }
    return respuestaJson(404, { detail: "No encontrado." });
  });
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

/** Los cuerpos de los `POST /api/v1/cargos/simulacion`. */
export function simulaciones(api: FetchFingido): CuerpoCargo[] {
  return llamadasDe(api)
    .filter((l) => l.metodo === "POST" && l.camino.endsWith("/api/v1/cargos/simulacion"))
    .map((l) => l.cuerpo as CuerpoCargo);
}

/** Los cuerpos de los `POST /api/v1/cargos`. */
export function registros(api: FetchFingido): CuerpoCargo[] {
  return llamadasDe(api)
    .filter((l) => l.metodo === "POST" && l.camino.endsWith("/api/v1/cargos"))
    .map((l) => l.cuerpo as CuerpoCargo);
}

// ---------------------------------------------------------------------------
// Abrir la pantalla y sus controles
// ---------------------------------------------------------------------------

/** Abre `/cargos/nuevo` con la sesion guardada y espera el buscador `Familia`. */
export async function abrirRegistrarCargo() {
  localStorage.setItem(CLAVE_TOKEN, "tok-admin");
  abrir("/cargos/nuevo");
  await screen.findByRole("combobox", { name: etiqueta("Familia") });
}

export function campoFamilia(): HTMLElement {
  return screen.getByRole("combobox", { name: etiqueta("Familia") });
}

export type Lista = "Alumno y turno" | "Tipo de cargo" | "Modalidad" | "Período";

export function lista(nombre: Lista): HTMLElement {
  return screen.getByRole("combobox", { name: etiqueta(nombre) });
}

export function listaSiHay(nombre: Lista): HTMLElement | null {
  return screen.queryByRole("combobox", { name: etiqueta(nombre) });
}

export function campoFechaSiHay(): HTMLElement | null {
  return screen.queryByLabelText(etiqueta("Fecha"));
}

export function botonRegistrar(): HTMLElement {
  return screen.getByRole("button", { name: "Registrar cargo" });
}

/** Escribe `apellido` en `Familia` y elige la opcion de `etiquetaFamilia`. */
export async function elegirFamilia(usuario: Usuario, apellido: string, etiquetaFamilia: string) {
  await usuario.type(campoFamilia(), apellido);
  const opcion = await screen.findByRole("option", { name: contiene(etiquetaFamilia) });
  await usuario.click(opcion);
}

/** Elige en una lista, esperando antes a que este a la vista. */
export async function elegirEn(usuario: Usuario, nombre: Lista, opcion: string) {
  const campo = await screen.findByRole("combobox", { name: etiqueta(nombre) });
  await elegir(usuario, campo, opcion);
}

/** Familia «Pérez – Ana» y `Juan Pérez · Mañana`. */
export async function elegirJuanManana(usuario: Usuario) {
  await elegirFamilia(usuario, "Pér", FAMILIA_PEREZ_ANA.etiqueta);
  await elegirEn(usuario, "Alumno y turno", "Juan Pérez · Mañana");
}

/** Familia, `Juan Pérez · Mañana`, «Abono», `Mes` y `periodo` elegidos. */
export async function elegirAbonoMes(usuario: Usuario, periodo: string = OPCION_MES_1) {
  await elegirJuanManana(usuario);
  await elegirEn(usuario, "Tipo de cargo", "Abono");
  await elegirEn(usuario, "Modalidad", "Mes");
  await elegirEn(usuario, "Período", periodo);
}

// ---------------------------------------------------------------------------
// El desglose
// ---------------------------------------------------------------------------

function normalizar(texto: string | null | undefined): string {
  return (texto ?? "")
    .replace(new RegExp(String.fromCharCode(0x200b), "g"), "")
    .replace(/\s+/g, " ")
    .trim();
}

/** El elemento mas profundo cuyo texto entero es `texto`. */
function elementoConTexto(texto: string): HTMLElement {
  const candidatos = Array.from(document.body.querySelectorAll<HTMLElement>("*")).filter(
    (el) =>
      normalizar(el.textContent) === texto &&
      !Array.from(el.children).some((hijo) => normalizar(hijo.textContent) === texto),
  );
  expect(candidatos, `no se ve «${texto}»`).toHaveLength(1);
  return candidatos[0] as HTMLElement;
}

/**
 * El renglon del desglose cuyo texto es `texto`: el contenedor mas cercano
 * que tiene a la vez ese texto y `valor`. Comprueba que ese contenedor no
 * incluye los textos de los otros renglones, es decir, que `valor` es de ese
 * renglon y no de otro.
 */
export function renglonDelDesglose(texto: string, valor: string, otros: string[]): HTMLElement {
  let actual: HTMLElement | null = elementoConTexto(texto);
  while (actual && !normalizar(actual.textContent).includes(valor)) {
    actual = actual.parentElement;
  }
  expect(actual, `«${texto}» no tiene al lado «${valor}»`).not.toBeNull();
  const contenido = normalizar((actual as HTMLElement).textContent);
  for (const otro of otros) {
    expect(contenido, `«${valor}» no es del renglon «${texto}»`).not.toContain(otro);
  }
  return actual as HTMLElement;
}

/** Espera el renglon (aparece despues de la respuesta de la simulacion). */
export async function esperarRenglon(texto: string, valor: string, otros: string[]) {
  let encontrado: HTMLElement | undefined;
  await waitFor(() => {
    encontrado = renglonDelDesglose(texto, valor, otros);
  });
  return encontrado as HTMLElement;
}

export const TARIFA_MANANA_MES = "Tarifa base · Mañana · Mes";
export const DESCUENTO_EMPLEADO_2 = "Descuento Empleado · 2 hijos en el turno";
export const TOTAL = "Total del cargo";
export const RENGLONES_ABONO = [TARIFA_MANANA_MES, DESCUENTO_EMPLEADO_2, TOTAL];

export function otrosQue(texto: string, renglones: string[]): string[] {
  return renglones.filter((r) => r !== texto);
}

/** Todo el texto de la pagina, para afirmar que un monto no aparece en ningun lado. */
export function textoDeLaPagina(): string {
  return normalizar(document.body.textContent);
}
