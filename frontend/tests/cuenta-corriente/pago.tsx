/**
 * Ayudas de los tests del formulario de pago de la pantalla «Cuenta
 * corriente»: la API fingida con `POST /api/v1/cargos/{cargo_id}/pagos`
 * (cuerpo `PagoEntrada`, respuesta `PagoRegistrado`), abrir el formulario de
 * un cargo y leer los pedidos enviados.
 *
 * Como se encuentra cada cosa (lo que la pantalla tiene que respetar):
 * - El formulario: un `dialog`. Dentro, `Monto` y `Fecha del pago` por su
 *   etiqueta, y los botones `Registrar pago` y `Cancelar`.
 * - El `Registrar pago` del renglon: un `button` dentro del renglon del cargo
 *   (ver `renglonDeCargo` en `pantalla.tsx`).
 * - Un mensaje "junto a `Monto`": la descripcion accesible del campo, como
 *   en los demas formularios (`toHaveAccessibleDescription`).
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { expect } from "vitest";
import { fingirFetch, respuestaJson, type FetchFingido } from "../auth/montar";
import { admin, etiqueta, type FamiliaEncontrada, type Usuario } from "../cargos/pantalla";
import {
  FAMILIA_PEREZ_ANA,
  abrirCuentaCorriente,
  elegirFamilia,
  esperarRenglon,
  type CargoEnCuenta,
  type CuentaCorriente,
} from "./pantalla";

// ---------------------------------------------------------------------------
// Datos con la forma del contrato
// ---------------------------------------------------------------------------

export interface PagoRegistrado {
  id: number;
  cargo_id: number;
  monto: string;
  fecha_pago: string;
  registrado_por: number;
  registrado_en: string;
  saldo_cargo: string;
  saldo_pendiente: string;
}

export function pagoRegistrado(campos: Partial<PagoRegistrado>): PagoRegistrado {
  return {
    id: 801,
    cargo_id: 901,
    monto: "30000.00",
    fecha_pago: "2026-11-02",
    registrado_por: 7,
    registrado_en: "2026-11-14T10:00:00-03:00",
    saldo_cargo: "25000.00",
    saldo_pendiente: "40000.00",
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

function urlDe(entrada: RequestInfo | URL): string {
  if (typeof entrada === "string") return entrada;
  if (entrada instanceof URL) return entrada.toString();
  return entrada.url;
}

const RUTA_CUENTA = /\/api\/v1\/familias\/(\d+)\/cuenta-corriente$/;
const RUTA_PAGOS = /\/api\/v1\/cargos\/(\d+)\/pagos$/;

export interface RespuestasPago {
  familias?: FamiliaEncontrada[];
  /** `GET /api/v1/familias/{id}/cuenta-corriente`; `vez` cuenta desde 1. */
  cuenta: (familiaId: number, vez: number) => CuentaCorriente;
  /** `POST /api/v1/cargos/{cargo_id}/pagos`. */
  pagar?: (cargoId: number, cuerpo: Record<string, unknown>) => Response | Promise<Response>;
}

/** Finge la API con la sesion de un Admin. Lo no previsto responde 404. */
export function fingirApiDePago(respuestas: RespuestasPago): FetchFingido {
  const familias = respuestas.familias ?? [FAMILIA_PEREZ_ANA];
  let vecesCuenta = 0;
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
    if (deFamilia && verbo === "GET") {
      vecesCuenta += 1;
      return respuestaJson(200, respuestas.cuenta(Number(deFamilia[1]), vecesCuenta));
    }
    const deCargo = RUTA_PAGOS.exec(camino);
    if (deCargo && verbo === "POST" && respuestas.pagar) {
      return respuestas.pagar(
        Number(deCargo[1]),
        JSON.parse(String(init?.body)) as Record<string, unknown>,
      );
    }
    return respuestaJson(404, { detail: "No encontrado." });
  });
}

export interface Pedido {
  camino: string;
  metodo: string;
  cuerpo: unknown;
}

function pedidosDe(api: FetchFingido): Pedido[] {
  return api.mock.calls.map(([entrada, init]) => ({
    camino: ruta(urlDe(entrada)),
    metodo: metodo(init),
    cuerpo:
      init?.body === undefined || init?.body === null ? undefined : JSON.parse(String(init.body)),
  }));
}

/** Todos los pedidos, de cualquier metodo, a `/api/v1/cargos` y lo que cuelga de ahi. */
export function pedidosACargos(api: FetchFingido): Pedido[] {
  return pedidosDe(api).filter(
    (p) => p.camino === "/api/v1/cargos" || p.camino.startsWith("/api/v1/cargos/"),
  );
}

/** Los `POST /api/v1/cargos/{cargo_id}/pagos` del cargo `cargoId`. */
export function pagosEnviados(api: FetchFingido, cargoId: number): Pedido[] {
  return pedidosDe(api).filter(
    (p) => p.metodo === "POST" && p.camino === `/api/v1/cargos/${cargoId}/pagos`,
  );
}

// ---------------------------------------------------------------------------
// Abrir el formulario
// ---------------------------------------------------------------------------

/**
 * Abre la cuenta corriente de «Pérez – Ana», espera el renglon `descripcion`
 * con su `Registrar pago` y lo pulsa. Devuelve el dialogo.
 */
export async function abrirFormularioDePago(
  usuario: Usuario,
  descripcion: string,
  textosDelRenglon: string[],
): Promise<HTMLElement> {
  await abrirCuentaCorriente();
  await elegirFamilia(usuario, "Pér", FAMILIA_PEREZ_ANA.etiqueta);
  const renglon = await esperarRenglon(descripcion, [...textosDelRenglon, "Registrar pago"], []);
  await usuario.click(within(renglon).getByRole("button", { name: /Registrar pago/ }));
  return screen.findByRole("dialog");
}

export function campoMonto(dialogo: HTMLElement): HTMLInputElement {
  return within(dialogo).getByLabelText(etiqueta("Monto")) as HTMLInputElement;
}

export function campoFechaDelPago(dialogo: HTMLElement): HTMLInputElement {
  return within(dialogo).getByLabelText(etiqueta("Fecha del pago")) as HTMLInputElement;
}

export function botonRegistrarPago(dialogo: HTMLElement): HTMLElement {
  return within(dialogo).getByRole("button", { name: "Registrar pago" });
}

export function botonCancelar(dialogo: HTMLElement): HTMLElement {
  return within(dialogo).getByRole("button", { name: "Cancelar" });
}

/** Completa el `input type="date"` con un valor `AAAA-MM-DD`. */
export async function ponerFecha(campo: HTMLInputElement, valor: string) {
  // user-event no escribe de a teclas en un input de fecha de jsdom: se
  // completa el valor entero, como lo deja el selector del navegador.
  fireEvent.change(campo, { target: { value: valor } });
  await waitFor(() => expect(campo).toHaveValue(valor));
}

/** Borra `Monto` y escribe `texto`. */
export async function escribirMonto(usuario: Usuario, dialogo: HTMLElement, texto: string) {
  const campo = campoMonto(dialogo);
  await usuario.clear(campo);
  if (texto !== "") await usuario.type(campo, texto);
  await waitFor(() => expect(campoMonto(dialogo)).toHaveValue(texto));
}

/** La fecha de hoy LOCAL del entorno, `AAAA-MM-DD`, sin pasar por UTC. */
export function hoyDelEntorno(): string {
  const ahora = new Date();
  const dos = (n: number) => String(n).padStart(2, "0");
  return `${ahora.getFullYear()}-${dos(ahora.getMonth() + 1)}-${dos(ahora.getDate())}`;
}

/** Un cargo con saldo, sobre el «Abono» del Mes de Juan. */
export function cargoConSaldo(base: CargoEnCuenta, campos: Partial<CargoEnCuenta>): CargoEnCuenta {
  return { ...base, ...campos };
}
