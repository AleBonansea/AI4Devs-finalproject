import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Link, useNavigate } from "react-router-dom";

import { NOMBRE_DEL_ROL } from "../lib/nombres";
import { useSesion } from "../lib/sesion";

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
            Escuela de Verano
          </Typography>
          <Typography variant="h6" component="p">
            {`${usuario.nombre} ${usuario.apellido}`}
          </Typography>
          <Typography color="text.secondary">{NOMBRE_DEL_ROL[usuario.rol]}</Typography>
          <Stack direction="row" spacing={2} useFlexGap sx={{ flexWrap: "wrap" }}>
            <Button component={Link} to="/alumnos/nuevo">
              Registrar alumno
            </Button>
            <Button component={Link} to="/asistencia">
              Tomar asistencia
            </Button>
            {/* Cobrar es solo del Admin: al resto ni se le ofrece. */}
            {usuario.rol === "admin" && (
              <Button component={Link} to="/cargos/nuevo">
                Registrar cargo
              </Button>
            )}
            <Button variant="outlined" onClick={alSalir}>
              Salir
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Container>
  );
}
