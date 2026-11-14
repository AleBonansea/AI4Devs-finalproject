/**
 * Las fechas como texto, en un solo lugar.
 *
 * Toda fecha que se muestra como texto (fuera de un campo de formulario)
 * pasa por `formatearFecha` y sale en `dd/mm/aaaa`.
 */

const FECHA_ISO = /^(\d{4})-(\d{2})-(\d{2})$/;

function conDosCifras(numero: number): string {
  return String(numero).padStart(2, "0");
}

/**
 * Escribe una fecha como `dd/mm/aaaa`.
 *
 * Con un texto `AAAA-MM-DD` (como la manda la API) lo corta por partes y NO
 * pasa por `Date`: `new Date("2027-01-05")` es la medianoche UTC, que en
 * Argentina todavia es el 04/01. Con un `Date` usa el dia, mes y ano locales.
 * Cualquier otro texto es un error de programacion y lanza `Error`.
 */
export function formatearFecha(fecha: string | Date): string {
  if (fecha instanceof Date) {
    const dia = conDosCifras(fecha.getDate());
    const mes = conDosCifras(fecha.getMonth() + 1);
    return `${dia}/${mes}/${fecha.getFullYear()}`;
  }
  const partes = FECHA_ISO.exec(fecha);
  if (!partes) {
    throw new Error(`La fecha «${fecha}» no tiene el formato AAAA-MM-DD.`);
  }
  const [, anio, mes, dia] = partes;
  return `${dia}/${mes}/${anio}`;
}
