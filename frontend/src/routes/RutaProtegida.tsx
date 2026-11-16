/**
 * La puerta de toda la zona protegida.
 *
 * Todas las pantallas con sesion pasan por aca, asi que ninguna puede
 * asomar sin token comprobado ni con el cambio de contrasena pendiente.
 */
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Stack from "@mui/material/Stack";
import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";

import { ErrorDeApi, usuarioActual } from "../lib/api";
import { useSesion } from "../lib/sesion";
import CambioPendiente from "../pages/CambioPendiente";

const MENSAJE_INESPERADO = "No se pudo completar la operación.";

export default function RutaProtegida() {
  const { hayToken, usuario, fijarUsuario, salir } = useSesion();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hayToken || usuario || error !== null) return;

    // StrictMode monta el efecto dos veces en desarrollo: la primera
    // respuesta se descarta y la segunda es la que fija el estado, asi la
    // pantalla nunca queda esperando una promesa huerfana.
    let vigente = true;
    usuarioActual()
      .then((leido) => {
        if (vigente) fijarUsuario(leido);
      })
      .catch((causa: unknown) => {
        if (!vigente) return;
        if (causa instanceof ErrorDeApi && causa.estado === 401) {
          // api.ts ya borro el token; se limpia el resto y se va al ingreso.
          salir();
          return;
        }
        // Un corte de red no cierra la sesion: el token se conserva.
        setError(causa instanceof ErrorDeApi ? causa.message : MENSAJE_INESPERADO);
      });
    return () => {
      vigente = false;
    };
  }, [hayToken, usuario, error, fijarUsuario, salir]);

  if (!hayToken) return <Navigate to="/ingresar" replace />;

  if (error !== null) {
    return (
      <Container maxWidth="sm" sx={{ py: 8 }}>
        <Alert
          severity="error"
          action={
            <Button color="inherit" variant="text" size="small" onClick={() => setError(null)}>
              Reintentar
            </Button>
          }
        >
          {error}
        </Alert>
      </Container>
    );
  }

  if (!usuario) {
    return (
      <Container maxWidth="sm" sx={{ py: 8 }}>
        <Stack alignItems="center">
          <CircularProgress aria-label="Comprobando la sesión" />
        </Stack>
      </Container>
    );
  }

  if (usuario.debe_cambiar_password) return <CambioPendiente />;

  return <Outlet />;
}
