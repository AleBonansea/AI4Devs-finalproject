/**
 * Ayudas de los tests de la pantalla «Cuenta corriente» (`/cuenta-corriente`):
 * la API fingida con las formas del contrato (`FamiliaEncontrada`,
 * `CuentaCorriente`, `CargoEnCuenta`, `PagoEnCuenta`, `PeriodoDeCargo`), y
 * como se encuentra cada cosa en pantalla.
 *
 * Como se encuentra cada cosa (lo que la pantalla tiene que respetar):
 * - `Familia`: un `combobox` con nombre `Familia` (el mismo buscador que en
 *   «Registrar cargo»).
 * - Un valor con su etiqueta (`Saldo pendiente` `$ 60.000`): el elemento mas
 *   profundo cuyo texto contiene la etiqueta y, en el contenedor mas cercano
 *   que lo incluye, el valor (ver `valorJunto`).
 * - Un renglon de cargo: el elemento mas profundo cuyo texto entero es su
 *   descripcion (`Abono · Mes 1`) y, subiendo, el contenedor mas cercano que
 *   tiene ademas todos los textos esperados de ese renglon. Ese contenedor no
 *   puede incluir la descripcion de otro renglon ni `Saldo pendiente` (que es
 *   de la familia, no de un cargo): asi lo que se ve en el se atribuye a ESE
 *   cargo (ver `renglonDeCargo`).
 * - `Total`, `Pagado` y `Saldo` de un renglon: la etiqueta seguida de su
 *   monto en el texto del renglon, admitiendo `:` y espacios en el medio.
 */
import { screen, waitFor } from "@testing-library/react";
import { expect } from "vitest";
import { CLAVE_TOKEN, abrir, fingirFetch, respuestaJson, type FetchFingido } from "../auth/montar";
import {
  FAMILIA_PEREZ_ANA,
  admin,
  etiqueta,
  type Categoria,
  type FamiliaEncontrada,
} from "../cargos/pantalla";

export { FAMILIA_PEREZ_ANA, elegirFamilia, esperar, type Usuario } from "../cargos/pantalla";
export { respuestaJson } from "../auth/montar";

// ---------------------------------------------------------------------------
// Datos con la forma del contrato
// ---------------------------------------------------------------------------

export interface PagoEnCuenta {
  id: number;
  monto: string;
  fecha_pago: string;
}

export interface PeriodoDeCargo {
  nombre: string;
  fecha_desde: string;
  fecha_hasta: string;
}

export interface CargoEnCuenta {
  id: number;
  alumno_id: number;
  nombre: string;
  apellido: string;
  tipo_cargo: string;
  modalidad: "mes" | "quincena" | "semana" | "dia" | null;
  turno: "manana" | "tarde" | null;
  periodo: PeriodoDeCargo | null;
  fecha_dia: string | null;
  monto_total: string;
  pagado: string;
  saldo: string;
  creado_en: string;
  pagos: PagoEnCuenta[];
}

export interface CuentaCorriente {
  familia_id: number;
  etiqueta: string;
  categoria: Categoria;
  total_cargos: string;
  total_pagado: string;
  saldo_pendiente: string;
  cargos: CargoEnCuenta[];
}

export const FAMILIA_GOMEZ_LUCIA: FamiliaEncontrada = {
  id: 52,
  etiqueta: "Gómez – Lucía",
  categoria: "socio",
};

export const MES_1: PeriodoDeCargo = {
  nombre: "Mes 1",
  fecha_desde: "2027-01-04",
  fecha_hasta: "2027-01-29",
};

/** El «Abono» del Mes de Juan, mañana, «Mes 1», con dos pagos (spec, «Elegir la familia»). */
export const ABONO_MES_JUAN: CargoEnCuenta = {
  id: 901,
  alumno_id: 31,
  nombre: "Juan",
  apellido: "Pérez",
  tipo_cargo: "Abono",
  modalidad: "mes",
  turno: "manana",
  periodo: MES_1,
  fecha_dia: null,
  monto_total: "85000.00",
  pagado: "40000.00",
  saldo: "45000.00",
  creado_en: "2026-11-01T10:00:00-03:00",
  pagos: [
    { id: 701, monto: "30000.00", fecha_pago: "2026-11-02" },
    { id: 702, monto: "10000.00", fecha_pago: "2026-11-05" },
  ],
};

/** La «Preinscripción» de Ana, sin modalidad ni turno ni periodo. */
export const PREINSCRIPCION_ANA: CargoEnCuenta = {
  id: 902,
  alumno_id: 30,
  nombre: "Ana",
  apellido: "Pérez",
  tipo_cargo: "Preinscripción",
  modalidad: null,
  turno: null,
  periodo: null,
  fecha_dia: null,
  monto_total: "20000.00",
  pagado: "5000.00",
  saldo: "15000.00",
  creado_en: "2026-10-30T10:00:00-03:00",
  pagos: [{ id: 703, monto: "5000.00", fecha_pago: "2026-11-01" }],
};

/** El «Abono» del Día de Juan, turno tarde, del 2027-01-08. */
export const ABONO_DIA_JUAN: CargoEnCuenta = {
  id: 903,
  alumno_id: 31,
  nombre: "Juan",
  apellido: "Pérez",
  tipo_cargo: "Abono",
  modalidad: "dia",
  turno: "tarde",
  periodo: null,
  fecha_dia: "2027-01-08",
  monto_total: "9000.00",
  pagado: "0.00",
  saldo: "9000.00",
  creado_en: "2026-11-03T10:00:00-03:00",
  pagos: [],
};

export function cuentaDe(
  familia: FamiliaEncontrada,
  campos: Partial<Omit<CuentaCorriente, "familia_id" | "etiqueta" | "categoria">>,
): CuentaCorriente {
  return {
    familia_id: familia.id,
    etiqueta: familia.etiqueta,
    categoria: familia.categoria,
    total_cargos: "0.00",
    total_pagado: "0.00",
    saldo_pendiente: "0.00",
    cargos: [],
    ...campos,
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

const RUTA_CUENTA = /\/api\/v1\/familias\/(\d+)\/cuenta-corriente$/;

export interface Respuestas {
  /** Las familias que existen; la busqueda devuelve las que empiezan con el apellido. */
  familias?: FamiliaEncontrada[];
  /** `GET /api/v1/familias/{id}/cuenta-corriente`. */
  cuenta: (familiaId: number) => Response | Promise<Response>;
}

/** Finge la API con la sesion de un Admin. Lo no previsto responde 404. */
export function fingirApi(respuestas: Respuestas): FetchFingido {
  const familias = respuestas.familias ?? [FAMILIA_PEREZ_ANA];
  return fingirFetch(async (url, init) => {
    const camino = ruta(url);
    const verbo = metodo(init);
    if (camino.endsWith("/api/v1/auth/yo")) return respuestaJson(200, admin());
    if (camino.endsWith("/api/v1/grupos") && verbo === "GET") return respuestaJson(200, []);
    if (camino.endsWith("/api/v1/familias") && verbo === "GET") {
      const apellido = (
        new URL(url, "http://localhost").searchParams.get("apellido") ?? ""
      ).toLowerCase();
      return respuestaJson(
        200,
        familias.filter((f) => f.etiqueta.toLowerCase().startsWith(apellido)),
      );
    }
    const deFamilia = RUTA_CUENTA.exec(camino);
    if (deFamilia && verbo === "GET") return respuestas.cuenta(Number(deFamilia[1]));
    return respuestaJson(404, { detail: "No encontrado." });
  });
}

/** Los ids de familia de los `GET /api/v1/familias/{id}/cuenta-corriente`, en orden. */
export function cuentasPedidas(api: FetchFingido): number[] {
  return api.mock.calls
    .map(([entrada, init]) => {
      const url =
        typeof entrada === "string"
          ? entrada
          : entrada instanceof URL
            ? entrada.toString()
            : entrada.url;
      const coincide = RUTA_CUENTA.exec(ruta(url));
      return coincide && metodo(init) === "GET" ? Number(coincide[1]) : null;
    })
    .filter((id): id is number => id !== null);
}

// ---------------------------------------------------------------------------
// Abrir la pantalla
// ---------------------------------------------------------------------------

/** Abre `/cuenta-corriente` con la sesion guardada y espera el buscador `Familia`. */
export async function abrirCuentaCorriente() {
  localStorage.setItem(CLAVE_TOKEN, "tok-admin");
  abrir("/cuenta-corriente");
  await screen.findByRole("combobox", { name: etiqueta("Familia") });
}

export function campoFamilia(): HTMLElement {
  return screen.getByRole("combobox", { name: etiqueta("Familia") });
}

// ---------------------------------------------------------------------------
// Leer la pantalla
// ---------------------------------------------------------------------------

export function normalizar(texto: string | null | undefined): string {
  return (texto ?? "")
    .replace(new RegExp(String.fromCharCode(0x200b), "g"), "")
    .replace(/\s+/g, " ")
    .trim();
}

function escapar(texto: string): string {
  return texto.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** `$ 85.000` como monto entero: no lo confunde con `$ 85.000,50` ni con `$ 0` dentro de `$ 0,50`. */
function monto(valor: string): RegExp {
  return new RegExp(`${escapar(valor)}(?![\\d.,])`);
}

/** `true` si `contenido` tiene el monto `valor` entero. */
export function tieneMonto(contenido: string, valor: string): boolean {
  return monto(valor).test(contenido);
}

/** Los elementos mas profundos cuyo texto cumple `cumple`. */
function masProfundos(cumple: (texto: string) => boolean): HTMLElement[] {
  return Array.from(document.body.querySelectorAll<HTMLElement>("*")).filter(
    (el) =>
      cumple(normalizar(el.textContent)) &&
      !Array.from(el.children).some((hijo) => cumple(normalizar(hijo.textContent))),
  );
}

/**
 * El valor `valor` junto a la etiqueta `nombre`: el contenedor mas cercano a
 * la etiqueta que tiene el valor. Ese contenedor no puede incluir ninguno de
 * los `excluidos` (por ejemplo, la descripcion de un cargo), para que el
 * valor sea de la etiqueta y no de otra cosa de la pantalla.
 */
export function valorJunto(nombre: string, valor: string, excluidos: string[]): HTMLElement {
  const etiquetas = masProfundos((t) => t.includes(nombre));
  expect(etiquetas, `no se ve «${nombre}»`).toHaveLength(1);
  let actual: HTMLElement | null = etiquetas[0] as HTMLElement;
  while (actual && !tieneMonto(normalizar(actual.textContent), valor)) {
    actual = actual.parentElement;
  }
  expect(actual, `«${nombre}» no tiene al lado «${valor}»`).not.toBeNull();
  const contenido = normalizar((actual as HTMLElement).textContent);
  for (const otro of excluidos) {
    expect(contenido, `«${valor}» no es de «${nombre}»`).not.toContain(otro);
  }
  return actual as HTMLElement;
}

export async function esperarValorJunto(nombre: string, valor: string, excluidos: string[]) {
  let encontrado: HTMLElement | undefined;
  await waitFor(() => {
    encontrado = valorJunto(nombre, valor, excluidos);
  });
  return encontrado as HTMLElement;
}

/**
 * El renglon del cargo cuya descripcion es `descripcion`: el contenedor mas
 * cercano a la descripcion que tiene tambien todos los `textos`. No puede
 * incluir las descripciones de los `otros` renglones ni `Saldo pendiente`.
 */
export function renglonDeCargo(
  descripcion: string,
  textos: string[],
  otros: string[],
): HTMLElement {
  const titulos = masProfundos((t) => t === descripcion);
  expect(titulos, `no se ve el renglon «${descripcion}»`).toHaveLength(1);
  const tieneTodo = (el: HTMLElement) => {
    const contenido = normalizar(el.textContent);
    return textos.every((t) => contenido.includes(t));
  };
  let actual: HTMLElement | null = titulos[0] as HTMLElement;
  while (actual && !tieneTodo(actual)) {
    actual = actual.parentElement;
  }
  expect(actual, `el renglon «${descripcion}» no tiene ${JSON.stringify(textos)}`).not.toBeNull();
  const contenido = normalizar((actual as HTMLElement).textContent);
  for (const otro of [...otros, "Saldo pendiente"]) {
    expect(contenido, `lo que se ve no es del renglon «${descripcion}»`).not.toContain(otro);
  }
  return actual as HTMLElement;
}

export async function esperarRenglon(descripcion: string, textos: string[], otros: string[]) {
  let encontrado: HTMLElement | undefined;
  await waitFor(() => {
    encontrado = renglonDeCargo(descripcion, textos, otros);
  });
  return encontrado as HTMLElement;
}

/**
 * Afirma que en el renglon la etiqueta `nombre` (`Total`, `Pagado`, `Saldo`)
 * va seguida de su monto, con `:` o espacios en el medio o sin nada.
 */
export function montoDelRenglon(renglon: HTMLElement, nombre: string, valor: string) {
  const contenido = normalizar(renglon.textContent);
  // Sin limite de palabra antes de la etiqueta: si la etiqueta y el texto
  // anterior estan en elementos separados, `textContent` los pega.
  const patron = new RegExp(`${escapar(nombre)}:?\\s*${monto(valor).source}`);
  expect(contenido, `el renglon no muestra «${nombre}» «${valor}»`).toMatch(patron);
}

/** `true` si dentro de `contenedor` hay un elemento cuyo texto entero es `texto`. */
export function hayTextoEn(contenedor: HTMLElement, texto: string): boolean {
  return Array.from(contenedor.querySelectorAll<HTMLElement>("*")).some(
    (el) => normalizar(el.textContent) === texto,
  );
}

/** Todo el texto de la pagina. */
export function textoDeLaPagina(): string {
  return normalizar(document.body.textContent);
}
