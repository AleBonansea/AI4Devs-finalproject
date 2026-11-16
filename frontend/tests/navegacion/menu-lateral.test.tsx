/**
 * Tests del encabezado y el menu lateral de la zona protegida.
 *
 * Spec: openspec/changes/menu-lateral-y-edad-de-grupos/specs/navegacion/spec.md
 * Un `describe` por Requirement y un `it` por Scenario, con su nombre.
 */
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { CLAVE_TOKEN, fingirFetch, llamadasAYo, respuestaJson, sinRespuesta } from "../auth/montar";
import {
  OPCIONES_ADMIN,
  OPCIONES_ESCUELA,
  abrir,
  direccion,
  esperarSesion,
  menu,
  opcion,
  recorrido,
  sesionDe,
  textosDe,
} from "./apoyo";

const TITULO_CAMBIO_PENDIENTE = "Tenés que cambiar tu contraseña antes de continuar.";

/** El "no se ve" de las opciones de Administracion, en toda la pagina. */
function expectSinAdministracion() {
  expect(screen.queryByText("Administración")).not.toBeInTheDocument();
  for (const nombre of OPCIONES_ADMIN) {
    expect(screen.queryByText(nombre)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: nombre })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: nombre })).not.toBeInTheDocument();
  }
}

/** El "no se ve" de las opciones de la seccion Escuela, en toda la pagina. */
function expectSinOpcionesDeEscuela() {
  expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  for (const nombre of OPCIONES_ESCUELA) {
    expect(screen.queryByText(nombre)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: nombre })).not.toBeInTheDocument();
  }
}

describe("Encabezado de la zona protegida", () => {
  it("Encabezado en una pantalla que no es el inicio", async () => {
    sesionDe("profesor");

    abrir("/asistencia");

    expect(await screen.findByText(/Carlos Gómez/)).toBeInTheDocument();
    expect(screen.getAllByText("Escuela de Verano").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/\bProfesor\b/).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Salir" })).toBeInTheDocument();
    expect(direccion()).toBe("/asistencia");
  });

  it("Salir desde otra pantalla", async () => {
    sesionDe("coordinador");
    const usuario = userEvent.setup();

    abrir("/alumnos/nuevo");
    await esperarSesion("coordinador");
    await usuario.click(screen.getByRole("button", { name: "Salir" }));

    await waitFor(() => expect(direccion()).toBe("/ingresar"));
    expect(localStorage.getItem(CLAVE_TOKEN)).toBeNull();
  });
});

describe("Opciones del menú según el rol", () => {
  it("Menú del Admin", async () => {
    sesionDe("admin");

    abrir("/");
    await esperarSesion("admin");

    expect(textosDe(menu())).toEqual([
      "Escuela",
      "Inicio",
      "Registrar alumno",
      "Tomar asistencia",
      "Administración",
      "Registrar cargo",
      "Cuenta corriente",
    ]);
    const enlaces = within(menu()).getAllByRole("link");
    expect(enlaces.map((enlace) => enlace.textContent?.trim())).toEqual([
      "Inicio",
      "Registrar alumno",
      "Tomar asistencia",
      "Registrar cargo",
      "Cuenta corriente",
    ]);
    expect(enlaces.map((enlace) => enlace.getAttribute("href"))).toEqual([
      "/",
      "/alumnos/nuevo",
      "/asistencia",
      "/cargos/nuevo",
      "/cuenta-corriente",
    ]);
  });

  it("Menú del Coordinador", async () => {
    sesionDe("coordinador");

    abrir("/");
    await esperarSesion("coordinador");

    for (const nombre of OPCIONES_ESCUELA) {
      expect(opcion(nombre)).toBeInTheDocument();
    }
    expectSinAdministracion();
  });

  it("Menú del Profesor", async () => {
    sesionDe("profesor");

    abrir("/asistencia");
    await esperarSesion("profesor");

    for (const nombre of OPCIONES_ESCUELA) {
      expect(opcion(nombre)).toBeInTheDocument();
    }
    expectSinAdministracion();
  });
});

describe("Moverse desde el menú", () => {
  it("De registrar alumno a tomar asistencia", async () => {
    sesionDe("coordinador");
    const usuario = userEvent.setup();

    abrir("/alumnos/nuevo");
    await esperarSesion("coordinador");
    await usuario.click(opcion("Tomar asistencia"));

    await waitFor(() => expect(direccion()).toBe("/asistencia"));
    // Sin pasar por el inicio.
    expect(recorrido).toEqual(["/alumnos/nuevo", "/asistencia"]);
  });

  it("De la cuenta corriente a registrar un cargo", async () => {
    sesionDe("admin");
    const usuario = userEvent.setup();

    abrir("/cuenta-corriente");
    await esperarSesion("admin");
    await usuario.click(opcion("Registrar cargo"));

    await waitFor(() => expect(direccion()).toBe("/cargos/nuevo"));
    expect(recorrido).toEqual(["/cuenta-corriente", "/cargos/nuevo"]);
  });

  it("Volver al inicio", async () => {
    sesionDe("profesor");
    const usuario = userEvent.setup();

    abrir("/asistencia");
    await esperarSesion("profesor");
    await usuario.click(opcion("Inicio"));

    await waitFor(() => expect(direccion()).toBe("/"));
    expect(recorrido).toEqual(["/asistencia", "/"]);
  });
});

describe("La pantalla abierta queda marcada en el menú", () => {
  it("Marcada en tomar asistencia", async () => {
    sesionDe("profesor");

    abrir("/asistencia");
    await esperarSesion("profesor");

    expect(opcion("Tomar asistencia")).toHaveAttribute("aria-current", "page");
    expect(opcion("Inicio")).not.toHaveAttribute("aria-current", "page");
    expect(opcion("Registrar alumno")).not.toHaveAttribute("aria-current", "page");
  });

  it("Marcada en el inicio", async () => {
    sesionDe("coordinador");

    abrir("/");
    await esperarSesion("coordinador");

    expect(opcion("Inicio")).toHaveAttribute("aria-current", "page");
    expect(opcion("Registrar alumno")).not.toHaveAttribute("aria-current", "page");
    expect(opcion("Tomar asistencia")).not.toHaveAttribute("aria-current", "page");
  });
});

describe("Sin menú fuera de la zona habilitada", () => {
  it("El ingreso no tiene menú", async () => {
    fingirFetch(async () => respuestaJson(404, { detail: "No encontrado." }));

    abrir("/ingresar");

    expect(await screen.findByLabelText("Usuario")).toBeInTheDocument();
    expectSinOpcionesDeEscuela();
  });

  it("Mientras se comprueba la sesión no hay menú", async () => {
    localStorage.setItem(CLAVE_TOKEN, "tok-profesor");
    // `GET /api/v1/auth/yo` no responde durante el test; el resto, 404.
    const falso = fingirFetch(async (url) =>
      url.includes("/api/v1/auth/yo")
        ? sinRespuesta()
        : respuestaJson(404, { detail: "No encontrado." }),
    );

    abrir("/asistencia");

    expect(
      await screen.findByRole("progressbar", { name: "Comprobando la sesión" }),
    ).toBeInTheDocument();
    // La comprobacion esta en curso: se pidio `yo` y no hubo respuesta.
    await waitFor(() => expect(llamadasAYo(falso).length).toBeGreaterThan(0));
    expectSinOpcionesDeEscuela();
  });

  it("El cambio de contraseña pendiente no tiene menú", async () => {
    sesionDe("profesor", true);

    abrir("/asistencia");

    expect(await screen.findByText(TITULO_CAMBIO_PENDIENTE)).toBeInTheDocument();
    expectSinOpcionesDeEscuela();
  });
});
