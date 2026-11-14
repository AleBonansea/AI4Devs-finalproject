/**
 * La pantalla «Tomar asistencia» (`/asistencia`): se elige grupo y fecha, se
 * ve la lista de inscriptos con lo ya tomado, se marca `Presente` / `Ausente`
 * y se guarda. Se puede volver a una fecha para corregirla.
 *
 * Al cambiar grupo o fecha se vuelve a pedir y se descartan las marcas sin
 * guardar. Solo vale la respuesta del ultimo pedido.
 */
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import ListaAsistencia from "../components/ListaAsistencia";
import SelectorGrupoDeAsistencia from "../components/SelectorGrupoDeAsistencia";
import {
  ErrorDeApi,
  abrirAsistencia,
  guardarAsistencia,
  type AsistenciaDelGrupo,
  type AsistenciaMarcada,
} from "../lib/api";

const MENSAJE_INESPERADO = "No se pudo completar la operación.";

/** Hoy como `AAAA-MM-DD` con la fecha LOCAL del dispositivo (`toISOString` da la de UTC). */
function hoyLocal(): string {
  const ahora = new Date();
  const mes = String(ahora.getMonth() + 1).padStart(2, "0");
  const dia = String(ahora.getDate()).padStart(2, "0");
  return `${ahora.getFullYear()}-${mes}-${dia}`;
}

function marcasDe(asistencia: AsistenciaDelGrupo): Record<number, boolean | null> {
  return Object.fromEntries(
    asistencia.alumnos.map((alumno) => [alumno.inscripcion_id, alumno.presente]),
  );
}

export default function TomarAsistencia() {
  const [grupoId, setGrupoId] = useState<number | null>(null);
  const [fecha, setFecha] = useState<string>(hoyLocal);
  const [asistencia, setAsistencia] = useState<AsistenciaDelGrupo | null>(null);
  const [marcas, setMarcas] = useState<Record<number, boolean | null>>({});
  const [cargando, setCargando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [errorAlAbrir, setErrorAlAbrir] = useState<string | null>(null);
  const [errorAlGuardar, setErrorAlGuardar] = useState<string | null>(null);
  const [exito, setExito] = useState(false);

  useEffect(() => {
    setAsistencia(null);
    setMarcas({});
    setErrorAlAbrir(null);
    setErrorAlGuardar(null);
    setExito(false);
    if (grupoId === null || !fecha) {
      setCargando(false);
      return;
    }
    // Con la fecha escrita a mano salen varios pedidos seguidos y pueden
    // volver en otro orden: solo vale el ultimo.
    let vigente = true;
    setCargando(true);
    abrirAsistencia(grupoId, fecha)
      .then((respuesta) => {
        if (!vigente) return;
        setAsistencia(respuesta);
        setMarcas(marcasDe(respuesta));
        setCargando(false);
      })
      .catch((causa: unknown) => {
        if (!vigente) return;
        setErrorAlAbrir(causa instanceof ErrorDeApi ? causa.message : MENSAJE_INESPERADO);
        setCargando(false);
      });
    return () => {
      vigente = false;
    };
  }, [grupoId, fecha]);

  const marcadas: AsistenciaMarcada[] = Object.entries(marcas).flatMap(([id, presente]) =>
    presente === null ? [] : [{ inscripcion_id: Number(id), presente }],
  );

  async function alGuardar() {
    if (grupoId === null || guardando || marcadas.length === 0) return;
    setGuardando(true);
    setExito(false);
    setErrorAlGuardar(null);
    try {
      const respuesta = await guardarAsistencia(grupoId, fecha, marcadas);
      setAsistencia(respuesta);
      setMarcas(marcasDe(respuesta));
      setExito(true);
    } catch (causa) {
      // Se conservan las marcas: no se pierde lo que se cargo.
      setErrorAlGuardar(causa instanceof ErrorDeApi ? causa.message : MENSAJE_INESPERADO);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <Container maxWidth="md" sx={{ py: { xs: 3, sm: 6 } }}>
      <Paper variant="outlined" sx={{ p: { xs: 2, sm: 4 } }}>
        <Stack spacing={4}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
            <Typography variant="h4" component="h1">
              Tomar asistencia
            </Typography>
            <Button component={Link} to="/" variant="text">
              Volver al inicio
            </Button>
          </Stack>

          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <SelectorGrupoDeAsistencia valor={grupoId} onCambiar={setGrupoId} />
            <TextField
              label="Fecha"
              type="date"
              value={fecha}
              onChange={(evento) => setFecha(evento.target.value)}
              // El campo de fecha siempre muestra su mascara: la etiqueta va arriba.
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Stack>

          {cargando ? (
            <Stack alignItems="center">
              <CircularProgress aria-label="Cargando la asistencia" />
            </Stack>
          ) : null}

          {errorAlAbrir ? <Alert severity="error">{errorAlAbrir}</Alert> : null}

          {asistencia && asistencia.alumnos.length === 0 ? (
            <Typography color="text.secondary">No hay alumnos inscriptos en este grupo.</Typography>
          ) : null}

          {asistencia && asistencia.alumnos.length > 0 ? (
            <Stack spacing={3}>
              <ListaAsistencia
                alumnos={asistencia.alumnos}
                marcas={marcas}
                onMarcar={(inscripcionId, presente) => {
                  setExito(false);
                  setMarcas((anteriores) => ({ ...anteriores, [inscripcionId]: presente }));
                }}
              />
              {errorAlGuardar ? <Alert severity="error">{errorAlGuardar}</Alert> : null}
              {exito ? <Alert severity="success">Asistencia guardada.</Alert> : null}
              <Stack alignItems="flex-start">
                <Button onClick={alGuardar} disabled={marcadas.length === 0 || guardando}>
                  Guardar
                </Button>
              </Stack>
            </Stack>
          ) : null}
        </Stack>
      </Paper>
    </Container>
  );
}
