import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";

import type { RolUsuario } from "../lib/api";
import { useSesion } from "../lib/sesion";

/** El rol escrito para personas. Vive aca porque es el unico lugar que lo muestra. */
const NOMBRE_DEL_ROL: Record<RolUsuario, string> = {
  admin: "Admin",
  coordinador: "Coordinador",
  profesor: "Profesor",
};

export default function Inicio() {
  const { usuario, salir } = useSesion();
  const navegar = useNavigate();

  // RutaProtegida no deja llegar aca sin usuario; esto solo calma al tipo.
  if (!usuario) return null;

  function alSalir() {
    salir();
    navegar("/ingresar", { replace: true });
  }

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Paper variant="outlined" sx={{ p: 4 }}>
        <Stack spacing={2} alignItems="flex-start">
          <Typography variant="h4" component="h1">
            Escuelita de Verano
          </Typography>
          <Typography variant="h6" component="p">
            {`${usuario.nombre} ${usuario.apellido}`}
          </Typography>
          <Typography color="text.secondary">{NOMBRE_DEL_ROL[usuario.rol]}</Typography>
          <Button onClick={alSalir}>Salir</Button>
        </Stack>
      </Paper>
    </Container>
  );
}
