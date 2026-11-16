/**
 * Ayudas de los tests de la pantalla «Registrar alumno»: la API fingida con
 * las formas del contrato, la busqueda de los campos por rol y etiqueta, y
 * las acciones de una persona (elegir un grupo, agregar una persona, etc.).
 *
 * Los campos se buscan como los encontraria un lector de pantalla. Donde la
 * spec no fija la etiqueta accesible de un control, la ayuda lo busca sin
 * depender de ese nombre y queda marcada con [PREGUNTA] (ver el informe de
 * la tarea 7.1): si la respuesta fija un nombre, se cambia solo aca.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import type userEvent from "@testing-library/user-event";
import { expect } from "vitest";
import {
  CLAVE_TOKEN,
  abrir,
  fingirFetch,
  respuestaJson,
  usuarioYo,
  type FetchFingido,
} from "../auth/montar";

export type Usuario = ReturnType<typeof userEvent.setup>;

// ---------------------------------------------------------------------------
// Datos con la forma del contrato
// ---------------------------------------------------------------------------

export type Turno = "manana" | "tarde";

export interface Grupo {
  id: number;
  nombre: string;
  turno: Turno;
  nacimiento_desde: string;
  nacimiento_hasta: string;
  sugerido: boolean;
}

export const DELFINES_MANANA: Grupo = {
  id: 1,
  nombre: "Delfines",
  turno: "manana",
  nacimiento_desde: "2020-01-01",
  nacimiento_hasta: "2021-12-31",
  sugerido: false,
};

export const DELFINES_TARDE: Grupo = {
  id: 2,
  nombre: "Delfines",
  turno: "tarde",
  nacimiento_desde: "2020-01-01",
  nacimiento_hasta: "2021-12-31",
  sugerido: false,
};

export const TIBURONES_MANANA: Grupo = {
  id: 3,
  nombre: "Tiburones",
  turno: "manana",
  nacimiento_desde: "2017-01-01",
  nacimiento_hasta: "2019-12-31",
  sugerido: false,
};

export const FAMILIA_PEREZ_JUAN = {
  id: 10,
  etiqueta: "Pérez – Juan",
  categoria: "empleado" as const,
};

export const PERSONA_MARIA = { id: 20, nombre: "María", apellido: "Pérez" };

export const OBLIGATORIO = "Este dato es obligatorio.";
export const SIN_TUTOR = "La familia nueva necesita al menos un tutor.";

export function sugeridos(grupos: Grupo[], ids: number[]): Grupo[] {
  return grupos.map((grupo) => ({ ...grupo, sugerido: ids.includes(grupo.id) }));
}

// ---------------------------------------------------------------------------
// La API fingida
// ---------------------------------------------------------------------------

export function parametro(url: string, nombre: string): string | null {
  return new URL(url, "http://localhost").searchParams.get(nombre);
}

function ruta(url: string): string {
  return new URL(url, "http://localhost").pathname;
}

function metodo(init?: RequestInit): string {
  return (init?.method ?? "GET").toUpperCase();
}

export interface Respuestas {
  /** El usuario de la sesion. Por defecto, un Coordinador. */
  usuario?: ReturnType<typeof usuarioYo>;
  /** `GET /api/v1/grupos`, con o sin `fecha_nacimiento`. */
  grupos?: (fechaNacimiento: string | null) => Grupo[];
  /** `GET /api/v1/familias?apellido=`. */
  familias?: (apellido: string) => Response | Promise<Response>;
  /** `GET /api/v1/personas?dni=`. */
  personas?: (dni: string) => Response | Promise<Response>;
  /** `POST /api/v1/alumnos`. */
  alta?: (cuerpo: unknown) => Response | Promise<Response>;
}

export function coordinador() {
  return usuarioYo({
    nombre: "Lucía",
    apellido: "Rodríguez",
    rol: "coordinador",
    debe_cambiar_password: false,
  });
}

export function profesor() {
  return usuarioYo({
    nombre: "Carlos",
    apellido: "Gómez",
    rol: "profesor",
    debe_cambiar_password: false,
  });
}

/** Finge la API de la pantalla. Lo que no esta previsto responde 404. */
export function fingirApi(respuestas: Respuestas = {}): FetchFingido {
  const usuario = respuestas.usuario ?? coordinador();
  const grupos = respuestas.grupos ?? (() => [DELFINES_MANANA, DELFINES_TARDE, TIBURONES_MANANA]);
  return fingirFetch(async (url, init) => {
    const camino = ruta(url);
    if (camino.endsWith("/api/v1/auth/yo")) return respuestaJson(200, usuario);
    if (camino.endsWith("/api/v1/grupos") && metodo(init) === "GET") {
      return respuestaJson(200, grupos(parametro(url, "fecha_nacimiento")));
    }
    if (camino.endsWith("/api/v1/familias") && metodo(init) === "GET" && respuestas.familias) {
      return respuestas.familias(parametro(url, "apellido") ?? "");
    }
    if (camino.endsWith("/api/v1/personas") && metodo(init) === "GET" && respuestas.personas) {
      return respuestas.personas(parametro(url, "dni") ?? "");
    }
    if (camino.endsWith("/api/v1/alumnos") && metodo(init) === "POST" && respuestas.alta) {
      return respuestas.alta(JSON.parse(String(init?.body)));
    }
    return respuestaJson(404, { detail: "No encontrado." });
  });
}

interface Llamada {
  url: string;
  metodo: string;
  cuerpo: unknown;
}

function llamadasDe(api: FetchFingido): Llamada[] {
  return api.mock.calls.map(([entrada, init]) => {
    const url =
      typeof entrada === "string"
        ? entrada
        : entrada instanceof URL
          ? entrada.toString()
          : entrada.url;
    return {
      url,
      metodo: metodo(init),
      cuerpo: init?.body === undefined ? undefined : JSON.parse(String(init.body)),
    };
  });
}

/** Las llamadas a `metodo` sobre la ruta `camino` (sin la query). */
export function llamadasA(api: FetchFingido, metodoBuscado: string, camino: string): Llamada[] {
  return llamadasDe(api).filter(
    (llamada) => llamada.metodo === metodoBuscado && ruta(llamada.url).endsWith(camino),
  );
}

/** Los cuerpos de los `POST /api/v1/alumnos`. */
export function altasEnviadas(api: FetchFingido): Record<string, unknown>[] {
  return llamadasA(api, "POST", "/api/v1/alumnos").map(
    (llamada) => llamada.cuerpo as Record<string, unknown>,
  );
}

// ---------------------------------------------------------------------------
// Abrir la pantalla
// ---------------------------------------------------------------------------

/** Abre `/alumnos/nuevo` con sesion y espera a que el formulario este a la vista. */
export async function abrirRegistrar() {
  localStorage.setItem(CLAVE_TOKEN, "tok-vigente");
  abrir("/alumnos/nuevo");
  await screen.findAllByLabelText(etiqueta("Nombre"));
}

// ---------------------------------------------------------------------------
// Campos
// ---------------------------------------------------------------------------

function escapar(texto: string): string {
  return texto.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * La etiqueta exacta, admitiendo la marca de obligatorio que MUI agrega al
 * final (un espacio fino y un asterisco).
 */
export function etiqueta(texto: string): RegExp {
  return new RegExp(`^${escapar(texto)}\\s*\\*?$`);
}

/** El texto como expresion regular literal, para "contiene" sin comodines. */
export function contiene(texto: string): RegExp {
  return new RegExp(escapar(texto));
}

/**
 * Un campo del alumno. Los datos del alumno van antes que la seccion de
 * personas, asi que si una persona tiene un campo con la misma etiqueta
 * (`Nombre`, `Apellido`), el del alumno es el primero.
 */
export function campoAlumno(texto: "Nombre" | "Apellido" | "Fecha de nacimiento"): HTMLElement {
  const campos = screen.getAllByLabelText(etiqueta(texto));
  expect(campos.length).toBeGreaterThan(0);
  return campos[0] as HTMLElement;
}

export function campoGrupo(): HTMLElement {
  return screen.getByRole("combobox", { name: /^Grupo/ });
}

/** `Categoría` como lista desplegable o como grupo de opciones. */
export function campoCategoria(): HTMLElement {
  return (
    screen.queryByRole("combobox", { name: /^Categoría(?!:)/ }) ??
    screen.getByRole("radiogroup", { name: /^Categoría(?!:)/ })
  );
}

export function campoCategoriaSiHay(): HTMLElement | null {
  return (
    screen.queryByRole("combobox", { name: /^Categoría(?!:)/ }) ??
    screen.queryByRole("radiogroup", { name: /^Categoría(?!:)/ }) ??
    screen.queryByRole("textbox", { name: /^Categoría(?!:)/ })
  );
}

export function botonRegistrar(): HTMLElement {
  return screen.getByRole("button", {
    name: (nombre) => /\bRegistrar\b/.test(nombre) && !/alumno/i.test(nombre),
  });
}

function normalizar(texto: string | null | undefined): string {
  return (texto ?? "")
    .replace(new RegExp(String.fromCharCode(0x200b), "g"), "")
    .replace(/\s+/g, " ")
    .trim();
}

/** El texto de la opcion elegida en una lista desplegable (nativa o de MUI). */
export function textoElegido(campo: HTMLElement): string {
  if (campo instanceof HTMLSelectElement) {
    return campo.value === "" ? "" : normalizar(campo.selectedOptions[0]?.textContent);
  }
  return normalizar(campo.textContent);
}

/** Elige `opcion` en una lista desplegable (nativa o de MUI) o en un grupo de opciones. */
export async function elegir(usuario: Usuario, campo: HTMLElement, opcion: string) {
  if (campo instanceof HTMLSelectElement) {
    const elegida = Array.from(campo.options).find((op) => normalizar(op.textContent) === opcion);
    expect(elegida, `no hay una opcion «${opcion}»`).toBeDefined();
    await usuario.selectOptions(campo, elegida as HTMLOptionElement);
    return;
  }
  if (campo.getAttribute("role") === "radiogroup") {
    await usuario.click(within(campo).getByRole("radio", { name: opcion }));
    return;
  }
  await usuario.click(campo);
  const lista = await screen.findByRole("listbox");
  await usuario.click(within(lista).getByRole("option", { name: opcion }));
  await waitFor(() => expect(screen.queryByRole("listbox")).not.toBeInTheDocument());
}

/** Despliega la lista y devuelve el texto de sus opciones (sin las vacias), y la cierra. */
export async function opcionesDe(usuario: Usuario, campo: HTMLElement): Promise<string[]> {
  if (campo instanceof HTMLSelectElement) {
    return Array.from(campo.options)
      .filter((op) => op.value !== "")
      .map((op) => normalizar(op.textContent))
      .filter((texto) => texto !== "");
  }
  await usuario.click(campo);
  const lista = await screen.findByRole("listbox");
  const textos = within(lista)
    .queryAllByRole("option")
    .map((op) => normalizar(op.textContent))
    .filter((texto) => texto !== "");
  await usuario.keyboard("{Escape}");
  await waitFor(() => expect(screen.queryByRole("listbox")).not.toBeInTheDocument());
  return textos;
}

/** Completa el `input type="date"` con un valor `AAAA-MM-DD`. */
export async function escribirFecha(usuario: Usuario, valor: string) {
  const campo = campoAlumno("Fecha de nacimiento") as HTMLInputElement;
  // user-event no escribe de a teclas en un input de fecha de jsdom: se
  // completa el valor entero, como lo deja el selector del navegador.
  void usuario;
  fireEvent.change(campo, { target: { value: valor } });
  await waitFor(() => expect(campo).toHaveValue(valor));
}

/**
 * Un elemento cuyo texto propio, sin contar a sus hijos que ya lo tienen
 * entero, es `texto`. Sirve para un texto partido en varias etiquetas.
 */
export function porTexto(texto: string) {
  return (_: string, elemento: Element | null): boolean => {
    if (!elemento) return false;
    const propio = normalizar(elemento.textContent) === texto;
    const enUnHijo = Array.from(elemento.children).some(
      (hijo) => normalizar(hijo.textContent) === texto,
    );
    return propio && !enUnHijo;
  };
}

/** Los `role="alert"` que hay en pantalla y contienen ese texto. */
export function alertasCon(texto: string): HTMLElement[] {
  return screen.queryAllByRole("alert").filter((alerta) => alerta.textContent?.includes(texto));
}

// ---------------------------------------------------------------------------
// Familia
// ---------------------------------------------------------------------------

/**
 * [PREGUNTA] La spec no fija la etiqueta del buscador de familia existente
 * («se escribe Pé en el buscador»). Se lo busca como el cuadro combinado que
 * aparece al elegir `Familia existente` y que no es `Grupo` ni `Categoría`.
 */
export async function buscadorFamilia(): Promise<HTMLElement> {
  let encontrado: HTMLElement | undefined;
  await waitFor(() => {
    const grupo = campoGrupo();
    const categoria = screen.queryByRole("combobox", { name: /^Categoría(?!:)/ });
    const candidatos = screen
      .getAllByRole("combobox")
      .filter((c) => c !== grupo && c !== categoria);
    expect(candidatos).toHaveLength(1);
    encontrado = candidatos[0];
  });
  return encontrado as HTMLElement;
}

/** Elige `Familia existente`, busca `apellido` y elige la familia de `etiqueta`. */
export async function elegirFamiliaExistente(
  usuario: Usuario,
  apellido: string,
  etiquetaFamilia: string,
) {
  await usuario.click(screen.getByRole("radio", { name: "Familia existente" }));
  const buscador = await buscadorFamilia();
  await usuario.type(buscador, apellido);
  const opcion = await screen.findByRole("option", { name: contiene(etiquetaFamilia) });
  await usuario.click(opcion);
}

// ---------------------------------------------------------------------------
// Personas
// ---------------------------------------------------------------------------

/**
 * [PREGUNTA] La spec no dice como se agrega una persona nueva: si hay un
 * boton (y con que nombre) o una fila vacia. Se supone un boton cuyo nombre
 * contiene «Agregar».
 */
export function botonAgregarPersona(): HTMLElement {
  return screen.getByRole("button", { name: /agregar/i });
}

/**
 * [PREGUNTA] La spec dice «el DNI a buscar» sin fijar su etiqueta. Se lo busca
 * como el cuadro de texto cuya etiqueta contiene «DNI», cuando todavia no hay
 * ninguna persona agregada (el alumno no tiene DNI).
 */
export function campoDniABuscar(): HTMLElement {
  return screen.getByRole("textbox", { name: /DNI/ });
}

export function casillasTutor(): HTMLElement[] {
  return screen.queryAllByRole("checkbox", { name: etiqueta("Tutor") });
}

export interface FilaPersona {
  nombre: HTMLElement;
  apellido: HTMLElement;
  telefono: HTMLElement;
  dni: HTMLElement;
  tutor: HTMLElement;
}

/**
 * Agrega una persona nueva y devuelve sus campos: los que aparecieron con
 * esas etiquetas despues de pulsar el boton.
 */
export async function agregarPersonaNueva(usuario: Usuario): Promise<FilaPersona> {
  const antes = {
    nombre: screen.queryAllByLabelText(etiqueta("Nombre")),
    apellido: screen.queryAllByLabelText(etiqueta("Apellido")),
    telefono: screen.queryAllByLabelText(etiqueta("Teléfono")),
    dni: screen.queryAllByLabelText(etiqueta("DNI")),
    tutor: casillasTutor(),
  };
  await usuario.click(botonAgregarPersona());

  const nuevo = async (previos: HTMLElement[], buscar: () => HTMLElement[]) => {
    let campo: HTMLElement | undefined;
    await waitFor(() => {
      const nuevos = buscar().filter((c) => !previos.includes(c));
      expect(nuevos).toHaveLength(1);
      campo = nuevos[0];
    });
    return campo as HTMLElement;
  };

  return {
    nombre: await nuevo(antes.nombre, () => screen.queryAllByLabelText(etiqueta("Nombre"))),
    apellido: await nuevo(antes.apellido, () => screen.queryAllByLabelText(etiqueta("Apellido"))),
    telefono: await nuevo(antes.telefono, () => screen.queryAllByLabelText(etiqueta("Teléfono"))),
    dni: await nuevo(antes.dni, () => screen.queryAllByLabelText(etiqueta("DNI"))),
    tutor: await nuevo(antes.tutor, casillasTutor),
  };
}

export interface DatosPersona {
  nombre: string;
  apellido: string;
  telefono: string;
  dni?: string;
  tutor: boolean;
}

export async function cargarPersonaNueva(
  usuario: Usuario,
  datos: DatosPersona,
): Promise<FilaPersona> {
  const fila = await agregarPersonaNueva(usuario);
  await usuario.type(fila.nombre, datos.nombre);
  await usuario.type(fila.apellido, datos.apellido);
  await usuario.type(fila.telefono, datos.telefono);
  if (datos.dni) await usuario.type(fila.dni, datos.dni);
  if (datos.tutor) await usuario.click(fila.tutor);
  return fila;
}

// ---------------------------------------------------------------------------
// El formulario completo de Juan Perez
// ---------------------------------------------------------------------------

export const MARIA_TUTORA: DatosPersona = {
  nombre: "María",
  apellido: "Pérez",
  telefono: "3511234567",
  dni: "30111222",
  tutor: true,
};

/** Nombre, apellido, fecha y grupo de Juan Perez en «Delfines» manana. */
export async function completarAlumnoJuan(usuario: Usuario) {
  await usuario.type(campoAlumno("Nombre"), "Juan");
  await usuario.type(campoAlumno("Apellido"), "Pérez");
  await escribirFecha(usuario, "2020-03-10");
  await elegirGrupoDelfinesManana(usuario);
}

/**
 * Elige «Delfines» manana, salvo que la sugerencia ya lo haya elegido
 * (si la fecha cargada lo marca como unico sugerido).
 */
async function elegirGrupoDelfinesManana(usuario: Usuario) {
  const grupo = campoGrupo();
  if (textoElegido(grupo).startsWith("Delfines · Mañana")) return;
  await elegir(usuario, grupo, "Delfines · Mañana");
  await waitFor(() => expect(textoElegido(campoGrupo())).toBe("Delfines · Mañana"));
}

/**
 * El formulario completo para Juan Perez en «Delfines» manana, familia
 * nueva `Empleado` y Maria Perez como tutora nueva. Devuelve la fila de Maria.
 */
export async function completarAltaJuan(usuario: Usuario): Promise<FilaPersona> {
  await completarAlumnoJuan(usuario);
  await elegir(usuario, campoCategoria(), "Empleado");
  return cargarPersonaNueva(usuario, MARIA_TUTORA);
}

export function alumnoRegistradoJuan() {
  return {
    id: 50,
    nombre: "Juan",
    apellido: "Pérez",
    fecha_nacimiento: "2020-03-10",
    familia: { ...FAMILIA_PEREZ_JUAN },
    inscripcion: {
      grupo_id: DELFINES_MANANA.id,
      grupo_nombre: "Delfines",
      turno: "manana",
      temporada_id: 3,
    },
  };
}

/** Espera real, para afirmar que algo no paso despues de la espera entre teclas. */
export function esperar(ms: number): Promise<void> {
  return new Promise((resolver) => setTimeout(resolver, ms));
}
