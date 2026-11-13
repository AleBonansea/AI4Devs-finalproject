import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

/**
 * Pantalla de ingreso. Por ahora solo la composicion del formulario: el
 * envio, la validacion y los errores llegan en la tarea 2.2.
 */
export default function Ingreso() {
  return (
    <Container maxWidth="xs" sx={{ py: 8 }}>
      <Paper variant="outlined" sx={{ p: 4 }}>
        <Stack spacing={2}>
          <Typography variant="h5" component="h1">
            Escuelita de Verano
          </Typography>
          <TextField id="ingreso-usuario" label="Usuario" autoComplete="username" />
          <TextField
            id="ingreso-contrasena"
            label="Contraseña"
            type="password"
            autoComplete="current-password"
          />
          <Button>Ingresar</Button>
        </Stack>
      </Paper>
    </Container>
  );
}
