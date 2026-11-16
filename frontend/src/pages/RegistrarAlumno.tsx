/**
 * La pantalla «Registrar alumno» (`/alumnos/nuevo`): los datos minimos del
 * alumno, su grupo, su familia (nueva o existente) y las personas
 * autorizadas a retirar, en un solo envio.
 *
 * Manda QUE se registra; ningun monto. Antes de enviar marca en su campo cada
 * dato minimo vacio. Los errores de la API vuelven con la clave del campo
 * (`nombre`, `personas.0.dni`) y se muestran ahi; lo que no tiene campo va a
 * un aviso general. En un error no se borra nada de lo cargado.
 */
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useCallback, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import ListaPersonas, { type PersonaEnLista } from "../components/ListaPersonas";
import SelectorFamilia, {
  FAMILIA_SIN_ELEGIR,
  type EleccionFamilia,
} from "../components/SelectorFamilia";
import SelectorGrupo from "../components/SelectorGrupo";
import {
  ErrorDeApi,
  registrarAlumno,
  type AltaAlumnoEntrada,
  type AlumnoRegistrado,
} from "../lib/api";
import { NOMBRE_DEL_TURNO } from "../lib/nombres";

const OBLIGATORIO = "Este dato es obligatorio.";
const SIN_TUTOR = "La familia nueva necesita al menos un tutor.";
const MENSAJE_INESPERADO = "No se pudo completar la operación.";

/** Las claves de la API que tienen un campo propio fuera de la lista de personas. */
const CAMPOS_DEL_ALTA = new Set([
  "nombre",
  "apellido",
  "fecha_nacimiento",
  "grupo_id",
  "categoria",
  "familia_id",
  "personas",
]);

interface Alumno {
  nombre: string;
  apellido: string;
  fechaNacimiento: string;
  grupoId: number | null;
}

const ALUMNO_VACIO: Alumno = { nombre: "", apellido: "", fechaNacimiento: "", grupoId: null };

function validar(
  alumno: Alumno,
  familia: EleccionFamilia,
  personas: PersonaEnLista[],
): Record<string, string> {
  const errores: Record<string, string> = {};
  if (!alumno.nombre.trim()) errores.nombre = OBLIGATORIO;
  if (!alumno.apellido.trim()) errores.apellido = OBLIGATORIO;
  if (!alumno.fechaNacimiento) errores.fecha_nacimiento = OBLIGATORIO;
  if (alumno.grupoId === null) errores.grupo_id = OBLIGATORIO;

  if (familia.modo === "nueva") {
    if (!familia.categoria) errores.categoria = OBLIGATORIO;
    if (!personas.some((persona) => persona.esTutor)) errores.personas = SIN_TUTOR;
  } else if (!familia.familia) {
    errores.familia_id = OBLIGATORIO;
  }

  personas.forEach((persona, indice) => {
    if (persona.tipo !== "nueva") return;
    for (const campo of ["nombre", "apellido", "telefono"] as const) {
      if (!persona[campo].trim()) errores[`personas.${indice}.${campo}`] = OBLIGATORIO;
    }
  });
  return errores;
}

function armarEntrada(
  alumno: Alumno,
  familia: EleccionFamilia,
  personas: PersonaEnLista[],
): AltaAlumnoEntrada {
  const entrada: AltaAlumnoEntrada = {
    nombre: alumno.nombre.trim(),
    apellido: alumno.apellido.trim(),
    fecha_nacimiento: alumno.fechaNacimiento,
    grupo_id: alumno.grupoId as number,
    // En el orden en que se ven: el indice de un error de la API es la fila.
    personas: personas.map((persona) => {
      if (persona.tipo === "reutilizada") {
        return { persona_id: persona.personaId, es_tutor: persona.esTutor };
      }
      const dni = persona.dni.trim();
      return {
        nombre: persona.nombre.trim(),
        apellido: persona.apellido.trim(),
        telefono: persona.telefono.trim(),
        ...(dni ? { dni } : {}),
        es_tutor: persona.esTutor,
      };
    }),
  };
  // Una familia o la otra, nunca las dos claves.
  if (familia.modo === "existente" && familia.familia) {
    entrada.familia_id = familia.familia.id;
  } else if (familia.modo === "nueva" && familia.categoria) {
    entrada.categoria = familia.categoria;
  }
  return entrada;
}

function mensajeDeExito(registrado: AlumnoRegistrado): string {
  const { inscripcion, familia } = registrado;
  return (
    `${registrado.nombre} ${registrado.apellido} quedó inscripto en ` +
    `${inscripcion.grupo_nombre} (${NOMBRE_DEL_TURNO[inscripcion.turno]}). ` +
    `Familia: ${familia.etiqueta}.`
  );
}

/** Si la clave del error tiene donde mostrarse en este formulario. */
function tieneCampo(clave: string, personas: PersonaEnLista[]): boolean {
  if (CAMPOS_DEL_ALTA.has(clave)) return true;
  const fila = /^personas\.(\d+)(\.|$)/.exec(clave);
  return fila !== null && Number(fila[1]) < personas.length;
}

export default function RegistrarAlumno() {
  const [alumno, setAlumno] = useState<Alumno>(ALUMNO_VACIO);
  const [familia, setFamilia] = useState<EleccionFamilia>(FAMILIA_SIN_ELEGIR);
  const [personas, setPersonas] = useState<PersonaEnLista[]>([]);
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [exito, setExito] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  // Los callbacks son estables para que las piezas memorizadas no se vuelvan
  // a dibujar con cada tecla de otro campo.
  const cambiarAlumno = useCallback((cambios: Partial<Alumno>) => {
    setAlumno((anterior) => ({ ...anterior, ...cambios }));
  }, []);

  const elegirGrupo = useCallback(
    (grupoId: number | null) => cambiarAlumno({ grupoId }),
    [cambiarAlumno],
  );

  const cantidadDePersonas = personas.length;
  const cambiarPersonas = useCallback(
    (nuevas: PersonaEnLista[]) => {
      // Al agregar o quitar una fila los indices se corren: los errores por
      // fila que habia ya no apuntan a la persona correcta.
      if (nuevas.length !== cantidadDePersonas) {
        setErrores((anteriores) =>
          Object.fromEntries(
            Object.entries(anteriores).filter(
              ([clave]) => clave === "personas" || !clave.startsWith("personas"),
            ),
          ),
        );
      }
      setPersonas(nuevas);
    },
    [cantidadDePersonas],
  );

  async function alEnviar(evento: FormEvent) {
    evento.preventDefault();
    if (enviando) return;
    setExito(null);
    setErrorGeneral(null);

    const locales = validar(alumno, familia, personas);
    setErrores(locales);
    if (Object.keys(locales).length > 0) return;

    setEnviando(true);
    try {
      const registrado = await registrarAlumno(armarEntrada(alumno, familia, personas));
      setAlumno(ALUMNO_VACIO);
      setFamilia(FAMILIA_SIN_ELEGIR);
      setPersonas([]);
      setExito(mensajeDeExito(registrado));
    } catch (causa) {
      if (!(causa instanceof ErrorDeApi)) {
        setErrorGeneral(MENSAJE_INESPERADO);
        return;
      }
      const conCampo: Record<string, string> = {};
      const sinCampo: string[] = [];
      for (const [clave, mensaje] of Object.entries(causa.porCampo)) {
        if (tieneCampo(clave, personas)) conCampo[clave] = mensaje;
        else sinCampo.push(mensaje);
      }
      setErrores(conCampo);
      if (Object.keys(causa.porCampo).length === 0) setErrorGeneral(causa.message);
      else if (sinCampo.length > 0) setErrorGeneral(sinCampo.join(" "));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Container maxWidth="md" sx={{ py: { xs: 3, sm: 6 } }}>
      <Paper variant="outlined" sx={{ p: { xs: 2, sm: 4 } }}>
        <Stack component="form" noValidate onSubmit={alEnviar} spacing={4}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
            <Typography variant="h4" component="h1">
              Registrar alumno
            </Typography>
            <Button component={Link} to="/" variant="text">
              Volver al inicio
            </Button>
          </Stack>

          <Stack spacing={2}>
            <Typography variant="h6" component="h2">
              Alumno
            </Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField
                label="Nombre"
                required
                value={alumno.nombre}
                onChange={(evento) => cambiarAlumno({ nombre: evento.target.value })}
                error={Boolean(errores.nombre)}
                helperText={errores.nombre}
              />
              <TextField
                label="Apellido"
                required
                value={alumno.apellido}
                onChange={(evento) => cambiarAlumno({ apellido: evento.target.value })}
                error={Boolean(errores.apellido)}
                helperText={errores.apellido}
              />
            </Stack>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField
                label="Fecha de nacimiento"
                type="date"
                required
                value={alumno.fechaNacimiento}
                onChange={(evento) => cambiarAlumno({ fechaNacimiento: evento.target.value })}
                error={Boolean(errores.fecha_nacimiento)}
                helperText={errores.fecha_nacimiento}
                // El campo de fecha siempre muestra su mascara: la etiqueta va arriba.
                slotProps={{ inputLabel: { shrink: true } }}
              />
              <SelectorGrupo
                fechaNacimiento={alumno.fechaNacimiento}
                valor={alumno.grupoId}
                onCambiar={elegirGrupo}
                error={errores.grupo_id}
              />
            </Stack>
          </Stack>

          <SelectorFamilia
            valor={familia}
            onCambiar={setFamilia}
            errorCategoria={errores.categoria}
            errorFamilia={errores.familia_id}
          />

          <ListaPersonas personas={personas} onCambiar={cambiarPersonas} errores={errores} />

          <Stack spacing={2} alignItems="flex-start">
            {errorGeneral ? (
              <Alert severity="error" sx={{ alignSelf: "stretch" }}>
                {errorGeneral}
              </Alert>
            ) : null}
            {exito ? (
              <Alert severity="success" sx={{ alignSelf: "stretch" }}>
                {exito}
              </Alert>
            ) : null}
            <Button type="submit" disabled={enviando}>
              Registrar
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Container>
  );
}
