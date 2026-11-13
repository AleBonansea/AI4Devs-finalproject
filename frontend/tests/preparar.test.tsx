/**
 * Comprueba que la preparacion de tests/preparar.ts hace lo que promete.
 *
 * Si un test pudiera ver el token o el `fetch` fingido del anterior, los
 * tests de sesion se aprobarian o fallarian segun el orden. Ademas deja la
 * suite con al menos un test, asi `vitest run` no sale con error.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

describe("preparacion de los tests", () => {
  const fetchOriginal = globalThis.fetch;

  it("un test escribe en localStorage y finge fetch", () => {
    localStorage.setItem("escuelita.token", "de-un-test-anterior");
    vi.stubGlobal("fetch", vi.fn());
    expect(localStorage.getItem("escuelita.token")).toBe("de-un-test-anterior");
    expect(globalThis.fetch).not.toBe(fetchOriginal);
  });

  it("el siguiente arranca sin token y con el fetch restaurado", () => {
    expect(localStorage.getItem("escuelita.token")).toBeNull();
    expect(globalThis.fetch).toBe(fetchOriginal);
  });

  it("los matchers de jest-dom estan cargados y el DOM empieza vacio", () => {
    expect(document.body).toBeEmptyDOMElement();
    render(<p>hola</p>);
    expect(screen.getByText("hola")).toBeInTheDocument();
  });
});
