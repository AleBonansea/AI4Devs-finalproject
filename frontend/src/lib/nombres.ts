/**
 * Los enumerados de la API escritos para personas. Una tabla por enumerado,
 * en un solo lugar: si manana `no_socio` se escribe distinto, cambia aca.
 */
import type { CategoriaFamilia, GrupoParaInscribir, Modalidad, RolUsuario, Turno } from "./api";

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

export const NOMBRE_DE_LA_MODALIDAD: Record<Modalidad, string> = {
  mes: "Mes",
  quincena: "Quincena",
  semana: "Semana",
  dia: "Día",
};

/** Un grupo para el selector: `Delfines · Mañana · 5 a 6 años`, o `7 años` si las edades coinciden. */
export function textoDelGrupo(
  grupo: Pick<GrupoParaInscribir, "nombre" | "turno" | "edad_desde" | "edad_hasta">,
): string {
  const edad =
    grupo.edad_desde === grupo.edad_hasta
      ? `${grupo.edad_desde} años`
      : `${grupo.edad_desde} a ${grupo.edad_hasta} años`;
  return `${grupo.nombre} · ${NOMBRE_DEL_TURNO[grupo.turno]} · ${edad}`;
}
