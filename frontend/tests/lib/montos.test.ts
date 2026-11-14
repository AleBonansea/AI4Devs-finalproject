/**
 * Tests de `formatearMonto` y `formatearPorcentaje`, la unica forma de
 * mostrar un monto o un porcentaje como texto.
 *
 * Fuente: openspec/changes/cobro/design.md, seccion «Frontend», viñeta
 * «`src/lib/montos.ts`», que fija estos casos. El espacio entre `$` y el
 * numero, y entre el numero y `%`, es un espacio comun (U+0020).
 */
import { describe, expect, it } from "vitest";
import { formatearMonto, formatearPorcentaje } from "../../src/lib/montos";

describe("formatearMonto", () => {
  it("85000.00 se escribe $ 85.000, sin centavos en cero", () => {
    expect(formatearMonto("85000.00")).toBe("$ 85.000");
  });

  it("4462.50 se escribe $ 4.462,50, con los centavos completos", () => {
    expect(formatearMonto("4462.50")).toBe("$ 4.462,50");
  });

  it("500.03 se escribe $ 500,03, sin separador de miles", () => {
    expect(formatearMonto("500.03")).toBe("$ 500,03");
  });

  it("1000000.00 se escribe $ 1.000.000, con dos separadores de miles", () => {
    expect(formatearMonto("1000000.00")).toBe("$ 1.000.000");
  });

  it("0.00 se escribe $ 0", () => {
    expect(formatearMonto("0.00")).toBe("$ 0");
  });

  it("un texto 85000 lanza Error", () => {
    expect(() => formatearMonto("85000")).toThrow(Error);
  });

  it("un texto 85000.5 lanza Error", () => {
    expect(() => formatearMonto("85000.5")).toThrow(Error);
  });

  it("un texto 1e5 lanza Error", () => {
    expect(() => formatearMonto("1e5")).toThrow(Error);
  });
});

describe("formatearPorcentaje", () => {
  it("15.00 se escribe 15 %", () => {
    expect(formatearPorcentaje("15.00")).toBe("15 %");
  });

  it("36.25 se escribe 36,25 %", () => {
    expect(formatearPorcentaje("36.25")).toBe("36,25 %");
  });

  it("57.50 se escribe 57,5 %, sin el cero final", () => {
    expect(formatearPorcentaje("57.50")).toBe("57,5 %");
  });

  it("0.00 se escribe 0 %", () => {
    expect(formatearPorcentaje("0.00")).toBe("0 %");
  });

  it("un texto 85000 lanza Error", () => {
    expect(() => formatearPorcentaje("85000")).toThrow(Error);
  });

  it("un texto 85000.5 lanza Error", () => {
    expect(() => formatearPorcentaje("85000.5")).toThrow(Error);
  });

  it("un texto 1e5 lanza Error", () => {
    expect(() => formatearPorcentaje("1e5")).toThrow(Error);
  });
});
