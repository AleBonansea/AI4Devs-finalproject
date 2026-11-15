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

/**
 * Escribe un monto de la API para un campo de formulario: como
 * `formatearMonto` pero sin el `$ ` (`55.000`, `4.462,50`). Un texto mal
 * formado lanza `Error`.
 */
export function montoParaEditar(monto: string): string {
  const [entero, centavos] = partir(monto, "monto");
  const parteEntera = conMiles(entero);
  return centavos === "00" ? parteEntera : `${parteEntera},${centavos}`;
}

/** Lo que escribe una persona: miles con punto (opcionales) y hasta dos decimales con coma. */
const MONTO_ESCRITO = /^(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?$/;

/**
 * Lee un monto escrito a mano (`55.000`, `4.462,50`, `4462,5`) y lo devuelve
 * como texto de la API con dos decimales (`"4462.50"`), o `null` si no se
 * entiende. Ignora los espacios alrededor. Trabaja sobre el texto, sin
 * `Number` ni `parseFloat`.
 */
export function leerMonto(texto: string): string | null {
  const partes = MONTO_ESCRITO.exec(texto.trim());
  if (!partes) {
    return null;
  }
  const [, entero = "", decimales = ""] = partes;
  return `${entero.replace(/\./g, "")}.${decimales.padEnd(2, "0")}`;
}
