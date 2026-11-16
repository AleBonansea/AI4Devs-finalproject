/**
 * Tests del inicio de la zona protegida: el saludo y los accesos, que ahora
 * son los del menu lateral.
 *
 * Spec: openspec/changes/menu-lateral-y-edad-de-grupos/specs/auth/spec.md,
 * Requirement «Inicio de la zona protegida» (MODIFIED). Reemplaza a
 * inicio-registrar, inicio-asistencia e inicio-cargo, escritos cuando el
 * inicio tenia botones de acceso propios.
 * Un `describe` por Requirement y un `it` por Scenario, con su nombre.
 */
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { abrir, direccion, esperarSesion, menu, sesionDe } from "../navegacion/apoyo";

/** Los "no se ve" de los accesos a cobrar, en toda la pagina. */
function expectSinAccesosACobrar() {
  for (const nombre of ["Registrar cargo", "Cuenta corriente"]) {
    expect(screen.queryByText(nombre)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: nombre })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: nombre })).not.toBeInTheDocument();
  }
}

describe("Inicio de la zona protegida", () => {
  it("Inicio de un Profesor", async () => {
    sesionDe("profesor");

    abrir("/");

    expect(await screen.findByText("Hola, Carlos")).toBeInTheDocument();
    expect(screen.getByText(/Carlos Gómez/)).toBeInTheDocument();
    expect(screen.getAllByText(/\bProfesor\b/).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Salir" })).toBeInTheDocument();
  });

  it("El inicio no repite los accesos del menú", async () => {
    sesionDe("admin");

    abrir("/");
    await screen.findByText("Hola, Juana");

    for (const nombre of [
      "Registrar alumno",
      "Tomar asistencia",
      "Registrar cargo",
      "Cuenta corriente",
    ]) {
      const textos = screen.getAllByText(nombre);
      expect(textos, nombre).toHaveLength(1);
      expect(menu()).toContainElement(textos[0] ?? null);
      const accesos = [
        ...screen.queryAllByRole("link", { name: nombre }),
        ...screen.queryAllByRole("button", { name: nombre }),
      ];
      expect(accesos, nombre).toHaveLength(1);
      expect(within(menu()).getByRole("link", { name: nombre })).toBe(accesos[0]);
    }
  });

  it("Ir a registrar un alumno", async () => {
    sesionDe("coordinador");
    const usuario = userEvent.setup();

    abrir("/");
    await esperarSesion("coordinador");
    await usuario.click(screen.getByRole("link", { name: "Registrar alumno" }));

    await waitFor(() => expect(direccion()).toBe("/alumnos/nuevo"));
  });

  it("Ir a tomar asistencia", async () => {
    sesionDe("profesor");
    const usuario = userEvent.setup();

    abrir("/");
    await esperarSesion("profesor");
    await usuario.click(screen.getByRole("link", { name: "Tomar asistencia" }));

    await waitFor(() => expect(direccion()).toBe("/asistencia"));
  });

  it("Ir a registrar un cargo", async () => {
    sesionDe("admin");
    const usuario = userEvent.setup();

    abrir("/");
    await esperarSesion("admin");
    await usuario.click(screen.getByRole("link", { name: "Registrar cargo" }));

    await waitFor(() => expect(direccion()).toBe("/cargos/nuevo"));
  });

  it("Ir a la cuenta corriente", async () => {
    sesionDe("admin");
    const usuario = userEvent.setup();

    abrir("/");
    await esperarSesion("admin");
    await usuario.click(screen.getByRole("link", { name: "Cuenta corriente" }));

    await waitFor(() => expect(direccion()).toBe("/cuenta-corriente"));
  });

  it("El Coordinador no ve el acceso a cobrar", async () => {
    sesionDe("coordinador");

    abrir("/");
    await esperarSesion("coordinador");

    expect(screen.getByRole("link", { name: "Registrar alumno" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Tomar asistencia" })).toBeInTheDocument();
    expectSinAccesosACobrar();
  });

  it("El Profesor no ve el acceso a cobrar", async () => {
    sesionDe("profesor");

    abrir("/");
    await esperarSesion("profesor");

    // Lo que si se ve, para que el "no se ve" no se apruebe en blanco.
    expect(screen.getByText("Hola, Carlos")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Registrar alumno" })).toBeInTheDocument();
    expectSinAccesosACobrar();
  });
});
