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
 * lo mismo si manana el naranja cambia de tono; `naranjaOscuro` no.
 *
 * Los valores salen del prototipo que valido el cliente (docs/previews/).
 * Las decisiones estan en openspec/changes/paleta-y-encuadre/design.md.
 */
const accion = "#1870b0";
const dinero = "#d85018";
const textoTenue = "#58717f";

export const colores = {
  // Botones, item activo del menu, enlaces. Es el `primary` de MUI.
  accion,
  // El dinero: saldo a cobrar y la accion de cobrar. Va en negrita o grande:
  // contra blanco da 4,13:1, que no alcanza para texto corrido.
  dinero,
  // La marca es SOLO el logotipo y el titulo de las pantallas sin sesion.
  // No se mapea a la paleta de MUI para que ningun boton la tome por defecto.
  marca: "#108038",

  fondo: "#eef5f9",
  superficie: "#ffffff",
  borde: "#d5e4ec",

  texto: "#14303f",
  textoTenue,

  // Estados del negocio. Se nombran por lo que significan en el dominio.
  // La deuda es dinero que falta cobrar, no una falla: va en el naranja del
  // dinero, como en el prototipo.
  deuda: dinero,
  // Mismo valor que `marca`, pero otro nombre: si el estado cambia de tono,
  // el logotipo no se mueve.
  saldado: "#108038",
  pendiente: "#986000",
  anulado: textoTenue,

  // Fallos de la API y de validacion. No es `deuda`: si lo fuera, un error
  // de formulario saldria del color del dinero.
  error: "#b3261e",
} as const;

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
  typography: {
    fontFamily: ['"Inter"', "system-ui", "sans-serif"].join(","),
  },
  shape: { borderRadius: 8 },
  components: {
    MuiButton: { defaultProps: { variant: "contained", disableElevation: true } },
    MuiTextField: { defaultProps: { size: "small", fullWidth: true } },
  },
});
