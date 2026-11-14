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
 * lo mismo si manana el rojo cambia de tono; `rojoOscuro` no.
 *
 * Los valores salen del CSS del prototipo que valido el cliente. Entre
 * parentesis, la variable original.
 */
const deuda = "#B42318";
const textoTenue = "#58717F";
const marca = "#16823A";

export const colores = {
  // Botones, item activo del menu, enlaces. Es el `primary` de MUI. (--shark)
  accion: "#1C77B5",
  accionSuave: "#DCEEF8",
  // El dinero: saldo a cobrar y la accion de cobrar. (--buoy)
  dinero: "#D9541B",
  dineroSuave: "#FCE7DC",
  // La marca es SOLO el logotipo y el titulo de la marca. No se mapea a la
  // paleta de MUI para que ningun boton la tome por defecto. (--leaf)
  marca,
  marcaSuave: "#DDF1E3",

  texto: "#14303F", // (--ink)
  textoTenue, // (--muted)
  borde: "#D5E4EC", // (--line)
  fondo: "#EEF5F9", // (--bg)
  superficie: "#FFFFFF",
  // Superficie secundaria: la barra lateral, los bloques dentro de una tarjeta.
  superficie2: "#F6FAFC",

  // Estados del negocio. Se nombran por lo que significan en el dominio.
  pendiente: "#9A6200",
  pendienteSuave: "#FBEFD6",
  deuda,
  deudaSuave: "#FBE3E0",
  // Mismo valor que `marca`, otro nombre: si el estado cambia de tono, el
  // logotipo no se mueve.
  saldado: marca,
  anulado: textoTenue,

  // Fallos de la API y de validacion. Comparte el rojo con `deuda`, pero es
  // otro nombre: un error de formulario no es una deuda.
  error: deuda,
} as const;

const tituloDeMarca = ['"Baloo 2"', "system-ui", "sans-serif"].join(",");

export const tema = createTheme({
  palette: {
    primary: { main: colores.accion },
    secondary: { main: colores.dinero },
    error: { main: colores.error },
    success: { main: colores.saldado },
    warning: { main: colores.pendiente },
    background: { default: colores.fondo, paper: colores.superficie },
    text: { primary: colores.texto, secondary: colores.textoTenue },
    divider: colores.borde,
  },
  // Las fuentes se cargan desde Google Fonts en frontend/index.html.
  typography: {
    fontFamily: ['"Nunito Sans"', "system-ui", "sans-serif"].join(","),
    h1: { fontFamily: tituloDeMarca },
    h2: { fontFamily: tituloDeMarca },
    h3: { fontFamily: tituloDeMarca },
    h4: { fontFamily: tituloDeMarca },
    h5: { fontFamily: tituloDeMarca },
    h6: { fontFamily: tituloDeMarca },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiButton: {
      defaultProps: { variant: "contained", disableElevation: true },
      // Como en el prototipo: «Ingresar» en negrita, no «INGRESAR».
      styleOverrides: { root: { textTransform: "none", fontWeight: 700 } },
    },
    MuiTextField: { defaultProps: { size: "small", fullWidth: true } },
  },
});
