import Box from "@mui/material/Box";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListSubheader from "@mui/material/ListSubheader";
import { NavLink } from "react-router-dom";

import type { RolUsuario } from "../lib/api";
import { colores } from "../tema";

interface Opcion {
  texto: string;
  ruta: string;
  /** Solo `Inicio`: `/` no debe quedar marcada en todas las pantallas. */
  exacta?: boolean;
}

interface Seccion {
  titulo: string;
  soloAdmin?: boolean;
  opciones: Opcion[];
}

// Las opciones del menu, en un solo lugar. Sumar una pantalla es sumar un renglon.
const SECCIONES: Seccion[] = [
  {
    titulo: "Escuela",
    opciones: [
      { texto: "Inicio", ruta: "/", exacta: true },
      { texto: "Registrar alumno", ruta: "/alumnos/nuevo" },
      { texto: "Tomar asistencia", ruta: "/asistencia" },
    ],
  },
  {
    titulo: "Administración",
    soloAdmin: true,
    opciones: [
      { texto: "Registrar cargo", ruta: "/cargos/nuevo" },
      { texto: "Cuenta corriente", ruta: "/cuenta-corriente" },
    ],
  },
];

interface Props {
  rol: RolUsuario;
}

/**
 * El menu de la zona protegida. Desde `md` es una columna; debajo, una fila
 * que se desplaza hacia el costado. Es la misma lista en los dos anchos.
 */
export default function MenuLateral({ rol }: Props) {
  return (
    <nav aria-label="Menú principal">
      {/* El contenedor hace la fila (debajo de md) o la columna; cada seccion es una lista. */}
      <Box
        sx={{
          display: "flex",
          flexDirection: { xs: "row", md: "column" },
          alignItems: { xs: "center", md: "stretch" },
          overflowX: { xs: "auto", md: "visible" },
          p: 1,
        }}
      >
        {SECCIONES.filter((seccion) => !seccion.soloAdmin || rol === "admin").map((seccion) => (
          <List
            key={seccion.titulo}
            disablePadding
            aria-labelledby={`menu-seccion-${seccion.titulo}`}
            sx={{
              display: "flex",
              flexDirection: { xs: "row", md: "column" },
              alignItems: { xs: "center", md: "stretch" },
              flexShrink: 0,
            }}
          >
            <ListSubheader
              component="div"
              id={`menu-seccion-${seccion.titulo}`}
              sx={{
                bgcolor: "transparent",
                color: "text.secondary",
                lineHeight: 2,
                px: 2,
                flexShrink: 0,
                whiteSpace: "nowrap",
              }}
            >
              {seccion.titulo}
            </ListSubheader>
            {seccion.opciones.map((opcion) => (
              <ListItemButton
                key={opcion.ruta}
                component={NavLink}
                to={opcion.ruta}
                end={opcion.exacta}
                sx={{
                  borderRadius: 1,
                  flexShrink: 0,
                  whiteSpace: "nowrap",
                  // Texto oscuro para el contraste; la marca de color va en el borde.
                  "&.active": {
                    bgcolor: colores.accionSuave,
                    color: colores.texto,
                    fontWeight: 700,
                    borderLeft: { md: `3px solid ${colores.accion}` },
                    borderBottom: { xs: `3px solid ${colores.accion}`, md: 0 },
                  },
                }}
              >
                {opcion.texto}
              </ListItemButton>
            ))}
          </List>
        ))}
      </Box>
    </nav>
  );
}
