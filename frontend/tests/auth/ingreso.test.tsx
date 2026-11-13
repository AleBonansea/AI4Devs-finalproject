/**
 * Tests de la pantalla de ingreso: el formulario, los campos vacios, el
 * ingreso correcto, el estado de carga, los errores generales y por campo,
 * y el ingreso con el cambio de contrasena pendiente.
 *
 * Spec: openspec/changes/pantalla-de-ingreso/specs/auth/spec.md
 * Un test por Scenario; el nombre dice el THEN.
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import {
  CLAVE_TOKEN,
  abrir,
  direccion,
  fingirFetch,
  llamadas,
  llamadasAYo,
  respuestaJson,
  sinRespuesta,
  usuarioYo,
  type FetchFingido,
} from "./montar";

const TITULO_CAMBIO_PENDIENTE = "Tenés que cambiar tu contraseña antes de continuar.";
const TEXTO_CAMBIO_PENDIENTE =
  "El cambio de contraseña todavía no está disponible. Pedile ayuda a un Admin.";
const MENSAJE_SIN_CONEXION = "No se pudo conectar con el servidor. Revisá tu conexión.";
const MENSAJE_ERROR_SERVIDOR = "El servidor tuvo un problema. Intentá de nuevo.";
const CREDENCIALES_INCORRECTAS = "Usuario o contraseña incorrectos.";
const USUARIO_BLOQUEADO = "Usuario bloqueado. Pedile a un Admin que blanquee tu contraseña.";
const FALTA_USUARIO = "Ingresá tu usuario.";
const FALTA_CONTRASENA = "Ingresá tu contraseña.";

type Usuario = ReturnType<typeof usuarioYo>;

/** Respuesta 200 de `POST /api/v1/auth/login`, con la forma del contrato. */
function loginCorrecto(accessToken: string, usuario: Usuario): Response {
  return respuestaJson(200, {
    access_token: accessToken,
    token_type: "bearer",
    usuario,
  });
}

function esLogin(url: string, init?: RequestInit): boolean {
  return url.includes("/api/v1/auth/login") && (init?.method ?? "GET").toUpperCase() === "POST";
}

/**
 * Un `fetch` que contesta el login con `responderLogin` y `GET /auth/yo`
 * con `usuarioDeYo` (si se da). Cualquier otra cosa, 404.
 */
function apiDeIngreso(responderLogin: () => Promise<Response>, usuarioDeYo?: Usuario) {
  return fingirFetch(async (url, init) => {
    if (esLogin(url, init)) return responderLogin();
    if (usuarioDeYo && url.includes("/api/v1/auth/yo")) {
      return respuestaJson(200, usuarioDeYo);
    }
    return respuestaJson(404, { detail: "No encontrado." });
  });
}

/** Las llamadas a `POST /api/v1/auth/login`. */
function llamadasALogin(falso: FetchFingido) {
  return llamadas(falso).filter(
    (llamada) => llamada.metodo === "POST" && llamada.url.includes("/api/v1/auth/login"),
  );
}

/** Los cuerpos (ya leidos del JSON) de las llamadas a `POST /api/v1/auth/login`. */
function cuerposDeLogin(falso: FetchFingido): unknown[] {
  return falso.mock.calls
    .filter(([entrada, init]) => {
      const url =
        typeof entrada === "string"
          ? entrada
          : entrada instanceof URL
            ? entrada.toString()
            : entrada.url;
      return esLogin(url, init);
    })
    .map(([, init]) => JSON.parse(String(init?.body)));
}

function campoUsuario() {
  return screen.getByLabelText("Usuario");
}

function campoContrasena() {
  return screen.getByLabelText("Contraseña");
}

function botonIngresar() {
  return screen.getByRole("button", { name: /Ingresar/ });
}

/** Abre `/ingresar` y espera a que el formulario este a la vista. */
async function abrirIngreso() {
  abrir("/ingresar");
  await screen.findByLabelText("Usuario");
}

/** Escribe lo que se pasa (lo vacio no se escribe) y pulsa `Ingresar`. */
async function ingresar(
  usuario: ReturnType<typeof userEvent.setup>,
  nombreDeUsuario: string,
  contrasena: string,
) {
  if (nombreDeUsuario) await usuario.type(campoUsuario(), nombreDeUsuario);
  if (contrasena) await usuario.type(campoContrasena(), contrasena);
  await usuario.click(botonIngresar());
}

describe("Pantalla de ingreso", () => {
  it("el formulario tiene el campo Usuario, el campo Contraseña de tipo contraseña y el botón Ingresar", async () => {
    fingirFetch(async () => respuestaJson(404, { detail: "No encontrado." }));

    abrir("/ingresar");

    expect(await screen.findByLabelText("Usuario")).toBeInTheDocument();
    expect(campoContrasena()).toHaveAttribute("type", "password");
    expect(botonIngresar()).toBeInTheDocument();
  });

  it("se hace una sola llamada al login con el usuario y la contraseña tal como se escribieron", async () => {
    const api = apiDeIngreso(() => sinRespuesta());
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, " JPerez ", "Verano2026");

    await waitFor(() => expect(llamadasALogin(api)).toHaveLength(1));
    expect(cuerposDeLogin(api)).toEqual([{ username: " JPerez ", password: "Verano2026" }]);
  });

  it("al pulsar Enter en Contraseña se hace una llamada al login", async () => {
    const api = apiDeIngreso(() => sinRespuesta());
    const usuario = userEvent.setup();

    await abrirIngreso();
    await usuario.type(campoUsuario(), "jperez");
    await usuario.type(campoContrasena(), "Verano2026{Enter}");

    await waitFor(() => expect(llamadasALogin(api)).toHaveLength(1));
  });
});

describe("Campos vacíos no se envían", () => {
  it("con los dos campos vacíos aparecen los dos mensajes y no se llama a la API", async () => {
    const api = apiDeIngreso(() => sinRespuesta());
    const usuario = userEvent.setup();

    await abrirIngreso();
    await usuario.click(botonIngresar());

    expect(await screen.findByText(FALTA_USUARIO)).toBeInTheDocument();
    expect(await screen.findByText(FALTA_CONTRASENA)).toBeInTheDocument();
    expect(api).not.toHaveBeenCalled();
  });

  it("con el usuario de solo espacios aparece Ingresá tu usuario. y no se llama a la API", async () => {
    const api = apiDeIngreso(() => sinRespuesta());
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "   ", "Verano2026");

    expect(await screen.findByText(FALTA_USUARIO)).toBeInTheDocument();
    expect(api).not.toHaveBeenCalled();
  });

  it("con un usuario de un carácter se llama al login y no aparece Ingresá tu usuario.", async () => {
    const api = apiDeIngreso(() => sinRespuesta());
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "j", "Verano2026");

    await waitFor(() => expect(llamadasALogin(api)).toHaveLength(1));
    expect(screen.queryByText(FALTA_USUARIO)).not.toBeInTheDocument();
  });

  it("con la contraseña de solo espacios se llama al login con esos espacios", async () => {
    const api = apiDeIngreso(() => sinRespuesta());
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "jperez", "   ");

    await waitFor(() => expect(llamadasALogin(api)).toHaveLength(1));
    expect(cuerposDeLogin(api)).toEqual([{ username: "jperez", password: "   " }]);
  });
});

describe("Ingreso correcto guarda la sesión", () => {
  it("al ingresar la dirección pasa a /, se ve el nombre y el rol, y la petición siguiente lleva el token", async () => {
    const juana = usuarioYo({
      nombre: "Juana",
      apellido: "Pérez",
      rol: "coordinador",
      debe_cambiar_password: false,
    });
    const api = apiDeIngreso(async () => loginCorrecto("tok-123", juana), juana);
    const usuario = userEvent.setup();

    const primera = abrir("/ingresar");
    await screen.findByLabelText("Usuario");
    await ingresar(usuario, "jperez", "Verano2026");

    expect(await screen.findByText(/Juana Pérez/)).toBeInTheDocument();
    expect(screen.getAllByText(/\bCoordinador\b/).length).toBeGreaterThan(0);
    await waitFor(() => expect(direccion()).toBe("/"));
    // El inicio usa el usuario que vino en la respuesta, sin volver a pedirlo.
    expect(llamadasAYo(api)).toHaveLength(0);
    expect(localStorage.getItem(CLAVE_TOKEN)).toBe("tok-123");

    // La peticion siguiente a la API (al volver a montar en /) lleva el token.
    primera.unmount();
    api.mockClear();
    abrir("/");

    await waitFor(() => expect(llamadasAYo(api)).toHaveLength(1));
    expect(llamadasAYo(api)[0]?.autorizacion).toBe("Bearer tok-123");
  });

  it("al recargar la página en / se llama a GET /api/v1/auth/yo con el token del ingreso", async () => {
    const juana = usuarioYo({ nombre: "Juana", apellido: "Pérez" });
    const api = apiDeIngreso(async () => loginCorrecto("tok-123", juana), juana);
    const usuario = userEvent.setup();

    const primera = abrir("/ingresar");
    await screen.findByLabelText("Usuario");
    await ingresar(usuario, "jperez", "Verano2026");
    await screen.findByText(/Juana Pérez/);

    primera.unmount();
    api.mockClear();
    abrir("/");

    await waitFor(() => expect(llamadasAYo(api)).toHaveLength(1));
    expect(llamadasAYo(api)[0]?.autorizacion).toBe("Bearer tok-123");
  });
});

describe("Estado de carga del ingreso", () => {
  it("mientras la API no responde el botón Ingresar está deshabilitado y hay un indicador de progreso", async () => {
    const api = apiDeIngreso(() => sinRespuesta());
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "jperez", "Verano2026");

    await waitFor(() => expect(llamadasALogin(api)).toHaveLength(1));
    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
    await waitFor(() => expect(botonIngresar()).toBeDisabled());
  });

  it("un doble clic antes de que la API responda hace una sola llamada al login", async () => {
    const api = apiDeIngreso(() => sinRespuesta());
    // Sin la comprobacion de pointer-events: el segundo clic tiene que llegar
    // aunque el boton ya este deshabilitado, como lo haria una persona.
    const usuario = userEvent.setup({ pointerEventsCheck: 0 });

    await abrirIngreso();
    await usuario.type(campoUsuario(), "jperez");
    await usuario.type(campoContrasena(), "Verano2026");
    await usuario.click(botonIngresar());
    await usuario.click(botonIngresar());

    await waitFor(() => expect(llamadasALogin(api).length).toBeGreaterThan(0));
    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
    expect(llamadasALogin(api)).toHaveLength(1);
  });

  it("cuando la API responde 401 el botón Ingresar vuelve a estar habilitado", async () => {
    apiDeIngreso(async () => respuestaJson(401, { detail: CREDENCIALES_INCORRECTAS }));
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "jperez", "Otra1234");

    expect(await screen.findByText(CREDENCIALES_INCORRECTAS)).toBeInTheDocument();
    await waitFor(() => expect(botonIngresar()).toBeEnabled());
  });
});

describe("Error general del ingreso", () => {
  it("con credenciales incorrectas se ve el aviso, se conserva el usuario, se vacía la contraseña y no se guarda token", async () => {
    apiDeIngreso(async () => respuestaJson(401, { detail: CREDENCIALES_INCORRECTAS }));
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "jperez", "Otra1234");

    expect(await screen.findByText(CREDENCIALES_INCORRECTAS)).toBeInTheDocument();
    expect(campoUsuario()).toHaveValue("jperez");
    await waitFor(() => expect(campoContrasena()).toHaveValue(""));
    expect(localStorage.getItem(CLAVE_TOKEN)).toBeNull();
    expect(direccion()).toBe("/ingresar");
  });

  it("con el usuario bloqueado se ve el aviso del bloqueo y no se guarda token", async () => {
    apiDeIngreso(async () => respuestaJson(403, { detail: USUARIO_BLOQUEADO }));
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "jperez", "Verano2026");

    expect(await screen.findByText(USUARIO_BLOQUEADO)).toBeInTheDocument();
    expect(localStorage.getItem(CLAVE_TOKEN)).toBeNull();
  });

  it("sin conexión con el servidor se ve el aviso de conexión", async () => {
    fingirFetch(() => Promise.reject(new TypeError("Failed to fetch")));
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "jperez", "Verano2026");

    expect(await screen.findByText(MENSAJE_SIN_CONEXION)).toBeInTheDocument();
  });

  it("con un error 500 sin cuerpo JSON se ve el aviso de problema del servidor", async () => {
    apiDeIngreso(
      async () =>
        new Response("Internal Server Error", {
          status: 500,
          headers: { "Content-Type": "text/plain" },
        }),
    );
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "jperez", "Verano2026");

    expect(await screen.findByText(MENSAJE_ERROR_SERVIDOR)).toBeInTheDocument();
  });

  it("al volver a intentar con éxito el aviso ya no está y se ve la zona protegida", async () => {
    const juana = usuarioYo({ nombre: "Juana", apellido: "Pérez" });
    let intentos = 0;
    apiDeIngreso(async () => {
      intentos += 1;
      if (intentos === 1) return respuestaJson(401, { detail: CREDENCIALES_INCORRECTAS });
      return loginCorrecto("tok-123", juana);
    }, juana);
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "jperez", "Otra1234");
    await screen.findByText(CREDENCIALES_INCORRECTAS);
    await waitFor(() => expect(botonIngresar()).toBeEnabled());
    await usuario.type(campoContrasena(), "Verano2026");
    await usuario.click(botonIngresar());

    expect(await screen.findByText(/Juana Pérez/)).toBeInTheDocument();
    expect(screen.queryByText(CREDENCIALES_INCORRECTAS)).not.toBeInTheDocument();
  });
});

describe("Error por campo del ingreso", () => {
  it("si la API rechaza el usuario, el mensaje aparece al lado de Usuario, nada al lado de Contraseña y no se guarda token", async () => {
    const mensaje = "Value error, El usuario no puede tener caracteres de control.";
    apiDeIngreso(async () =>
      respuestaJson(422, {
        detail: [{ loc: ["body", "username"], msg: mensaje, type: "value_error" }],
      }),
    );
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "jperez", "Verano2026");

    expect(await screen.findByText(mensaje)).toBeInTheDocument();
    expect(screen.queryByText(FALTA_CONTRASENA)).not.toBeInTheDocument();
    expect(campoContrasena()).not.toHaveAttribute("aria-invalid", "true");
    expect(localStorage.getItem(CLAVE_TOKEN)).toBeNull();
  });

  it("si la API rechaza la contraseña, el mensaje aparece al lado de Contraseña", async () => {
    const mensaje = "String should have at most 128 characters";
    apiDeIngreso(async () =>
      respuestaJson(422, {
        detail: [{ loc: ["body", "password"], msg: mensaje, type: "string_too_long" }],
      }),
    );
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "jperez", "Verano2026");

    expect(await screen.findByText(mensaje)).toBeInTheDocument();
  });
});

describe("Aviso de cambio de contraseña pendiente", () => {
  it("al ingresar con el cambio pendiente se ve el aviso y Salir, y no el nombre ni el rol", async () => {
    const pendiente = usuarioYo({
      nombre: "Juana",
      apellido: "Pérez",
      rol: "coordinador",
      debe_cambiar_password: true,
    });
    apiDeIngreso(async () => loginCorrecto("tok-123", pendiente), pendiente);
    const usuario = userEvent.setup();

    await abrirIngreso();
    await ingresar(usuario, "jperez", "Verano2026");

    expect(await screen.findByText(TITULO_CAMBIO_PENDIENTE)).toBeInTheDocument();
    expect(screen.getByText(TEXTO_CAMBIO_PENDIENTE)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Salir" })).toBeInTheDocument();
    expect(screen.queryByText(/Juana Pérez/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bCoordinador\b/)).not.toBeInTheDocument();
  });
});
