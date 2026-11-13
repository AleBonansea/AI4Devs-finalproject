/**
 * El campo `Grupo` de un alta: los grupos donde el usuario puede inscribir,
 * escritos como nombre y turno, con la marca `(sugerido)` segun la fecha de
 * nacimiento.
 *
 * Pide los grupos a la API cada vez que cambia la fecha. Distingue el grupo
 * elegido a mano del elegido por la sugerencia: mientras el usuario no haya
 * elegido a mano, la sugerencia manda (con exactamente un sugerido lo elige;
 * con dos o ninguno deja el grupo sin elegir). Una eleccion a mano no la pisa
 * ninguna sugerencia. Lo van a reusar la ficha y la reinscripcion (HU-AF-11).
 */
import TextField from "@mui/material/TextField";
import { memo, useEffect, useRef, useState } from "react";

import { ErrorDeApi, listarGrupos, type GrupoParaInscribir } from "../lib/api";
import { NOMBRE_DEL_TURNO } from "../lib/nombres";

const MENSAJE_INESPERADO = "No se pudieron cargar los grupos.";

interface Props {
  /** `AAAA-MM-DD`, o vacio si todavia no se cargo. */
  fechaNacimiento: string;
  /** El id del grupo elegido, o null. */
  valor: number | null;
  /** Recibe null cuando la sugerencia deja el grupo sin elegir. */
  onCambiar: (grupoId: number | null) => void;
  /** El error de validacion del campo, si hay. */
  error?: string;
}

function textoDelGrupo(grupo: GrupoParaInscribir): string {
  const base = `${grupo.nombre} · ${NOMBRE_DEL_TURNO[grupo.turno]}`;
  return grupo.sugerido ? `${base} (sugerido)` : base;
}

function SelectorGrupo({ fechaNacimiento, valor, onCambiar, error }: Props) {
  const [grupos, setGrupos] = useState<GrupoParaInscribir[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  // La respuesta llega despues del render que la pidio: la sugerencia mira la
  // eleccion de ese momento, no la de cuando salio el pedido.
  const valorActual = useRef(valor);
  const cambiar = useRef(onCambiar);
  useEffect(() => {
    valorActual.current = valor;
    cambiar.current = onCambiar;
  });

  // El ultimo grupo que eligio la sugerencia, o null si no eligio ninguno o
  // si despues el usuario eligio a mano. Si el valor actual coincide con este,
  // la eleccion es de la sugerencia y una fecha nueva la puede reemplazar.
  const elegidoPorSugerencia = useRef<number | null>(null);

  useEffect(() => {
    // Solo vale la respuesta del ultimo pedido: con la fecha escrita a mano
    // salen varios seguidos y pueden volver en otro orden.
    let vigente = true;
    setCargando(true);
    setErrorCarga(null);
    listarGrupos(fechaNacimiento || undefined)
      .then((leidos) => {
        if (!vigente) return;
        setGrupos(leidos);
        setCargando(false);
        // Sin eleccion, o con la de una sugerencia anterior, manda la nueva.
        // Si el valor actual lo eligio el usuario a mano, no se toca.
        const actual = valorActual.current;
        const mandaLaSugerencia = actual === null || actual === elegidoPorSugerencia.current;
        if (!mandaLaSugerencia) return;
        const [unico, ...otros] = leidos.filter((grupo) => grupo.sugerido);
        const nuevo = unico && otros.length === 0 ? unico.id : null;
        elegidoPorSugerencia.current = nuevo;
        if (nuevo !== actual) cambiar.current(nuevo);
      })
      .catch((causa: unknown) => {
        if (!vigente) return;
        setCargando(false);
        setErrorCarga(causa instanceof ErrorDeApi ? causa.message : MENSAJE_INESPERADO);
      });
    return () => {
      vigente = false;
    };
  }, [fechaNacimiento]);

  let ayuda: string | undefined;
  if (error) ayuda = error;
  else if (errorCarga) ayuda = errorCarga;
  else if (cargando && grupos.length === 0) ayuda = "Cargando grupos…";
  else if (!cargando && grupos.length === 0) ayuda = "No hay grupos donde puedas inscribir.";
  else if (grupos.some((grupo) => grupo.sugerido)) ayuda = "Sugerido por la fecha de nacimiento.";

  // Mientras llega la primera lista el valor elegido no tiene opcion: se
  // muestra vacio en lugar de un valor fuera de rango.
  const valorVisible = valor !== null && grupos.some((grupo) => grupo.id === valor) ? valor : "";

  return (
    <TextField
      select
      required
      label="Grupo"
      value={valorVisible}
      onChange={(evento) => {
        if (evento.target.value === "") return;
        // Eleccion a mano: desde ahora ninguna sugerencia la reemplaza.
        elegidoPorSugerencia.current = null;
        onCambiar(Number(evento.target.value));
      }}
      error={Boolean(error || errorCarga)}
      helperText={ayuda}
      // La lista nativa: en el telefono abre el selector del sistema.
      slotProps={{ select: { native: true }, inputLabel: { shrink: true } }}
    >
      <option value="" disabled>
        Elegí un grupo
      </option>
      {grupos.map((grupo) => (
        <option key={grupo.id} value={grupo.id}>
          {textoDelGrupo(grupo)}
        </option>
      ))}
    </TextField>
  );
}

// Memorizada: la pantalla se vuelve a dibujar con cada tecla de otro campo y
// esta pieza solo cambia cuando cambian sus props.
export default memo(SelectorGrupo);
