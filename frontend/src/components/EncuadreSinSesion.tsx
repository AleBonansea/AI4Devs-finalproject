import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

import { colores } from "../tema";

/**
 * Encuadre de las pantallas sin sesion (ingreso y aviso de cambio de
 * contrasena pendiente): logo, titulo y subtitulo arriba, y el contenido de
 * cada pantalla debajo. No lleva la temporada porque, sin sesion, todavia no
 * se sabe cual es la vigente.
 */
export default function EncuadreSinSesion({ children }: { children: ReactNode }) {
  return (
    <Container maxWidth="xs" sx={{ py: 5 }}>
      <Paper variant="outlined" sx={{ p: 4 }}>
        <Stack alignItems="center" spacing={1} sx={{ mb: 3 }}>
          <Box
            component="img"
            src="/logo.png"
            alt="Logo de la Escuela de Verano"
            sx={{ width: 96, height: 96 }}
          />
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
    </Container>
  );
}
