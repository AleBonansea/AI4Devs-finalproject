/**
 * Ayudas de los tests de navegacion: la sesion fingida de cada rol, la API de
 * las pantallas que piden datos al abrirse (con las formas del contrato), el
 * menu y el registro de las direcciones por las que paso la aplicacion.
 *
 * Como se encuentra cada cosa (lo que la aplicacion tiene que respetar):
 * - El menu: el unico elemento `navigation` de la pagina.
 * - Sus opciones: enlaces (`link`) con el nombre de la opcion.
 * - La opcion de la direccion abierta: `aria-current="page"`.
 */
import { render, screen, within } from "@testing-library/react";
import { useEffect } from "react";
import { MemoryRouter, useLocation } from "react-router-dom";
import App from "../../src/App";
import {
  CLAVE_TOKEN,
  fingirFetch,
  respuestaJson,
  usuarioYo,
  type FetchFingido,
} from "../auth/montar";

export type Rol = "admin" | "coordinador" | "profesor";

export const OPCIONES_ESCUELA = ["Inicio", "Registrar alumno", "Tomar asistencia"] as const;
export const OPCIONES_ADMIN = ["Registrar cargo", "Cuenta corriente"] as const;

/** Nombre y apellido de la sesion de cada rol. */
export const PERSONA: Record<Rol, { nombre: string; apellido: string }> = {
  admin: { nombre: "Juana", apellido: "Pérez" },
  coordinador: { nombre: "Lucía", apellido: "Rodríguez" },
  profesor: { nombre: "Carlos", apellido: "Gómez" },
};

/** `GrupoParaInscribir`, con la edad del grupo que ahora trae el contrato. */
const DELFINES_MANANA = {
  id: 1,
  nombre: "Delfines",
  turno: "manana",
  nacimiento_desde: "2019-01-01",
  nacimiento_hasta: "2020-12-31",
  sugerido: false,
  edad_desde: 6,
  edad_hasta: 7,
};

function caminoDe(url: string): string {
  return new URL(url, "http://localhost").pathname;
}

/**
 * Guarda el token y finge la API con la sesion de `rol`. Responde lo que las
 * pantallas de la zona protegida piden al abrirse; el resto, 404.
 */
export function sesionDe(rol: Rol, debeCambiarPassword = false): FetchFingido {
  localStorage.setItem(CLAVE_TOKEN, `tok-${rol}`);
  const persona = PERSONA[rol];
  return fingirFetch(async (url, init) => {
    const metodo = (init?.method ?? "GET").toUpperCase();
    const camino = caminoDe(url);
    if (metodo !== "GET") return respuestaJson(404, { detail: "No encontrado." });
    if (camino === "/api/v1/auth/yo") {
      return respuestaJson(
        200,
        usuarioYo({ ...persona, rol, debe_cambiar_password: debeCambiarPassword }),
      );
    }
    if (camino === "/api/v1/grupos") return respuestaJson(200, [DELFINES_MANANA]);
    const asistencia = camino.match(/^\/api\/v1\/grupos\/(\d+)\/asistencias\/([\d-]+)$/);
    if (asistencia) {
      return respuestaJson(200, {
        grupo_id: Number(asistencia[1]),
        grupo: DELFINES_MANANA.nombre,
        turno: DELFINES_MANANA.turno,
        fecha: asistencia[2],
        alumnos: [],
      });
    }
    if (camino === "/api/v1/cargos/opciones") {
      return respuestaJson(200, { tipos_cargo: [], periodos: [] });
    }
    if (camino === "/api/v1/familias") return respuestaJson(200, []);
    return respuestaJson(404, { detail: "No encontrado." });
  });
}

/** Las direcciones por las que paso la aplicacion, en orden y sin repetir seguidas. */
export const recorrido: string[] = [];

function DireccionActual() {
  const ubicacion = useLocation();
  useEffect(() => {
    if (recorrido[recorrido.length - 1] !== ubicacion.pathname) {
      recorrido.push(ubicacion.pathname);
    }
  }, [ubicacion.pathname]);
  return <output aria-label="dirección actual">{ubicacion.pathname}</output>;
}

/** Monta la aplicacion de cero en `direccion`, con el recorrido vacio. */
export function abrir(direccion: string) {
  recorrido.length = 0;
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

/** Espera a que la sesion este comprobada: el encabezado muestra al usuario. */
export async function esperarSesion(rol: Rol): Promise<void> {
  const { nombre, apellido } = PERSONA[rol];
  await screen.findByText(new RegExp(`${nombre} ${apellido}`));
}

/** El menu de la zona protegida. */
export function menu(): HTMLElement {
  return screen.getByRole("navigation");
}

/** La opcion `nombre` del menu. */
export function opcion(nombre: string): HTMLElement {
  return within(menu()).getByRole("link", { name: nombre });
}

/** Los textos visibles dentro de `elemento`, en el orden del documento. */
export function textosDe(elemento: HTMLElement): string[] {
  const textos: string[] = [];
  const recorredor = document.createTreeWalker(elemento, NodeFilter.SHOW_TEXT);
  for (let nodo = recorredor.nextNode(); nodo; nodo = recorredor.nextNode()) {
    const texto = nodo.textContent?.replace(/\s+/g, " ").trim();
    if (texto) textos.push(texto);
  }
  return textos;
}
