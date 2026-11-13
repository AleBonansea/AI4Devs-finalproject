/**
 * Los enumerados de la API escritos para personas. Una tabla por enumerado,
 * en un solo lugar: si manana `no_socio` se escribe distinto, cambia aca.
 */
import type { CategoriaFamilia, RolUsuario, Turno } from "./api";

export const NOMBRE_DEL_ROL: Record<RolUsuario, string> = {
  admin: "Admin",
  coordinador: "Coordinador",
  profesor: "Profesor",
};

export const NOMBRE_DEL_TURNO: Record<Turno, string> = {
  manana: "Mañana",
  tarde: "Tarde",
};

export const NOMBRE_DE_LA_CATEGORIA: Record<CategoriaFamilia, string> = {
  socio: "Socio",
  empleado: "Empleado",
  no_socio: "No socio",
};
