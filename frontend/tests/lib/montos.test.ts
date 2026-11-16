/**
 * Tests de `formatearMonto` y `formatearPorcentaje`, la unica forma de
 * mostrar un monto o un porcentaje como texto.
 *
 * Fuente: openspec/changes/cobro/design.md, seccion «Frontend», viñeta
 * «`src/lib/montos.ts`», que fija estos casos. El espacio entre `$` y el
 * numero, y entre el numero y `%`, es un espacio comun (U+0020).
 */
import { describe, expect, it } from "vitest";
import {
  formatearMonto,
  formatearPorcentaje,
  leerMonto,
  montoParaEditar,
} from "../../src/lib/montos";

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

/*
 * `montoParaEditar` y `leerMonto`: el monto que se propone en un campo de
 * texto y la lectura de lo que escribe la persona, de vuelta al texto con dos
 * decimales que espera la API.
 *
 * Fuente: openspec/changes/cuenta-corriente/design.md, seccion «Frontend»,
 * viñeta «`src/lib/montos.ts`», que fija estos casos.
 */
describe("montoParaEditar", () => {
  it("55000.00 se propone como 55.000, sin $ ni centavos en cero", () => {
    expect(montoParaEditar("55000.00")).toBe("55.000");
  });

  it("4462.50 se propone como 4.462,50, con los centavos completos", () => {
    expect(montoParaEditar("4462.50")).toBe("4.462,50");
  });

  it("0.05 se propone como 0,05", () => {
    expect(montoParaEditar("0.05")).toBe("0,05");
  });
});

describe("leerMonto", () => {
  it("55.000 se lee como 55000.00", () => {
    expect(leerMonto("55.000")).toBe("55000.00");
  });

  it("55000, sin separador de miles, se lee como 55000.00", () => {
    expect(leerMonto("55000")).toBe("55000.00");
  });

  it("4.462,50 se lee como 4462.50", () => {
    expect(leerMonto("4.462,50")).toBe("4462.50");
  });

  it("4462,5, con un solo decimal, se lee como 4462.50", () => {
    expect(leerMonto("4462,5")).toBe("4462.50");
  });

  it("0,01 se lee como 0.01", () => {
    expect(leerMonto("0,01")).toBe("0.01");
  });

  it("los espacios alrededor no cuentan: '  4.462,50  ' se lee como 4462.50", () => {
    expect(leerMonto("  4.462,50  ")).toBe("4462.50");
  });

  it("4,462.50, con los separadores al reves, devuelve null", () => {
    expect(leerMonto("4,462.50")).toBeNull();
  });

  it("4462.50 devuelve null, porque el punto es de miles", () => {
    expect(leerMonto("4462.50")).toBeNull();
  });

  it("44.62, con un grupo de miles de dos cifras, devuelve null", () => {
    expect(leerMonto("44.62")).toBeNull();
  });

  it("1.2345, con un grupo de miles de cuatro cifras, devuelve null", () => {
    expect(leerMonto("1.2345")).toBeNull();
  });

  it("4462,505, con tres decimales, devuelve null", () => {
    expect(leerMonto("4462,505")).toBeNull();
  });

  it("-10 devuelve null", () => {
    expect(leerMonto("-10")).toBeNull();
  });

  it("abc devuelve null", () => {
    expect(leerMonto("abc")).toBeNull();
  });

  it("el texto vacio devuelve null", () => {
    expect(leerMonto("")).toBeNull();
  });
});
