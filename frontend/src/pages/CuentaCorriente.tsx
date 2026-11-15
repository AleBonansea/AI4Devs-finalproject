import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";

/**
 * Cuenta corriente de una familia. Por ahora solo el titulo: la tarea 5.3
 * agrega la busqueda de familia, los cargos, los pagos y el saldo.
 */
export default function CuentaCorriente() {
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1">
        Cuenta corriente
      </Typography>
    </Container>
  );
}
