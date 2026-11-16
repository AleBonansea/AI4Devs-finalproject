/**
 * El desglose de un cargo simulado: tarifa base, descuento y total.
 *
 * No calcula nada. Escribe lo que devolvio la API: el descuento se muestra
 * como porcentaje y no como un monto restado, porque restar seria calcular
 * en el cliente. Con `modalidad` null el cargo es de monto fijo.
 */
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { CargoSimulado, Modalidad, Turno } from "../lib/api";
import { formatearMonto, formatearPorcentaje } from "../lib/montos";
import { NOMBRE_DE_LA_CATEGORIA, NOMBRE_DE_LA_MODALIDAD, NOMBRE_DEL_TURNO } from "../lib/nombres";
import { colores } from "../tema";

interface Props {
  desglose: CargoSimulado;
  turno: Turno;
  /** null en un cargo de monto fijo. */
  modalidad: Modalidad | null;
}

/** Un renglon: el texto a la izquierda y su monto o porcentaje a la derecha. */
function Renglon({
  texto,
  valor,
  destacado,
}: {
  texto: string;
  valor?: string;
  destacado?: boolean;
}) {
  return (
    <Stack direction="row" justifyContent="space-between" alignItems="baseline" spacing={2}>
      <Typography fontWeight={destacado ? 700 : undefined}>{texto}</Typography>
      {valor === undefined ? null : (
        <Typography
          fontWeight={destacado ? 700 : undefined}
          sx={destacado ? { color: colores.dinero } : undefined}
        >
          {valor}
        </Typography>
      )}
    </Stack>
  );
}

function textoDelDescuento(desglose: CargoSimulado, modalidad: Modalidad): string {
  const categoria = NOMBRE_DE_LA_CATEGORIA[desglose.categoria_aplicada];
  const hijos = desglose.cantidad_hijos_aplicada;
  // Solo el Mes descuenta por cantidad de hijos en el turno.
  if (modalidad === "mes" && hijos !== null) {
    return `Descuento ${categoria} · ${hijos} ${hijos === 1 ? "hijo" : "hijos"} en el turno`;
  }
  return `Descuento ${categoria} · ${NOMBRE_DE_LA_MODALIDAD[modalidad]}`;
}

export default function DesgloseCargo({ desglose, turno, modalidad }: Props) {
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack spacing={1} divider={<Divider flexItem />}>
        {modalidad === null ? (
          <>
            <Renglon texto="Monto fijo" valor={formatearMonto(desglose.monto_base)} />
            <Renglon texto="Sin descuento" />
          </>
        ) : (
          <>
            <Renglon
              texto={`Tarifa base · ${NOMBRE_DEL_TURNO[turno]} · ${NOMBRE_DE_LA_MODALIDAD[modalidad]}`}
              valor={formatearMonto(desglose.monto_base)}
            />
            <Renglon
              texto={textoDelDescuento(desglose, modalidad)}
              valor={formatearPorcentaje(desglose.porcentaje_aplicado)}
            />
          </>
        )}
        <Renglon texto="Total del cargo" valor={formatearMonto(desglose.monto_total)} destacado />
      </Stack>
    </Paper>
  );
}
