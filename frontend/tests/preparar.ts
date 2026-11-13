/**
 * Preparacion comun de todos los tests del frontend.
 *
 * Cada test arranca como un navegador recien abierto: sin token guardado,
 * sin el DOM del test anterior y con el `fetch` de verdad restaurado. Nada
 * depende del orden ni de lo que dejo otro test.
 */
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
});
