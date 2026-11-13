/**
 * La familia de un alta: nueva, con su `Categoría`, o existente, elegida con
 * un buscador por apellido. De una familia existente se muestra la categoria
 * como texto: cambiarla es cosa del Admin y no se hace desde un alta.
 *
 * El buscador consulta la API desde 2 caracteres y espera 300 ms sin teclas
 * antes de pedir, para no lanzar un pedido por letra.
 */
import Autocomplete from "@mui/material/Autocomplete";
import CircularProgress from "@mui/material/CircularProgress";
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormLabel from "@mui/material/FormLabel";
import ListItemText from "@mui/material/ListItemText";
import Radio from "@mui/material/Radio";
import RadioGroup from "@mui/material/RadioGroup";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { memo, useEffect, useId, useState } from "react";

import {
  ErrorDeApi,
  buscarFamilias,
  type CategoriaFamilia,
  type FamiliaEncontrada,
} from "../lib/api";
import { NOMBRE_DE_LA_CATEGORIA } from "../lib/nombres";

const MINIMO_PARA_BUSCAR = 2;
const ESPERA_ENTRE_TECLAS_MS = 300;
const MENSAJE_INESPERADO = "No se pudo buscar familias.";

const CATEGORIAS = Object.keys(NOMBRE_DE_LA_CATEGORIA) as CategoriaFamilia[];

export interface EleccionFamilia {
  modo: "nueva" | "existente";
  /** La categoria de la familia nueva, o vacio si no se eligio. */
  categoria: CategoriaFamilia | "";
  /** La familia existente elegida, o null. */
  familia: FamiliaEncontrada | null;
}

export const FAMILIA_SIN_ELEGIR: EleccionFamilia = { modo: "nueva", categoria: "", familia: null };

interface Props {
  valor: EleccionFamilia;
  onCambiar: (valor: EleccionFamilia) => void;
  errorCategoria?: string;
  errorFamilia?: string;
}

function SelectorFamilia({ valor, onCambiar, errorCategoria, errorFamilia }: Props) {
  const idModo = useId();
  return (
    <Stack spacing={2}>
      <FormControl>
        <FormLabel id={idModo}>Familia</FormLabel>
        <RadioGroup
          row
          aria-labelledby={idModo}
          value={valor.modo}
          onChange={(evento) =>
            onCambiar({ ...valor, modo: evento.target.value as EleccionFamilia["modo"] })
          }
        >
          <FormControlLabel value="nueva" control={<Radio />} label="Familia nueva" />
          <FormControlLabel value="existente" control={<Radio />} label="Familia existente" />
        </RadioGroup>
      </FormControl>

      {valor.modo === "nueva" ? (
        <TextField
          select
          required
          label="Categoría"
          value={valor.categoria}
          onChange={(evento) =>
            onCambiar({ ...valor, categoria: evento.target.value as CategoriaFamilia })
          }
          error={Boolean(errorCategoria)}
          helperText={errorCategoria}
          // La lista nativa: en el telefono abre el selector del sistema.
          slotProps={{ select: { native: true }, inputLabel: { shrink: true } }}
        >
          <option value="" disabled>
            Elegí una categoría
          </option>
          {CATEGORIAS.map((categoria) => (
            <option key={categoria} value={categoria}>
              {NOMBRE_DE_LA_CATEGORIA[categoria]}
            </option>
          ))}
        </TextField>
      ) : (
        <BuscadorFamilia
          familia={valor.familia}
          onElegir={(familia) => onCambiar({ ...valor, familia })}
          error={errorFamilia}
        />
      )}
    </Stack>
  );
}

// Memorizada: la pantalla se vuelve a dibujar con cada tecla de otro campo y
// esta pieza solo cambia cuando cambian sus props.
export default memo(SelectorFamilia);

interface PropsBuscador {
  familia: FamiliaEncontrada | null;
  onElegir: (familia: FamiliaEncontrada | null) => void;
  error?: string;
}

function BuscadorFamilia({ familia, onElegir, error }: PropsBuscador) {
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
            label="Buscar familia por apellido"
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
