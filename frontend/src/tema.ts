import { createTheme } from "@mui/material/styles";

/**
 * El catalogo de color del sistema.
 *
 * Este es el unico archivo del frontend donde un valor de color puede
 * aparecer escrito. En el resto se usan los nombres, via `theme.palette` o
 * `sx`. Un hook corta los valores a pelo fuera de aca.
 *
 * El motivo no es purismo: un agente sin catalogo inventa un gris nuevo cada
 * vez, y a los dos meses hay catorce grises y ninguno es el del sistema.
 *
 * Cada nombre dice PARA QUE sirve, no como se ve. `deuda` sigue significando
 * lo mismo si manana el rojo cambia de tono; `rojoClaro` no.
 */
export const colores = {
  marca: "#1b5e20",
  marcaClara: "#4c8c4a",
  acento: "#f9a825",

  fondo: "#f6f7f5",
  superficie: "#ffffff",
  borde: "#dfe3dc",

  texto: "#1f2420",
  textoTenue: "#5b625c",

  // Estados del negocio. Se nombran por lo que significan en el dominio.
  deuda: "#b3261e",
  saldado: "#1b5e20",
  pendiente: "#9a6700",
  anulado: "#5b625c",
} as const;

export const tema = createTheme({
  palette: {
    primary: { main: colores.marca, light: colores.marcaClara },
    secondary: { main: colores.acento },
    error: { main: colores.deuda },
    success: { main: colores.saldado },
    warning: { main: colores.pendiente },
    background: { default: colores.fondo, paper: colores.superficie },
    text: { primary: colores.texto, secondary: colores.textoTenue },
    divider: colores.borde,
  },
  typography: {
    fontFamily: ['"Inter"', "system-ui", "sans-serif"].join(","),
  },
  shape: { borderRadius: 8 },
  components: {
    MuiButton: { defaultProps: { variant: "contained", disableElevation: true } },
    MuiTextField: { defaultProps: { size: "small", fullWidth: true } },
  },
});
