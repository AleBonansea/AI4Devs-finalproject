/**
 * La pantalla «Cuenta corriente» (`/cuenta-corriente`), solo para el Admin: se
 * elige la familia y se ven sus cargos con lo pagado y el saldo.
 *
 * No calcula nada: muestra los montos que devuelve la API. Solo vale la
 * respuesta del ultimo pedido, porque dos respuestas pueden llegar en otro
 * orden: al cambiar la familia, la respuesta vieja se descarta.
 */
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import BuscadorFamilia from "../components/BuscadorFamilia";
import FormularioPago from "../components/FormularioPago";
import RenglonDeCargo from "../components/RenglonDeCargo";
import {
  ErrorDeApi,
  cuentaCorriente,
  type CargoEnCuenta,
  type CuentaCorriente as Cuenta,
  type FamiliaEncontrada,
  type PagoRegistrado,
} from "../lib/api";
import { formatearMonto } from "../lib/montos";
import { colores } from "../tema";

export default function CuentaCorriente() {
  const [familia, setFamilia] = useState<FamiliaEncontrada | null>(null);
  const [cuenta, setCuenta] = useState<Cuenta | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargoAPagar, setCargoAPagar] = useState<CargoEnCuenta | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  // Cada pago registrado sube el contador y la cuenta se vuelve a pedir.
  const [version, setVersion] = useState(0);

  const familiaId = familia?.id ?? null;
  useEffect(() => {
    setError(null);
    if (familiaId === null) {
      setCuenta(null);
      return;
    }
    let vigente = true;
    cuentaCorriente(familiaId)
      .then((leida) => {
        if (vigente) setCuenta(leida);
      })
      .catch((causa: unknown) => {
        if (!vigente) return;
        setError(
          causa instanceof ErrorDeApi ? causa.message : "No se pudo cargar la cuenta corriente.",
        );
      });
    return () => {
      vigente = false;
    };
  }, [familiaId, version]);

  function elegirFamilia(elegida: FamiliaEncontrada | null) {
    // Otra familia: ni el aviso ni el formulario abierto son de esta cuenta.
    setCuenta(null);
    setAviso(null);
    setCargoAPagar(null);
    setFamilia(elegida);
  }

  function alRegistrar(pago: PagoRegistrado) {
    setCargoAPagar(null);
    setAviso(
      `Pago registrado por ${formatearMonto(pago.monto)}. ` +
        `Saldo pendiente de la familia: ${formatearMonto(pago.saldo_pendiente)}.`,
    );
    setVersion((v) => v + 1);
  }

  const cargando = familia !== null && cuenta === null && error === null;

  return (
    <Container maxWidth="md" sx={{ py: { xs: 3, sm: 6 } }}>
      <Paper variant="outlined" sx={{ p: { xs: 2, sm: 4 } }}>
        <Stack spacing={4}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
            <Typography variant="h4" component="h1">
              Cuenta corriente
            </Typography>
            <Button component={Link} to="/" variant="text">
              Volver al inicio
            </Button>
          </Stack>

          <Stack spacing={2}>
            <BuscadorFamilia familia={familia} onElegir={elegirFamilia} etiqueta="Familia" />

            {cargando ? (
              <Stack alignItems="center" role="status" aria-label="Cargando la cuenta corriente">
                <CircularProgress />
              </Stack>
            ) : null}
            {error ? <Alert severity="error">{error}</Alert> : null}
            {aviso ? <Alert severity="success">{aviso}</Alert> : null}

            {cuenta ? (
              <Stack spacing={2}>
                <Stack direction="row" spacing={1} alignItems="baseline">
                  <Typography variant="h6" component="p">
                    Saldo pendiente
                  </Typography>
                  <Typography variant="h6" component="p" sx={{ color: colores.dinero }}>
                    {formatearMonto(cuenta.saldo_pendiente)}
                  </Typography>
                </Stack>
                {cuenta.cargos.length === 0 ? (
                  <Alert severity="info">La familia no tiene cargos en la temporada.</Alert>
                ) : (
                  cuenta.cargos.map((cargo) => (
                    <RenglonDeCargo key={cargo.id} cargo={cargo} alPagar={setCargoAPagar} />
                  ))
                )}
              </Stack>
            ) : null}
          </Stack>
        </Stack>
      </Paper>
      {cargoAPagar ? (
        <FormularioPago
          cargo={cargoAPagar}
          abierto
          alCerrar={() => setCargoAPagar(null)}
          alRegistrar={alRegistrar}
        />
      ) : null}
    </Container>
  );
}
