/**
 * Las personas autorizadas a retirar de un alta: nuevas, con sus datos, o ya
 * cargadas, reutilizadas por DNI. Cada una lleva su casilla `Tutor` y se
 * puede quitar.
 *
 * La lista se manda a la API en el orden en que se ve, asi que el indice de
 * un error como `personas.0.dni` es la fila. Los errores llegan con esas
 * mismas claves.
 */
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormHelperText from "@mui/material/FormHelperText";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { memo, useRef, useState, type KeyboardEvent } from "react";

import { ErrorDeApi, buscarPersonaPorDni } from "../lib/api";

const MENSAJE_INESPERADO = "No se pudo buscar la persona.";

export type CampoPersonaNueva = "nombre" | "apellido" | "telefono" | "dni";

export type PersonaEnLista =
  | {
      clave: number;
      tipo: "nueva";
      nombre: string;
      apellido: string;
      telefono: string;
      dni: string;
      esTutor: boolean;
    }
  | {
      clave: number;
      tipo: "reutilizada";
      personaId: number;
      nombre: string;
      apellido: string;
      esTutor: boolean;
    };

interface Props {
  personas: PersonaEnLista[];
  onCambiar: (personas: PersonaEnLista[]) => void;
  /** Errores con las claves de la API: `personas` y `personas.<fila>.<campo>`. */
  errores: Record<string, string>;
}

const CAMPOS_NUEVA: { campo: CampoPersonaNueva; etiqueta: string; obligatorio: boolean }[] = [
  { campo: "nombre", etiqueta: "Nombre", obligatorio: true },
  { campo: "apellido", etiqueta: "Apellido", obligatorio: true },
  { campo: "telefono", etiqueta: "Teléfono", obligatorio: true },
  { campo: "dni", etiqueta: "DNI", obligatorio: false },
];

/** Los errores de una fila que no tienen un campo propio donde mostrarse. */
function erroresDeLaFila(
  errores: Record<string, string>,
  indice: number,
  persona: PersonaEnLista,
): string[] {
  const prefijo = `personas.${indice}`;
  return Object.entries(errores)
    .filter(([clave]) => clave === prefijo || clave.startsWith(`${prefijo}.`))
    .filter(([clave]) => {
      if (persona.tipo !== "nueva") return true;
      return !CAMPOS_NUEVA.some(({ campo }) => clave === `${prefijo}.${campo}`);
    })
    .map(([, mensaje]) => mensaje);
}

function ListaPersonas({ personas, onCambiar, errores }: Props) {
  const siguienteClave = useRef(1);
  const [dni, setDni] = useState("");
  const [buscando, setBuscando] = useState(false);
  const [errorBusqueda, setErrorBusqueda] = useState<string | null>(null);

  function nuevaClave(): number {
    const clave = siguienteClave.current;
    siguienteClave.current += 1;
    return clave;
  }

  function agregarNueva() {
    onCambiar([
      ...personas,
      {
        clave: nuevaClave(),
        tipo: "nueva",
        nombre: "",
        apellido: "",
        telefono: "",
        dni: "",
        esTutor: false,
      },
    ]);
  }

  async function buscar() {
    const buscado = dni.trim();
    if (!buscado) {
      setErrorBusqueda("Escribí un DNI para buscar.");
      return;
    }
    setBuscando(true);
    setErrorBusqueda(null);
    try {
      const encontrada = await buscarPersonaPorDni(buscado);
      if (personas.some((p) => p.tipo === "reutilizada" && p.personaId === encontrada.id)) {
        setErrorBusqueda("Esa persona ya está en la lista.");
        return;
      }
      onCambiar([
        ...personas,
        {
          clave: nuevaClave(),
          tipo: "reutilizada",
          personaId: encontrada.id,
          nombre: encontrada.nombre,
          apellido: encontrada.apellido,
          esTutor: false,
        },
      ]);
      setDni("");
    } catch (causa) {
      setErrorBusqueda(causa instanceof ErrorDeApi ? causa.message : MENSAJE_INESPERADO);
    } finally {
      setBuscando(false);
    }
  }

  function alTeclearDni(evento: KeyboardEvent) {
    // Enter en el DNI busca; no envia el alta entera.
    if (evento.key === "Enter") {
      evento.preventDefault();
      void buscar();
    }
  }

  function cambiar(indice: number, cambios: Partial<PersonaEnLista>) {
    onCambiar(
      personas.map((persona, i) =>
        i === indice ? ({ ...persona, ...cambios } as PersonaEnLista) : persona,
      ),
    );
  }

  function quitar(indice: number) {
    onCambiar(personas.filter((_, i) => i !== indice));
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h6" component="h2">
        Personas autorizadas a retirar
      </Typography>

      {errores.personas ? <Alert severity="error">{errores.personas}</Alert> : null}

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems="flex-start">
        <TextField
          label="DNI a buscar"
          value={dni}
          onChange={(evento) => setDni(evento.target.value)}
          onKeyDown={alTeclearDni}
          error={Boolean(errorBusqueda)}
          helperText={errorBusqueda ?? "Para reutilizar una persona ya cargada."}
          slotProps={{ htmlInput: { inputMode: "numeric" } }}
        />
        <Button
          variant="outlined"
          onClick={() => void buscar()}
          disabled={buscando}
          sx={{ flexShrink: 0 }}
        >
          Buscar por DNI
        </Button>
      </Stack>

      {personas.length === 0 ? (
        <Typography color="text.secondary">Todavía no agregaste ninguna persona.</Typography>
      ) : null}

      {personas.map((persona, indice) => {
        const nombreCompleto = `${persona.nombre} ${persona.apellido}`.trim();
        const erroresFila = erroresDeLaFila(errores, indice, persona);
        return (
          <Paper key={persona.clave} variant="outlined" sx={{ p: 2 }}>
            <Stack spacing={2}>
              {persona.tipo === "nueva" ? (
                <Stack
                  direction={{ xs: "column", sm: "row" }}
                  spacing={2}
                  useFlexGap
                  flexWrap="wrap"
                >
                  {CAMPOS_NUEVA.map(({ campo, etiqueta, obligatorio }) => {
                    const error = errores[`personas.${indice}.${campo}`];
                    return (
                      <TextField
                        key={campo}
                        label={etiqueta}
                        required={obligatorio}
                        value={persona[campo]}
                        onChange={(evento) => cambiar(indice, { [campo]: evento.target.value })}
                        error={Boolean(error)}
                        helperText={error}
                        sx={{ flex: "1 1 12rem" }}
                        slotProps={{
                          htmlInput:
                            campo === "telefono" || campo === "dni"
                              ? { inputMode: campo === "telefono" ? "tel" : "numeric" }
                              : undefined,
                        }}
                      />
                    );
                  })}
                </Stack>
              ) : (
                <Stack spacing={0.5}>
                  <Typography>{nombreCompleto}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Ya cargada, encontrada por DNI.
                  </Typography>
                </Stack>
              )}

              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <FormControlLabel
                  label="Tutor"
                  control={
                    <Checkbox
                      checked={persona.esTutor}
                      onChange={(evento) => cambiar(indice, { esTutor: evento.target.checked })}
                    />
                  }
                />
                <Button
                  variant="text"
                  onClick={() => quitar(indice)}
                  aria-label={`Quitar a ${nombreCompleto || "esta persona"}`}
                >
                  Quitar
                </Button>
              </Stack>

              {erroresFila.map((mensaje) => (
                <FormHelperText key={mensaje} error>
                  {mensaje}
                </FormHelperText>
              ))}
            </Stack>
          </Paper>
        );
      })}

      <Stack direction="row">
        <Button variant="outlined" onClick={agregarNueva}>
          Agregar persona nueva
        </Button>
      </Stack>
    </Stack>
  );
}

// Memorizada: la pantalla se vuelve a dibujar con cada tecla de otro campo y
// esta pieza solo cambia cuando cambian sus props.
export default memo(ListaPersonas);
