/**
 * Como se nombra un cargo en pantalla (`Abono · Mes 1`). El renglon de la
 * cuenta corriente y el formulario de pago lo escriben igual, asi que sale de
 * un solo lugar.
 */
import type { CargoEnCuenta } from "./api";
import { formatearFecha } from "./fechas";

export function descripcionDeCargo(cargo: CargoEnCuenta): string {
  if (cargo.periodo) return `${cargo.tipo_cargo} · ${cargo.periodo.nombre}`;
  if (cargo.modalidad === "dia" && cargo.fecha_dia) {
    return `${cargo.tipo_cargo} · Día ${formatearFecha(cargo.fecha_dia)}`;
  }
  return cargo.tipo_cargo;
}
