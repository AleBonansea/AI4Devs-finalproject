import Alert from "@mui/material/Alert";
import AlertTitle from "@mui/material/AlertTitle";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import { useNavigate } from "react-router-dom";

import { useSesion } from "../lib/sesion";

/**
 * Lo unico que ve un usuario con el cambio de contrasena pendiente.
 * El cambio en si es de HU-UT-06 (lote 2); mientras tanto solo puede salir.
 */
export default function CambioPendiente() {
  const { salir } = useSesion();
  const navegar = useNavigate();

  function alSalir() {
    salir();
    navegar("/ingresar", { replace: true });
  }

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Paper variant="outlined" sx={{ p: 4 }}>
        <Stack spacing={2} alignItems="flex-start">
          <Alert severity="warning">
            <AlertTitle>Tenés que cambiar tu contraseña antes de continuar.</AlertTitle>
            El cambio de contraseña todavía no está disponible. Pedile ayuda a un Admin.
          </Alert>
          <Button onClick={alSalir}>Salir</Button>
        </Stack>
      </Paper>
    </Container>
  );
}
