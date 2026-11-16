/**
 * Tests de la zona protegida, la sesion rechazada, el inicio, el aviso de
 * cambio de contrasena pendiente (al recargar) y Salir.
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
  llamadasAYo,
  respuestaJson,
  sinRespuesta,
  usuarioYo,
} from "./montar";

const TITULO_CAMBIO_PENDIENTE = "Tenés que cambiar tu contraseña antes de continuar.";
const MENSAJE_SIN_CONEXION = "No se pudo conectar con el servidor. Revisá tu conexión.";

/** Un `fetch` que responde 200 a `GET /api/v1/auth/yo` con ese usuario. */
function apiConUsuario(usuario: ReturnType<typeof usuarioYo>) {
  return fingirFetch(async (url) => {
    if (url.includes("/api/v1/auth/yo")) return respuestaJson(200, usuario);
    return respuestaJson(404, { detail: "No encontrado." });
  });
}

describe("La zona protegida exige sesión", () => {
  it("sin token, la dirección pasa a /ingresar, se ve el formulario y no se llama a la API", async () => {
    const api = fingirFetch(async () => respuestaJson(200, {}));

    abrir("/");

    expect(await screen.findByLabelText("Usuario")).toBeInTheDocument();
    await waitFor(() => expect(direccion()).toBe("/ingresar"));
    expect(api).not.toHaveBeenCalled();
  });

  it("una dirección cualquiera sin token pasa a /ingresar", async () => {
    fingirFetch(async () => respuestaJson(200, {}));

    abrir("/familias");

    await waitFor(() => expect(direccion()).toBe("/ingresar"));
  });

  it("con token vigente se ve el nombre y el rol del usuario", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-vigente");
    apiConUsuario(
      usuarioYo({
        nombre: "Juana",
        apellido: "Pérez",
        rol: "admin",
        debe_cambiar_password: false,
      }),
    );

    abrir("/");

    expect(await screen.findByText(/Juana Pérez/)).toBeInTheDocument();
    expect(screen.getAllByText(/\bAdmin\b/).length).toBeGreaterThan(0);
  });

  it("mientras se comprueba el token se ve un indicador de carga y ni el inicio ni el formulario", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-vigente");
    const api = fingirFetch(() => sinRespuesta());

    abrir("/");

    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
    await waitFor(() => expect(llamadasAYo(api)).toHaveLength(1));
    expect(screen.queryByLabelText("Usuario")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Salir" })).not.toBeInTheDocument();
    expect(screen.queryByText(/Juana Pérez/)).not.toBeInTheDocument();
  });
});

describe("Sesión rechazada por la API", () => {
  it("con el token vencido o inválido la dirección pasa a /ingresar y no queda token guardado", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-vencido");
    const api = fingirFetch(async () => respuestaJson(401, { detail: "No autenticado." }));

    abrir("/");

    await waitFor(() => expect(direccion()).toBe("/ingresar"));
    expect(llamadasAYo(api)).toHaveLength(1);
    expect(localStorage.getItem(CLAVE_TOKEN)).toBeNull();
  });

  it("sin conexión al comprobar la sesión se ve el mensaje y Reintentar, y el token y la dirección se conservan", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-vigente");
    fingirFetch(() => Promise.reject(new TypeError("Failed to fetch")));

    abrir("/");

    expect(await screen.findByText(MENSAJE_SIN_CONEXION)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
    expect(localStorage.getItem(CLAVE_TOKEN)).toBe("tok-vigente");
    expect(direccion()).toBe("/");
  });

  it("al reintentar con la conexión de vuelta se ve el inicio con el nombre del usuario", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-vigente");
    let conexion = false;
    const api = fingirFetch(async (url) => {
      if (!conexion) throw new TypeError("Failed to fetch");
      if (url.includes("/api/v1/auth/yo")) {
        return respuestaJson(
          200,
          usuarioYo({
            nombre: "Juana",
            apellido: "Pérez",
            debe_cambiar_password: false,
          }),
        );
      }
      return respuestaJson(404, { detail: "No encontrado." });
    });
    const usuario = userEvent.setup();

    abrir("/");
    const reintentar = await screen.findByRole("button", {
      name: "Reintentar",
    });
    conexion = true;
    await usuario.click(reintentar);

    expect(await screen.findByText(/Juana Pérez/)).toBeInTheDocument();
    expect(llamadasAYo(api).length).toBeGreaterThanOrEqual(2);
  });
});

describe("Inicio de la zona protegida", () => {
  it("el inicio de un Profesor muestra Carlos Gómez, Profesor y el botón Salir", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-profesor");
    apiConUsuario(
      usuarioYo({
        nombre: "Carlos",
        apellido: "Gómez",
        rol: "profesor",
        debe_cambiar_password: false,
      }),
    );

    abrir("/");

    expect(await screen.findByText(/Carlos Gómez/)).toBeInTheDocument();
    expect(screen.getAllByText(/\bProfesor\b/).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Salir" })).toBeInTheDocument();
  });
});

describe("Aviso de cambio de contraseña pendiente", () => {
  it("al recargar con el cambio pendiente se ve el aviso y no se ve el inicio", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-pendiente");
    apiConUsuario(
      usuarioYo({
        nombre: "Carlos",
        apellido: "Gómez",
        rol: "profesor",
        debe_cambiar_password: true,
      }),
    );

    abrir("/");

    expect(await screen.findByText(TITULO_CAMBIO_PENDIENTE)).toBeInTheDocument();
    expect(screen.queryByText(/Carlos Gómez/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bProfesor\b/)).not.toBeInTheDocument();
  });

  it("sin el cambio pendiente no aparece el aviso", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-vigente");
    apiConUsuario(
      usuarioYo({
        nombre: "Juana",
        apellido: "Pérez",
        debe_cambiar_password: false,
      }),
    );

    abrir("/");

    // Se espera a que la sesion este comprobada para que la ausencia del
    // aviso no sea solo porque todavia no termino de cargar.
    expect(await screen.findByText(/Juana Pérez/)).toBeInTheDocument();
    expect(screen.queryByText(TITULO_CAMBIO_PENDIENTE)).not.toBeInTheDocument();
  });
});

describe("Salir", () => {
  it("al salir desde el inicio la dirección pasa a /ingresar, no queda token y no se llama a la API", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-vigente");
    const api = apiConUsuario(usuarioYo({ nombre: "Juana", apellido: "Pérez" }));
    const usuario = userEvent.setup();

    abrir("/");
    await screen.findByText(/Juana Pérez/);
    const llamadasAntes = api.mock.calls.length;
    await usuario.click(screen.getByRole("button", { name: "Salir" }));

    await waitFor(() => expect(direccion()).toBe("/ingresar"));
    expect(localStorage.getItem(CLAVE_TOKEN)).toBeNull();
    expect(api.mock.calls.length).toBe(llamadasAntes);
  });

  it("al salir desde el aviso de cambio pendiente la dirección pasa a /ingresar y no queda token", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-pendiente");
    apiConUsuario(usuarioYo({ debe_cambiar_password: true }));
    const usuario = userEvent.setup();

    abrir("/");
    await screen.findByText(TITULO_CAMBIO_PENDIENTE);
    await usuario.click(screen.getByRole("button", { name: "Salir" }));

    await waitFor(() => expect(direccion()).toBe("/ingresar"));
    expect(localStorage.getItem(CLAVE_TOKEN)).toBeNull();
  });

  it("después de salir, abrir / pasa a /ingresar sin llamar a GET /api/v1/auth/yo", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-vigente");
    const api = apiConUsuario(usuarioYo({ nombre: "Juana", apellido: "Pérez" }));
    const usuario = userEvent.setup();

    const primera = abrir("/");
    await screen.findByText(/Juana Pérez/);
    await usuario.click(screen.getByRole("button", { name: "Salir" }));
    await waitFor(() => expect(direccion()).toBe("/ingresar"));
    primera.unmount();
    api.mockClear();

    abrir("/");

    await waitFor(() => expect(direccion()).toBe("/ingresar"));
    expect(llamadasAYo(api)).toHaveLength(0);
  });
});
