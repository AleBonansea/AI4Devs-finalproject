/**
 * La lista de asistencia: un renglon por alumno con `Nombre Apellido` y un
 * grupo exclusivo `Presente` / `Ausente`. Sin elegir, ninguno esta marcado.
 * Botones de al menos 44 px de alto, para el dedo; el grupo ocupa todo el
 * ancho en pantallas chicas.
 */
import Stack from "@mui/material/Stack";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";

import type { AlumnoEnAsistencia } from "../lib/api";
import { colores } from "../tema";

interface Props {
  alumnos: AlumnoEnAsistencia[];
  /** `inscripcion_id` -> presente, o null si no se eligio. */
  marcas: Record<number, boolean | null>;
  onMarcar: (inscripcionId: number, presente: boolean | null) => void;
}

const BOTON = { minHeight: 44, flex: { xs: 1, sm: "none" }, px: 3 } as const;

export default function ListaAsistencia({ alumnos, marcas, onMarcar }: Props) {
  return (
    <Stack spacing={2} component="ul" sx={{ listStyle: "none", m: 0, p: 0 }}>
      {alumnos.map((alumno) => {
        const nombre = `${alumno.nombre} ${alumno.apellido}`;
        const marca = marcas[alumno.inscripcion_id] ?? null;
        return (
          <Stack
            key={alumno.inscripcion_id}
            component="li"
            direction={{ xs: "column", sm: "row" }}
            spacing={1}
            justifyContent="space-between"
            alignItems={{ xs: "stretch", sm: "center" }}
          >
            <Typography>{nombre}</Typography>
            <ToggleButtonGroup
              exclusive
              aria-label={nombre}
              value={marca}
              onChange={(_evento, nuevo: boolean | null) => onMarcar(alumno.inscripcion_id, nuevo)}
              sx={{ width: { xs: "100%", sm: "auto" } }}
            >
              <ToggleButton
                value={true}
                sx={{
                  ...BOTON,
                  "&.Mui-selected, &.Mui-selected:hover": {
                    backgroundColor: colores.presente,
                    color: colores.superficie,
                  },
                }}
              >
                Presente
              </ToggleButton>
              <ToggleButton
                value={false}
                sx={{
                  ...BOTON,
                  "&.Mui-selected, &.Mui-selected:hover": {
                    backgroundColor: colores.ausente,
                    color: colores.superficie,
                  },
                }}
              >
                Ausente
              </ToggleButton>
            </ToggleButtonGroup>
          </Stack>
        );
      })}
    </Stack>
  );
}
