/**
 * Los montos y porcentajes como texto, en un solo lugar.
 *
 * La API manda los decimales como texto con dos cifras (`"4462.50"`). Todo
 * monto o porcentaje que se muestra pasa por `formatearMonto` o
 * `formatearPorcentaje`. Trabajan sobre el texto, sin `Number` ni
 * `parseFloat`: un importe no pasa nunca por un flotante.
 */

const DECIMAL_DE_API = /^(\d+)\.(\d{2})$/;

/** Parte el texto en entero y decimales; cualquier otro texto lanza `Error`. */
function partir(texto: string, que: string): [string, string] {
  const partes = DECIMAL_DE_API.exec(texto);
  if (!partes) {
    throw new Error(`El ${que} «${texto}» no tiene el formato 0.00.`);
  }
  const [, entero = "", decimales = ""] = partes;
  return [entero, decimales];
}

/** Agrupa los miles del entero con punto. */
function conMiles(entero: string): string {
  return entero.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

/**
 * Escribe un monto como `$ 85.000` o `$ 4.462,50`: miles con punto,
 * decimales con coma, y los centavos solo si no son `00`.
 */
export function formatearMonto(monto: string): string {
  const [entero, centavos] = partir(monto, "monto");
  const parteEntera = conMiles(entero);
  return centavos === "00" ? `$ ${parteEntera}` : `$ ${parteEntera},${centavos}`;
}

/**
 * Escribe un porcentaje como `15 %`, `36,25 %` o `57,5 %`: decimales con
 * coma y sin ceros finales.
 */
export function formatearPorcentaje(porcentaje: string): string {
  const [entero, decimales] = partir(porcentaje, "porcentaje");
  const sinCeros = decimales.replace(/0+$/, "");
  return sinCeros === "" ? `${entero} %` : `${entero},${sinCeros} %`;
}
