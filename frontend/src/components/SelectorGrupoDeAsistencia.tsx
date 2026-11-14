/**
 * El campo `Grupo` de la pantalla de asistencia: los grupos del usuario,
 * escritos como nombre y turno (`Delfines · Mañana`). Si hay exactamente uno,
 * lo elige solo; con varios, deja el campo sin elegir.
 *
 * No reusa `SelectorGrupo`: aquel sugiere por fecha de nacimiento y no pisa
 * la eleccion a mano, reglas que aca no existen.
 */
import TextField from "@mui/material/TextField";
import { useEffect, useRef, useState } from "react";

import { ErrorDeApi, listarGrupos, type GrupoParaInscribir } from "../lib/api";
import { NOMBRE_DEL_TURNO } from "../lib/nombres";

const MENSAJE_INESPERADO = "No se pudieron cargar los grupos.";

interface Props {
  /** El id del grupo elegido, o null. */
  valor: number | null;
  onCambiar: (grupoId: number | null) => void;
}

export default function SelectorGrupoDeAsistencia({ valor, onCambiar }: Props) {
  const [grupos, setGrupos] = useState<GrupoParaInscribir[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  // El efecto corre una sola vez; usa siempre el ultimo `onCambiar`.
  const cambiar = useRef(onCambiar);
  useEffect(() => {
    cambiar.current = onCambiar;
  });

  useEffect(() => {
    let vigente = true;
    listarGrupos()
      .then((leidos) => {
        if (!vigente) return;
        setGrupos(leidos);
        setCargando(false);
        const [unico, ...otros] = leidos;
        if (unico && otros.length === 0) cambiar.current(unico.id);
      })
      .catch((causa: unknown) => {
        if (!vigente) return;
        setCargando(false);
        setErrorCarga(causa instanceof ErrorDeApi ? causa.message : MENSAJE_INESPERADO);
      });
    return () => {
      vigente = false;
    };
  }, []);

  let ayuda: string | undefined;
  if (errorCarga) ayuda = errorCarga;
  else if (cargando) ayuda = "Cargando grupos…";
  else if (grupos.length === 0) ayuda = "No tenés grupos asignados.";

  const valorVisible = valor !== null && grupos.some((grupo) => grupo.id === valor) ? valor : "";

  return (
    <TextField
      select
      label="Grupo"
      value={valorVisible}
      onChange={(evento) => {
        if (evento.target.value === "") return;
        onCambiar(Number(evento.target.value));
      }}
      error={Boolean(errorCarga)}
      helperText={ayuda}
      // La lista nativa: en el telefono abre el selector del sistema.
      slotProps={{ select: { native: true }, inputLabel: { shrink: true } }}
    >
      <option value="" disabled>
        Elegí un grupo
      </option>
      {grupos.map((grupo) => (
        <option key={grupo.id} value={grupo.id}>
          {`${grupo.nombre} · ${NOMBRE_DEL_TURNO[grupo.turno]}`}
        </option>
      ))}
    </TextField>
  );
}
