import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import { Outlet, useNavigate } from "react-router-dom";

import { NOMBRE_DEL_ROL } from "../lib/nombres";
import { useSesion } from "../lib/sesion";
import LogoConAro from "./LogoConAro";
import MenuLateral from "./MenuLateral";

/**
 * El marco de toda pantalla con sesion: encabezado con el usuario y «Salir»,
 * el menu y, al lado, la pantalla. RutaProtegida lo deja pasar solo con la
 * sesion comprobada y sin cambio de contrasena pendiente.
 */
export default function MarcoZonaProtegida() {
  const { usuario, salir } = useSesion();
  const navegar = useNavigate();

  // RutaProtegida no deja llegar aca sin usuario; esto solo calma al tipo.
  if (!usuario) return null;

  function alSalir() {
    salir();
    navegar("/ingresar", { replace: true });
  }

  return (
    // Columna de al menos el alto de la ventana: el cuerpo ocupa lo que deja
    // el encabezado, asi la columna del menu llega siempre hasta abajo, aunque
    // la pantalla tenga poco contenido o pocas opciones.
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppBar position="static" color="inherit" elevation={0} sx={{ bgcolor: "background.paper" }}>
        <Toolbar sx={{ gap: 2, borderBottom: 1, borderColor: "divider", minWidth: 0 }}>
          <Box sx={{ flexShrink: 0, display: "flex" }}>
            <LogoConAro tamano="chico" />
          </Box>
          <Typography
            variant="h6"
            component="p"
            noWrap
            sx={{ flexGrow: 1, minWidth: 0, display: { xs: "none", sm: "block" } }}
          >
            Escuela de Verano
          </Typography>
          {/* En el telefono el titulo se oculta y el usuario ocupa el espacio libre. */}
          <Stack alignItems="flex-end" sx={{ minWidth: 0, flexGrow: { xs: 1, sm: 0 } }}>
            <Typography variant="body2" noWrap sx={{ fontWeight: 700, maxWidth: "100%" }}>
              {`${usuario.nombre} ${usuario.apellido}`}
            </Typography>
            <Typography variant="caption" noWrap color="text.secondary" sx={{ maxWidth: "100%" }}>
              {NOMBRE_DEL_ROL[usuario.rol]}
            </Typography>
          </Stack>
          <Button variant="outlined" onClick={alSalir} sx={{ flexShrink: 0 }}>
            Salir
          </Button>
        </Toolbar>
      </AppBar>
      <Box sx={{ display: "flex", flexDirection: { xs: "column", md: "row" }, flexGrow: 1 }}>
        <Box
          sx={{
            flexShrink: 0,
            width: { md: 240 },
            bgcolor: "background.paper",
            borderBottom: { xs: 1, md: 0 },
            borderRight: { md: 1 },
            borderColor: "divider",
            minWidth: 0,
          }}
        >
          <MenuLateral rol={usuario.rol} />
        </Box>
        <Box component="main" sx={{ flexGrow: 1, minWidth: 0 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
