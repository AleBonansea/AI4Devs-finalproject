/**
 * Tests del encabezado de las pantallas sin sesion (ingreso y aviso de
 * cambio de contrasena pendiente) y del boton unico de ingreso.
 *
 * Spec: openspec/changes/paleta-y-encuadre/specs/auth/spec.md
 * Un `describe` por Requirement y un `it` por Scenario, con su nombre.
 */
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { CLAVE_TOKEN, abrir, fingirFetch, respuestaJson, usuarioYo } from "./montar";

const ALT_LOGO = "Logo de la Escuela de Verano";
const TITULO = "Escuela de Verano";
const SUBTITULO = "Centro Médico · Administración de la temporada";
const TITULO_CAMBIO_PENDIENTE = "Tenés que cambiar tu contraseña antes de continuar.";

/** Una API que no conoce nada: toda llamada responde 404. */
function apiVacia() {
  return fingirFetch(async () => respuestaJson(404, { detail: "No encontrado." }));
}

/** Abre `/ingresar` y espera a que el formulario este a la vista. */
async function abrirIngreso() {
  abrir("/ingresar");
  await screen.findByLabelText("Usuario");
}

/** `a` va antes que `b` en el orden del documento. */
function vaAntes(a: Node, b: Node): boolean {
  return Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
}

/**
 * El subtitulo esta en pantalla y el elemento que lo contiene no tiene nada
 * mas: ni la temporada ni el anio, ni siquiera dentro de un elemento hijo.
 */
function expectSubtituloExacto(subtitulo: HTMLElement) {
  expect(subtitulo.textContent?.replace(/\s+/g, " ").trim()).toBe(SUBTITULO);
}

describe("Encabezado de las pantallas sin sesión", () => {
  it("El ingreso muestra el encabezado", async () => {
    apiVacia();

    await abrirIngreso();

    expect(screen.getByRole("img", { name: ALT_LOGO })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: TITULO })).toBeInTheDocument();
    expectSubtituloExacto(screen.getByText(SUBTITULO));
  });

  it("El encabezado va antes de los campos", async () => {
    apiVacia();

    await abrirIngreso();

    const logo = screen.getByRole("img", { name: ALT_LOGO });
    const titulo = screen.getByRole("heading", { level: 1, name: TITULO });
    const subtitulo = screen.getByText(SUBTITULO);
    const campoUsuario = screen.getByLabelText("Usuario");

    expect(vaAntes(logo, titulo)).toBe(true);
    expect(vaAntes(titulo, subtitulo)).toBe(true);
    expect(vaAntes(subtitulo, campoUsuario)).toBe(true);
  });

  it("El aviso de cambio pendiente muestra el mismo encabezado", async () => {
    const pendiente = usuarioYo({ debe_cambiar_password: true });
    // Contrato: `POST /auth/login` devuelve `LoginRespuesta`; `GET /auth/yo`
    // devuelve `UsuarioActual`. Cualquier otra llamada, 404.
    fingirFetch(async (url, init) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (metodo === "POST" && url.includes("/api/v1/auth/login")) {
        return respuestaJson(200, {
          access_token: "tok-123",
          token_type: "bearer",
          usuario: pendiente,
        });
      }
      if (metodo === "GET" && url.includes("/api/v1/auth/yo")) {
        return respuestaJson(200, pendiente);
      }
      return respuestaJson(404, { detail: "No encontrado." });
    });
    const usuario = userEvent.setup();

    await abrirIngreso();
    await usuario.type(screen.getByLabelText("Usuario"), "jperez");
    await usuario.type(screen.getByLabelText("Contraseña"), "Verano2026");
    await usuario.click(screen.getByRole("button", { name: "Ingresar" }));

    expect(await screen.findByText(TITULO_CAMBIO_PENDIENTE)).toBeInTheDocument();
    expect(await screen.findByRole("img", { name: ALT_LOGO })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { level: 1, name: TITULO })).toBeInTheDocument();
    expectSubtituloExacto(await screen.findByText(SUBTITULO));
  });

  it("En el aviso, el encabezado va antes del aviso", async () => {
    // Recarga: el token ya esta guardado y `GET /auth/yo` devuelve
    // `UsuarioActual` con el cambio de contrasena pendiente.
    localStorage.setItem(CLAVE_TOKEN, "tok-vigente");
    fingirFetch(async (url, init) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (metodo === "GET" && url.includes("/api/v1/auth/yo")) {
        return respuestaJson(200, usuarioYo({ debe_cambiar_password: true }));
      }
      return respuestaJson(404, { detail: "No encontrado." });
    });

    abrir("/");

    const aviso = await screen.findByText(TITULO_CAMBIO_PENDIENTE);
    const logo = await screen.findByRole("img", { name: ALT_LOGO });
    const titulo = await screen.findByRole("heading", { level: 1, name: TITULO });
    const subtitulo = await screen.findByText(SUBTITULO);
    const salir = await screen.findByRole("button", { name: "Salir" });

    expect(vaAntes(logo, titulo)).toBe(true);
    expect(vaAntes(titulo, subtitulo)).toBe(true);
    expect(vaAntes(subtitulo, aviso)).toBe(true);
    expect(vaAntes(aviso, salir)).toBe(true);
  });
});

describe("Un solo botón de ingreso", () => {
  it("El único botón es Ingresar", async () => {
    apiVacia();

    await abrirIngreso();

    const botones = screen.getAllByRole("button");
    expect(botones).toHaveLength(1);
    expect(botones[0]).toHaveAccessibleName("Ingresar");
  });

  it("No se puede elegir el rol al entrar", async () => {
    apiVacia();

    await abrirIngreso();

    expect(screen.getByRole("button", { name: "Ingresar" })).toBeInTheDocument();
    expect(screen.queryAllByText(/^\s*Entrar como/)).toHaveLength(0);
    expect(screen.queryAllByRole("button", { name: /^\s*Entrar como/ })).toHaveLength(0);
    expect(screen.queryAllByText(/Prototipo/)).toHaveLength(0);
  });
});
