/**
 * El buscador de una familia existente por apellido. Lo usan el alta de
 * alumnos (dentro de `SelectorFamilia`) y «Registrar cargo».
 *
 * Consulta la API desde 2 caracteres y espera 300 ms sin teclas antes de
 * pedir, para no lanzar un pedido por letra. Las opciones se escriben como
 * `Pérez – Ana`. Con una familia elegida muestra su categoria como texto.
 */
import Autocomplete from "@mui/material/Autocomplete";
import CircularProgress from "@mui/material/CircularProgress";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";

import { ErrorDeApi, buscarFamilias, type FamiliaEncontrada } from "../lib/api";
import { NOMBRE_DE_LA_CATEGORIA } from "../lib/nombres";

const MINIMO_PARA_BUSCAR = 2;
const ESPERA_ENTRE_TECLAS_MS = 300;
const MENSAJE_INESPERADO = "No se pudo buscar familias.";

interface Props {
  familia: FamiliaEncontrada | null;
  onElegir: (familia: FamiliaEncontrada | null) => void;
  error?: string;
  /** La etiqueta del campo. Por defecto, la del alta de alumnos. */
  etiqueta?: string;
}

export default function BuscadorFamilia({
  familia,
  onElegir,
  error,
  etiqueta = "Buscar familia por apellido",
}: Props) {
  // Lo que se ve en el cuadro y lo que se busca son cosas distintas: al
  // elegir una familia el cuadro muestra su etiqueta, y eso no es una busqueda.
  const [texto, setTexto] = useState(familia?.etiqueta ?? "");
  const [busqueda, setBusqueda] = useState("");
  const [opciones, setOpciones] = useState<FamiliaEncontrada[]>([]);
  const [buscando, setBuscando] = useState(false);
  const [errorBusqueda, setErrorBusqueda] = useState<string | null>(null);

  useEffect(() => {
    const apellido = busqueda.trim();
    if (apellido.length < MINIMO_PARA_BUSCAR) {
      setOpciones([]);
      setBuscando(false);
      return;
    }
    let vigente = true;
    setBuscando(true);
    const espera = setTimeout(() => {
      buscarFamilias(apellido)
        .then((encontradas) => {
          if (!vigente) return;
          setOpciones(encontradas);
          setErrorBusqueda(null);
        })
        .catch((causa: unknown) => {
          if (!vigente) return;
          setOpciones([]);
          setErrorBusqueda(causa instanceof ErrorDeApi ? causa.message : MENSAJE_INESPERADO);
        })
        .finally(() => {
          if (vigente) setBuscando(false);
        });
    }, ESPERA_ENTRE_TECLAS_MS);
    return () => {
      vigente = false;
      clearTimeout(espera);
    };
  }, [busqueda]);

  const ayuda = error ?? errorBusqueda ?? undefined;

  return (
    <Stack spacing={1}>
      <Autocomplete
        value={familia}
        options={opciones}
        // La API ya filtra por apellido; filtrar otra vez aca esconderia resultados.
        filterOptions={(lista) => lista}
        getOptionLabel={(opcion) => opcion.etiqueta}
        isOptionEqualToValue={(opcion, elegida) => opcion.id === elegida.id}
        inputValue={texto}
        onInputChange={(_, nuevo, motivo) => {
          setTexto(nuevo);
          if (motivo === "input" || motivo === "clear") {
            setBusqueda(nuevo);
            // Escribir de nuevo es buscar otra familia: la elegida se suelta.
            if (familia) onElegir(null);
          }
        }}
        onChange={(_, elegida) => onElegir(elegida)}
        loading={buscando}
        loadingText="Buscando…"
        noOptionsText={
          busqueda.trim().length < MINIMO_PARA_BUSCAR
            ? "Escribí al menos 2 letras del apellido."
            : "No hay familias con ese apellido."
        }
        renderOption={(props, opcion) => {
          const { key, ...resto } = props;
          return (
            <li key={key} {...resto}>
              <ListItemText
                primary={opcion.etiqueta}
                secondary={NOMBRE_DE_LA_CATEGORIA[opcion.categoria]}
              />
            </li>
          );
        }}
        renderInput={(parametros) => (
          <TextField
            {...parametros}
            required
            label={etiqueta}
            error={Boolean(ayuda)}
            helperText={ayuda}
            slotProps={{
              input: {
                ...parametros.InputProps,
                endAdornment: (
                  <>
                    {buscando ? <CircularProgress color="inherit" size={20} /> : null}
                    {parametros.InputProps.endAdornment}
                  </>
                ),
              },
            }}
          />
        )}
      />
      {familia ? (
        <Typography>{`Categoría: ${NOMBRE_DE_LA_CATEGORIA[familia.categoria]}`}</Typography>
      ) : null}
    </Stack>
  );
}
