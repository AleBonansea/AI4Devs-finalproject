import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";

/** Pantalla de registro de un cargo. Por ahora solo el titulo (tarea 5.3). */
export default function RegistrarCargo() {
  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Typography variant="h4" component="h1">
        Registrar cargo
      </Typography>
    </Container>
  );
}
