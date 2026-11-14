/**
 * Tests del acceso `Registrar cargo` desde el inicio de la zona protegida.
 *
 * Spec: openspec/changes/cobro/specs/auth/spec.md, Requirement «Inicio de la
 * zona protegida», Scenarios «Ir a registrar un cargo», «El Coordinador no ve
 * el acceso a cobrar» y «El Profesor no ve el acceso a cobrar». Los otros
 * Scenarios del Requirement estan en zona-protegida.test.tsx,
 * inicio-registrar.test.tsx e inicio-asistencia.test.tsx.
 */
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { CLAVE_TOKEN, abrir, direccion, fingirFetch, respuestaJson, usuarioYo } from "./montar";

type Rol = "admin" | "coordinador" | "profesor";

/** Finge la API con la sesion de `rol` y devuelve el stub. */
function sesionDe(rol: Rol, nombre: string, apellido: string) {
  localStorage.setItem(CLAVE_TOKEN, `tok-${rol}`);
  return fingirFetch(async (url) => {
    if (url.includes("/api/v1/auth/yo")) {
      return respuestaJson(200, usuarioYo({ nombre, apellido, rol, debe_cambiar_password: false }));
    }
    if (url.includes("/api/v1/cargos/opciones")) {
      return respuestaJson(200, { tipos_cargo: [], periodos: [] });
    }
    if (url.includes("/api/v1/grupos")) return respuestaJson(200, []);
    return respuestaJson(404, { detail: "No encontrado." });
  });
}

/** El acceso con ese nombre, sea enlace o boton; null si no esta. */
function accesoONada(nombre: string): HTMLElement | null {
  return (
    screen.queryByRole("link", { name: nombre }) ?? screen.queryByRole("button", { name: nombre })
  );
}

describe("Inicio de la zona protegida", () => {
  it("al pulsar Registrar cargo desde el inicio la dirección pasa a /cargos/nuevo", async () => {
    sesionDe("admin", "Juana", "Pérez");
    const usuario = userEvent.setup();

    abrir("/");
    await screen.findByText(/Juana Pérez/);
    const acceso =
      screen.queryByRole("link", { name: "Registrar cargo" }) ??
      screen.getByRole("button", { name: "Registrar cargo" });
    await usuario.click(acceso);

    await waitFor(() => expect(direccion()).toBe("/cargos/nuevo"));
  });

  it("el Coordinador ve Registrar alumno y Tomar asistencia y no ve Registrar cargo", async () => {
    sesionDe("coordinador", "Lucía", "Rodríguez");

    abrir("/");
    await screen.findByText(/Lucía Rodríguez/);

    expect(accesoONada("Registrar alumno")).not.toBeNull();
    expect(accesoONada("Tomar asistencia")).not.toBeNull();
    expect(accesoONada("Registrar cargo")).toBeNull();
    expect(screen.queryByText("Registrar cargo")).toBeNull();
  });

  it("el Profesor no ve Registrar cargo", async () => {
    sesionDe("profesor", "Carlos", "Gómez");

    abrir("/");
    await screen.findByText(/Carlos Gómez/);

    // Lo que si se ve, para que el "no se ve" no se apruebe en blanco.
    expect(accesoONada("Registrar alumno")).not.toBeNull();
    expect(accesoONada("Registrar cargo")).toBeNull();
    expect(screen.queryByText("Registrar cargo")).toBeNull();
  });
});
