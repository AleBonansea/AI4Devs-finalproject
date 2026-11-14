/**
 * La familia de un alta: nueva, con su `Categoría`, o existente, elegida con
 * un buscador por apellido. De una familia existente se muestra la categoria
 * como texto: cambiarla es cosa del Admin y no se hace desde un alta.
 *
 * La busqueda por apellido es `BuscadorFamilia`.
 */
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormLabel from "@mui/material/FormLabel";
import Radio from "@mui/material/Radio";
import RadioGroup from "@mui/material/RadioGroup";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { memo, useId } from "react";

import type { CategoriaFamilia, FamiliaEncontrada } from "../lib/api";
import { NOMBRE_DE_LA_CATEGORIA } from "../lib/nombres";
import BuscadorFamilia from "./BuscadorFamilia";

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
