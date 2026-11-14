import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

import { colores } from "../tema";
import LogoConAro from "./LogoConAro";

/**
 * Encuadre de las pantallas sin sesion (ingreso y aviso de cambio de
 * contrasena pendiente): logo, titulo y subtitulo arriba, y el contenido de
 * cada pantalla debajo. No lleva la temporada porque, sin sesion, todavia no
 * se sabe cual es la vigente.
 *
 * Las medidas de la tarjeta salen del prototipo: 420 px de ancho maximo,
 * esquinas de 18 px y 28 px de relleno.
 */
export default function EncuadreSinSesion({ children }: { children: ReactNode }) {
  return (
    <Box sx={{ px: 2, py: 5 }}>
      <Paper
        elevation={0}
        sx={{
          maxWidth: 420,
          mx: "auto",
          p: "28px",
          borderRadius: "18px",
          border: `1px solid ${colores.borde}`,
          boxShadow: 2,
        }}
      >
        <Stack alignItems="center" spacing={1} sx={{ mb: 3 }}>
          <LogoConAro />
          {/* Centrado tambien el texto: a ancho de telefono el titulo se parte
              en dos renglones y el Stack solo centra la caja. */}
          <Typography
            component="h1"
            variant="h4"
            textAlign="center"
            sx={{ fontWeight: 800, color: colores.marca }}
          >
            Escuela de Verano
          </Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Centro Médico · Administración de la temporada
          </Typography>
        </Stack>
        {children}
      </Paper>
    </Box>
  );
}
