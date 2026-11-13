/**
 * Ayudas de los tests de sesion: montar la aplicacion en una direccion,
 * leer la direccion actual y fingir la API.
 *
 * "Abrir una direccion" o "recargar" es montar la aplicacion de cero con un
 * MemoryRouter nuevo. La direccion no se ve en pantalla, asi que al lado de
 * la aplicacion va un componente del test que la escribe.
 */
import { render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { vi, type Mock } from "vitest";
import App from "../../src/App";

export const CLAVE_TOKEN = "escuelita.token";

function DireccionActual() {
  const ubicacion = useLocation();
  return <output aria-label="dirección actual">{ubicacion.pathname}</output>;
}

/** Monta la aplicacion de cero en `direccion`. */
export function abrir(direccion: string) {
  return render(
    <MemoryRouter initialEntries={[direccion]}>
      <App />
      <DireccionActual />
    </MemoryRouter>,
  );
}

/** El texto de la direccion actual. */
export function direccion(): string {
  return screen.getByLabelText("dirección actual").textContent ?? "";
}

export function respuestaJson(status: number, cuerpo: unknown): Response {
  return new Response(JSON.stringify(cuerpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Usuario como lo devuelve `GET /api/v1/auth/yo`. */
export function usuarioYo(campos: {
  nombre?: string;
  apellido?: string;
  rol?: "admin" | "coordinador" | "profesor";
  debe_cambiar_password?: boolean;
}) {
  return {
    id: 7,
    username: "jperez",
    nombre: "Juana",
    apellido: "Pérez",
    rol: "admin",
    debe_cambiar_password: false,
    ...campos,
  };
}

export type FetchFingido = Mock<typeof fetch>;

/** Reemplaza el `fetch` global por uno fingido y lo devuelve. */
export function fingirFetch(
  implementacion: (url: string, init?: RequestInit) => Promise<Response>,
): FetchFingido {
  const falso = vi.fn<typeof fetch>((entrada, init) => implementacion(urlDe(entrada), init));
  vi.stubGlobal("fetch", falso);
  return falso;
}

/** Una promesa que nunca se resuelve: la API "todavia no respondio". */
export function sinRespuesta(): Promise<Response> {
  return new Promise<Response>(() => {});
}

function urlDe(entrada: RequestInfo | URL): string {
  if (typeof entrada === "string") return entrada;
  if (entrada instanceof URL) return entrada.toString();
  return entrada.url;
}

function metodoDe(entrada: RequestInfo | URL, init?: RequestInit): string {
  if (init?.method) return init.method.toUpperCase();
  if (typeof entrada !== "string" && !(entrada instanceof URL)) {
    return entrada.method.toUpperCase();
  }
  return "GET";
}

function autorizacionDe(entrada: RequestInfo | URL, init?: RequestInit): string | null {
  if (init?.headers) {
    const valor = new Headers(init.headers).get("Authorization");
    if (valor !== null) return valor;
  }
  if (typeof entrada !== "string" && !(entrada instanceof URL)) {
    return entrada.headers.get("Authorization");
  }
  return null;
}

/** Las llamadas que recibio el `fetch` fingido, ya leidas. */
export function llamadas(falso: FetchFingido) {
  return falso.mock.calls.map(([entrada, init]) => ({
    url: urlDe(entrada),
    metodo: metodoDe(entrada, init),
    autorizacion: autorizacionDe(entrada, init),
  }));
}

/** Las llamadas a `GET /api/v1/auth/yo`. */
export function llamadasAYo(falso: FetchFingido) {
  return llamadas(falso).filter(
    (llamada) => llamada.metodo === "GET" && llamada.url.includes("/api/v1/auth/yo"),
  );
}
