/**
 * Un cargo de la cuenta corriente: que es, de quien, total, pagado, saldo y
 * sus pagos. No calcula nada: escribe lo que devolvio la API. Un cargo con
 * saldo `"0.00"` (texto) se muestra como saldado y no ofrece cobrar.
 */
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { CargoEnCuenta } from "../lib/api";
import { formatearFecha } from "../lib/fechas";
import { formatearMonto } from "../lib/montos";
import { NOMBRE_DEL_TURNO } from "../lib/nombres";
import { colores } from "../tema";

interface Props {
  cargo: CargoEnCuenta;
  /** Lo que pasa al tocar «Registrar pago»; la pantalla de pagos lo conecta. */
  alPagar?: (cargo: CargoEnCuenta) => void;
}

function descripcion(cargo: CargoEnCuenta): string {
  if (cargo.periodo) return `${cargo.tipo_cargo} · ${cargo.periodo.nombre}`;
  if (cargo.modalidad === "dia" && cargo.fecha_dia) {
    return `${cargo.tipo_cargo} · Día ${formatearFecha(cargo.fecha_dia)}`;
  }
  return cargo.tipo_cargo;
}

function aQuien(cargo: CargoEnCuenta): string {
  const alumno = `${cargo.nombre} ${cargo.apellido}`;
  return cargo.turno ? `${alumno} · ${NOMBRE_DEL_TURNO[cargo.turno]}` : alumno;
}

/** Una etiqueta seguida de su monto. */
function Monto(props: { etiqueta: string; valor: string; destacado?: boolean }) {
  const { etiqueta, valor, destacado } = props;
  return (
    <Stack direction="row" spacing={1} alignItems="baseline">
      <Typography variant="body2" color="text.secondary">
        {etiqueta}
      </Typography>
      <Typography
        fontWeight={destacado ? 700 : undefined}
        sx={destacado ? { color: colores.dinero } : undefined}
      >
        {formatearMonto(valor)}
      </Typography>
    </Stack>
  );
}

export default function RenglonDeCargo({ cargo, alPagar }: Props) {
  const saldado = cargo.saldo === "0.00";
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack spacing={1.5}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
          <Stack>
            <Typography fontWeight={700}>{descripcion(cargo)}</Typography>
            <Typography variant="body2" color="text.secondary">
              {aQuien(cargo)}
            </Typography>
          </Stack>
          {saldado ? (
            <Chip label="Saldado" size="small" variant="outlined" sx={{ color: colores.saldado }} />
          ) : null}
        </Stack>

        <Stack direction="row" flexWrap="wrap" columnGap={3} rowGap={0.5}>
          <Monto etiqueta="Total" valor={cargo.monto_total} />
          <Monto etiqueta="Pagado" valor={cargo.pagado} />
          <Monto etiqueta="Saldo" valor={cargo.saldo} destacado={!saldado} />
        </Stack>

        {cargo.pagos.length > 0 ? (
          <Stack>
            <Typography variant="body2" color="text.secondary">
              Pagos
            </Typography>
            <List dense disablePadding>
              {cargo.pagos.map((pago) => (
                <ListItem key={pago.id} disableGutters sx={{ py: 0 }}>
                  <Typography variant="body2">
                    {`${formatearFecha(pago.fecha_pago)} · ${formatearMonto(pago.monto)}`}
                  </Typography>
                </ListItem>
              ))}
            </List>
          </Stack>
        ) : null}

        {saldado ? null : (
          <Stack alignItems="flex-start">
            <Button size="small" onClick={() => alPagar?.(cargo)}>
              Registrar pago
            </Button>
          </Stack>
        )}
      </Stack>
    </Paper>
  );
}
