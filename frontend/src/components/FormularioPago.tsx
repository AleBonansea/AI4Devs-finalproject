/**
 * El formulario para registrar un pago de un cargo, en un diálogo. Propone el
 * saldo del cargo como monto y la fecha de hoy; se puede cambiar cualquiera.
 *
 * No calcula nada: el saldo que muestra es el que devolvió la API, el monto se
 * lee del texto escrito (`leerMonto`) y la API decide si el pago se acepta.
 * Los rechazos por campo de la API se escriben junto a su campo.
 */
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useRef, useState, type FormEvent } from "react";

import { ErrorDeApi, registrarPago, type CargoEnCuenta, type PagoRegistrado } from "../lib/api";
import { descripcionDeCargo } from "../lib/descripcionDeCargo";
import { hoyLocal } from "../lib/fechas";
import { formatearMonto, leerMonto, montoParaEditar } from "../lib/montos";
import { colores } from "../tema";

interface Props {
  cargo: CargoEnCuenta;
  abierto: boolean;
  alCerrar: () => void;
  alRegistrar: (pago: PagoRegistrado) => void;
}

const MENSAJE_INESPERADO = "No se pudo registrar el pago.";

export default function FormularioPago({ cargo, abierto, alCerrar, alRegistrar }: Props) {
  const [monto, setMonto] = useState(() => montoParaEditar(cargo.saldo));
  const [fecha, setFecha] = useState(hoyLocal);
  const [errorDeMonto, setErrorDeMonto] = useState<string | null>(null);
  const [errorDeFecha, setErrorDeFecha] = useState<string | null>(null);
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [registrando, setRegistrando] = useState(false);
  // El estado se actualiza en el render siguiente: la referencia corta un
  // segundo envío que llegue antes.
  const enCurso = useRef(false);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    if (enCurso.current) return;

    setErrorGeneral(null);
    setErrorDeFecha(null);
    if (monto.trim() === "") {
      setErrorDeMonto("Este dato es obligatorio.");
      return;
    }
    const montoLeido = leerMonto(monto);
    if (montoLeido === null) {
      setErrorDeMonto("Escribí el monto como 4.462,50.");
      return;
    }
    setErrorDeMonto(null);

    enCurso.current = true;
    setRegistrando(true);
    try {
      const pago = await registrarPago(cargo.id, { monto: montoLeido, fecha_pago: fecha });
      // La pantalla cierra el diálogo: no queda nada que actualizar acá.
      alRegistrar(pago);
    } catch (causa) {
      enCurso.current = false;
      setRegistrando(false);
      if (!(causa instanceof ErrorDeApi)) {
        setErrorGeneral(MENSAJE_INESPERADO);
        return;
      }
      const { monto: deMonto, fecha_pago: deFecha } = causa.porCampo;
      setErrorDeMonto(deMonto ?? null);
      setErrorDeFecha(deFecha ?? null);
      // Sin mensaje por campo (o con uno de un campo que no está), va entero arriba.
      if (!deMonto && !deFecha) setErrorGeneral(causa.message);
    }
  }

  return (
    <Dialog
      open={abierto}
      onClose={registrando ? undefined : alCerrar}
      fullWidth
      maxWidth="xs"
      aria-labelledby="titulo-registrar-pago"
    >
      <form onSubmit={(evento) => void enviar(evento)} noValidate>
        <DialogTitle id="titulo-registrar-pago">Registrar pago</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <Stack>
              <Typography fontWeight={700}>{descripcionDeCargo(cargo)}</Typography>
              <Stack direction="row" spacing={1} alignItems="baseline">
                <Typography variant="body2" color="text.secondary">
                  Saldo del cargo
                </Typography>
                <Typography fontWeight={700} sx={{ color: colores.dinero }}>
                  {formatearMonto(cargo.saldo)}
                </Typography>
              </Stack>
            </Stack>

            {errorGeneral ? <Alert severity="error">{errorGeneral}</Alert> : null}

            <TextField
              label="Monto"
              value={monto}
              onChange={(evento) => setMonto(evento.target.value)}
              error={Boolean(errorDeMonto)}
              helperText={errorDeMonto}
              slotProps={{ htmlInput: { inputMode: "decimal" } }}
              fullWidth
              autoFocus
            />
            <TextField
              label="Fecha del pago"
              type="date"
              value={fecha}
              onChange={(evento) => setFecha(evento.target.value)}
              error={Boolean(errorDeFecha)}
              helperText={errorDeFecha}
              slotProps={{ inputLabel: { shrink: true } }}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={alCerrar} disabled={registrando}>
            Cancelar
          </Button>
          <Button type="submit" variant="contained" disabled={registrando}>
            Registrar pago
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
