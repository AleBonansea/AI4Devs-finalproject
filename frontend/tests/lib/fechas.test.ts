/**
 * Tests de `formatearFecha`, la unica forma de mostrar una fecha como texto.
 *
 * Fuente: openspec/changes/asistencia/design.md, seccion «Frontend: las
 * fechas como texto, en `src/lib/fechas.ts`», que fija estos cinco casos.
 */
import { describe, expect, it } from "vitest";
import { formatearFecha } from "../../src/lib/fechas";

describe("formatearFecha", () => {
  it("2027-01-05 se escribe 05/01/2027", () => {
    expect(formatearFecha("2027-01-05")).toBe("05/01/2027");
  });

  it("2027-02-26 se escribe 26/02/2027, sin invertir día y mes", () => {
    expect(formatearFecha("2027-02-26")).toBe("26/02/2027");
  });

  it("un Date local del 5 de enero a las 23:30 se escribe 05/01/2027", () => {
    expect(formatearFecha(new Date(2027, 0, 5, 23, 30))).toBe("05/01/2027");
  });

  it("un texto 05/01/2027 lanza Error", () => {
    expect(() => formatearFecha("05/01/2027")).toThrow(Error);
  });

  it("un texto 2027-1-5 lanza Error", () => {
    expect(() => formatearFecha("2027-1-5")).toThrow(Error);
  });
});
