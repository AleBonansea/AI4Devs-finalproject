import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";

import { useSesion } from "../lib/sesion";

/** El inicio: solo el saludo. Los accesos estan en el menu y «Salir» en el encabezado. */
export default function Inicio() {
  const { usuario } = useSesion();

  // RutaProtegida no deja llegar aca sin usuario; esto solo calma al tipo.
  if (!usuario) return null;

  return (
    <Container maxWidth="md" sx={{ py: { xs: 2, sm: 4 } }}>
      <Typography variant="h4" component="h1">
        {`Hola, ${usuario.nombre}`}
      </Typography>
    </Container>
  );
}
